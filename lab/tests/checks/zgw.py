"""Categorie 3, zgw: het ZGW-aansluitprofiel (MijnZaken op ZGW, VNG API Lab) tegen Open Zaak.

Deze module plant twee runs van Redocly Respect (tests/respect/run.mjs), de uitkomst per
workflow komt in tests/rapport.py:
  zgw/gedrag/<workflow>   schema- en content-typecontroles als waarschuwing
  zgw/strikt/<workflow>   standaard van Respect, alle controles tellen

Token: ZGW-JWT van applicatie "burgerportaal" (alleen lezen). ZGW 1.x kent geen token per burger,
dus tokenA en tokenB zijn hetzelfde applicatietoken.
"""
import sys

from kader import ROOT, Context

sys.path.insert(0, str(ROOT / "seed"))
from lib import env, zgw_token  # noqa: E402

CAT = "zgw"
GEDRAG = '{"SCHEMA_CHECK":"warn","CONTENT_TYPE_CHECK":"warn"}'


def uitvoeren(ctx: Context):
    cfg = ctx.manifest.get("zgw")
    if not ctx.component("openzaak"):
        ctx.overslaan(f"{CAT}/profiel", CAT, None, "ZGW-aansluitprofiel", "geen Open Zaak in deze stack")
        return
    if not cfg:
        ctx.overslaan(f"{CAT}/profiel", CAT, "openzaak", "ZGW-aansluitprofiel",
                      "stack.yaml heeft geen sectie zgw (zaken-URL en profiel)")
        return
    profiel = cfg.get("profiel", "aansluitprofielen/mijnzaken/zgw.openzaak.arazzo.yaml")
    if not (ROOT / profiel).exists():
        ctx.overslaan(f"{CAT}/profiel", CAT, "openzaak", "ZGW-aansluitprofiel", f"profiel {profiel} bestaat niet")
        return
    token = zgw_token(env("ZGW_PORTAAL_CLIENT_ID"), env("ZGW_PORTAAL_SECRET"))
    inputs = {"tokenA": token, "tokenB": token, "bsnA": ctx.burger("A"), "bsnB": ctx.burger("B")}
    for modus, severity in (("gedrag", GEDRAG), ("strikt", None)):
        ctx.respect_jobs.append({
            "id": f"zgw-{modus}", "prefix": f"{CAT}/{modus}", "categorie": CAT, "component": "openzaak",
            "naam": f"ZGW-aansluitprofiel ({modus})", "arazzo": profiel,
            "servers": {"zaken": cfg["zaken"]}, "inputs": inputs, "severity": severity,
        })
