"""Kader van de gedeelde testsuite: manifest laden, checks uitvoeren en vastleggen.

Een check heeft een id (categorie/component/...), een status (pass, fail of skip) en bij
fail of skip altijd een reden. Checks zijn functies die een korte detailtekst teruggeven;
ze slaan zichzelf over met `raise Overslaan("reden")` en falen met een exceptie.
"""
from __future__ import annotations

import json
import os
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATEGORIEEN = ["gezondheid", "rook", "zgw", "burger-isolatie", "mijn-apis"]


def plugin_mappen() -> list[Path]:
    """Mappen van de actieve plug-ins (DEMOSTACK_PLUGINS, gezet door scripts/stack.sh)."""
    return [Path(p) for p in os.environ.get("DEMOSTACK_PLUGINS", "").split() if p]


def laad_plugin(map_: Path, stack: str) -> dict:
    """Leest plugin.yaml en past de sectie `per_stack.<stack>` toe (lijsten op id)."""
    m = yaml.safe_load((map_ / "plugin.yaml").read_text()) or {}
    m["map"] = str(map_)
    extra = (m.pop("per_stack", None) or {}).get(stack) or {}
    for sleutel, waarde in extra.items():
        if isinstance(waarde, list) and all(isinstance(x, dict) and "id" in x for x in waarde):
            bestaand = {x["id"]: x for x in m.get(sleutel) or []}
            for x in waarde:
                bestaand[x["id"]] = {**bestaand.get(x["id"], {}), **x}
            m[sleutel] = list(bestaand.values())
        elif isinstance(waarde, dict) and isinstance(m.get(sleutel), dict):
            m[sleutel] = {**m[sleutel], **waarde}
        else:
            m[sleutel] = waarde
    return m


class Overslaan(Exception):
    """Check niet uitvoerbaar in deze stack; de boodschap is de reden."""


def _per_id(*lijsten):
    """Voegt lijsten van dicts met een id samen; een latere lijst overschrijft op id."""
    uit = {}
    for lijst in lijsten:
        for item in lijst or []:
            uit[item["id"]] = item
    return list(uit.values())


def _lees(stack: str) -> dict:
    """Leest stacks/<stack>/stack.yaml en volgt `erft: <andere stack>` (zonder basis)."""
    eigen = yaml.safe_load((ROOT / f"stacks/{stack}/stack.yaml").read_text()) or {}
    ouder_naam = eigen.get("erft")
    if not ouder_naam:
        return eigen
    ouder = _lees(ouder_naam)
    zonder = set(eigen.get("zonder", []))
    m = {**{k: v for k, v in ouder.items() if k not in ("gepland", "erft", "zonder")}, **eigen}
    m["componenten"] = [c for c in _per_id(ouder.get("componenten"), eigen.get("componenten")) if c["id"] not in zonder]
    m["burgerkanalen"] = [k for k in _per_id(ouder.get("burgerkanalen"), eigen.get("burgerkanalen"))
                          if k["id"] not in zonder and k.get("api") not in zonder]
    m["bekende_fouten"] = {**(ouder.get("bekende_fouten") or {}), **(eigen.get("bekende_fouten") or {})}
    m["testburgers"] = {**(ouder.get("testburgers") or {}), **(eigen.get("testburgers") or {})}
    return m


def laad_manifest(stack: str) -> dict:
    """Voegt stacks/basis/stack.yaml en stacks/<stack>/stack.yaml (met `erft`) samen.

    Sleutels: componenten, gepland, burgerkanalen, zgw, bekende_fouten, testburgers,
    erft (stack waarvan dit manifest alles overneemt), zonder (component-id's die weg moeten).

    Daarna komen de actieve plug-ins erbij (docs/PLUGINS.md): hun componenten,
    burgerkanalen, mijn_apis en bekende_fouten. Elk component en kanaal van een plug-in
    krijgt `plugin: <naam>`.
    """
    basis = yaml.safe_load((ROOT / "stacks/basis/stack.yaml").read_text()) or {}
    eigen = _lees(stack)
    m = {**basis, **eigen}
    m["naam"] = stack
    m["componenten"] = _per_id(basis.get("componenten"), eigen.get("componenten"))
    m["testburgers"] = {**basis.get("testburgers", {}), **(eigen.get("testburgers") or {})}
    m["burgerkanalen"] = eigen.get("burgerkanalen") or []
    m["bekende_fouten"] = eigen.get("bekende_fouten") or {}
    m["gepland"] = eigen.get("gepland") or []
    m["mijn_apis"] = []
    m["plugins"] = []
    for map_ in plugin_mappen():
        p = laad_plugin(map_, stack)
        naam = p.get("naam", map_.name)
        m["plugins"].append({k: p.get(k) for k in ("naam", "titel", "leverancier", "versie", "licentie", "bron", "map")})
        for sleutel in ("componenten", "burgerkanalen", "mijn_apis"):
            m[sleutel] = _per_id(m[sleutel], [{**x, "plugin": naam} for x in p.get(sleutel) or []])
        m["bekende_fouten"] = {**m["bekende_fouten"], **(p.get("bekende_fouten") or {})}
    return m


def lees_ps(pad: Path) -> dict[str, dict]:
    """Leest `docker compose ps --format json` (een JSON-array of een object per regel)."""
    if not pad.exists():
        return {}
    tekst = pad.read_text().strip()
    if not tekst:
        return {}
    if tekst.startswith("["):
        rijen = json.loads(tekst)
    else:
        rijen = [json.loads(r) for r in tekst.splitlines() if r.strip()]
    return {r["Service"]: r for r in rijen}


@dataclass
class Context:
    stack: str
    manifest: dict
    ps: dict
    raw: Path
    alleen: set[str] | None = None
    resultaten: list[dict] = field(default_factory=list)
    respect_jobs: list[dict] = field(default_factory=list)
    gedeeld: dict = field(default_factory=dict)  # gedeelde toestand tussen checks

    # -- componenten
    def component(self, cid: str) -> dict | None:
        return next((c for c in self.manifest["componenten"] if c["id"] == cid), None)

    def heeft(self, *cids: str) -> bool:
        return all(self.component(c) for c in cids)

    def ontbrekend(self, *cids: str) -> list[str]:
        return [c for c in cids if not self.component(c)]

    def burger(self, letter: str) -> str:
        return self.manifest["testburgers"][letter]

    def wil(self, categorie: str) -> bool:
        return self.alleen is None or categorie in self.alleen

    # -- vastleggen
    def leg_vast(self, cid, categorie, component, naam, status, detail=None, reden=None, duur=None):
        r = {"id": cid, "categorie": categorie, "component": component, "naam": naam, "status": status}
        if detail:
            r["detail"] = detail
        if reden:
            r["reden"] = reden
        if duur is not None:
            r["duur_s"] = round(duur, 2)
        self.resultaten.append(r)
        teken = {"pass": "OK   ", "fail": "FOUT ", "skip": "SKIP "}[status]
        print(f"{teken} {cid}: {detail or reden or ''}"[:400], flush=True)
        return r

    def overslaan(self, cid, categorie, component, naam, reden):
        return self.leg_vast(cid, categorie, component, naam, "skip", reden=reden)

    def voer_uit(self, cid, categorie, component, naam, fn, *args):
        start = time.time()
        try:
            detail = fn(*args)
        except Overslaan as e:
            return self.leg_vast(cid, categorie, component, naam, "skip", reden=str(e), duur=time.time() - start)
        except Exception as e:  # noqa: BLE001
            reden = f"{type(e).__name__}: {e}" if not isinstance(e, AssertionError) else str(e)
            if isinstance(e, KeyError):
                reden = f"gegevens uit een eerdere controle ontbreken ({e}); zie de check ervoor"
            r = self.leg_vast(cid, categorie, component, naam, "fail", reden=reden[:1500], duur=time.time() - start)
            r["traceback"] = traceback.format_exc()[-2000:]
            return r
        return self.leg_vast(cid, categorie, component, naam, "pass", detail=str(detail or "")[:1500] or None,
                             duur=time.time() - start)


def eis(voorwaarde, melding):
    if not voorwaarde:
        raise AssertionError(melding)
