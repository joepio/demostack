"""Evaluatie per stack voor de welkomstpagina: welke API's, versies, geheugen, images en licenties.

Draait op de host (docker-CLI nodig). Schrijft public/stacks.json en public/stacks.html (fragment dat build.sh invoegt).
Versies van API's worden live uit de OpenAPI-specificaties gelezen; geheugen en image-grootte live uit Docker.
"""
import html, json, os, re, subprocess, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = dict(l.split("=", 1) for l in (HERE.parent / ".env").read_text().splitlines() if "=" in l and not l.startswith("#"))
D = ENV["BASE_DOMAIN"]
ACTIVE = set(filter(None, ENV.get("COMPOSE_PROFILES", "").split(",")))

# Standaard-API's met de plek van hun OpenAPI-specificatie in deze omgeving
APIS = {
    "zaken": ("Zaken API", f"https://zaken.{D}/zaken/api/v1/schema/openapi.yaml"),
    "catalogi": ("Catalogi API", f"https://zaken.{D}/catalogi/api/v1/schema/openapi.yaml"),
    "documenten": ("Documenten API", f"https://zaken.{D}/documenten/api/v1/schema/openapi.yaml"),
    "besluiten": ("Besluiten API", f"https://zaken.{D}/besluiten/api/v1/schema/openapi.yaml"),
    "autorisaties": ("Autorisaties API", f"https://zaken.{D}/autorisaties/api/v1/schema/openapi.yaml"),
    "klantinteracties": ("Klantinteracties API", f"https://klant.{D}/klantinteracties/api/v1/schema/openapi.yaml"),
    "objecten": ("Objecten API", f"https://objecten.{D}/api/v2/schema/openapi.yaml"),
    "objecttypen": ("Objecttypen API", f"https://objecttypen.{D}/api/v2/schema/openapi.yaml"),
    "notificaties": ("Notificaties API", f"https://notificaties.{D}/api/v1/schema/openapi.yaml"),
    "formulieren": ("Open Formulieren API", f"https://formulieren.{D}/api/v2/schema"),
    "brp": ("Haal Centraal BRP Personen", None),
    "kvk": ("KvK Zoeken/Basisprofiel", None),
    "bag": ("BAG Individuele bevragingen", None),
    "oidc": ("OpenID Connect (Keycloak)", None),
    "selectielijst": ("Selectielijst API", None),
    "pabc": ("PABC (autorisatiebeheer)", None),
    "elastic": ("Elasticsearch", None),
    "solr": ("Solr", None),
}

C = lambda **kw: kw  # leesbaarheid
STACKS = [
    {"id": "registers", "naam": "Gedeelde basis: registers en formulieren", "profiel": None,
     "uitleg": "De zaakgerichte registers volgens de ZGW-standaarden, plus formulieren, notificaties en inloggen. Alle werkplekken bouwen hierop.",
     "componenten": [
        C(naam="Open Zaak", maker="Maykin / Dimpact", licentie="EUPL-1.2", diensten=["openzaak", "openzaak-celery", "openzaak-beat"],
          biedt=["zaken", "catalogi", "documenten", "besluiten", "autorisaties"], gebruikt=["notificaties", "selectielijst", "oidc"]),
        C(naam="Open Klant", maker="Maykin", licentie="EUPL-1.2", diensten=["openklant", "openklant-celery"],
          biedt=["klantinteracties"], gebruikt=["oidc"]),
        C(naam="Objecten", maker="Maykin", licentie="EUPL-1.2", diensten=["objects", "objects-celery"],
          biedt=["objecten"], gebruikt=["objecttypen", "notificaties", "oidc"]),
        C(naam="Objecttypen", maker="Maykin", licentie="EUPL-1.2", diensten=["objecttypes"], biedt=["objecttypen"], gebruikt=["oidc"]),
        C(naam="Open Notificaties", maker="Maykin / Dimpact", licentie="EUPL-1.2",
          diensten=["opennotificaties", "opennotificaties-celery", "opennotificaties-beat"], biedt=["notificaties"], gebruikt=["autorisaties", "oidc"]),
        C(naam="Open Formulieren", maker="Maykin / stakeholders", licentie="EUPL-1.2", diensten=["openforms", "openforms-celery", "openforms-beat"],
          biedt=["formulieren"], gebruikt=["zaken", "catalogi", "documenten", "objecten", "objecttypen", "oidc"]),
        C(naam="Keycloak", maker="Red Hat / CNCF", licentie="Apache-2.0", diensten=["keycloak"], biedt=["oidc"], gebruikt=[]),
        C(naam="PostgreSQL + PostGIS", maker="PostgreSQL-community", licentie="PostgreSQL", diensten=["db"], biedt=[], gebruikt=[]),
        C(naam="Redis", maker="Redis Ltd.", licentie="RSALv2 / SSPLv1 / AGPLv3", diensten=["redis"], biedt=[], gebruikt=[]),
        C(naam="nginx, Mailpit", maker="F5 / Axllent", licentie="BSD-2-Clause, MIT", diensten=["nginx", "mailpit"], biedt=[], gebruikt=[]),
     ]},
    {"id": "kcc", "naam": "Klantcontact: KISS", "profiel": "kcc",
     "uitleg": "Werkplek voor het klantcontactcentrum (Dimpact en Den Haag). Zoekt inwoners en bedrijven, toont zaken en contactmomenten, legt contactverzoeken vast.",
     "componenten": [
        C(naam="KISS", maker="VNG Realisatie / Dimpact / ICATT", licentie="EUPL-1.2", diensten=["kiss"], biedt=[],
          gebruikt=["klantinteracties", "zaken", "catalogi", "documenten", "objecten", "brp", "kvk", "elastic", "oidc"]),
        C(naam="Elasticsearch", maker="Elastic", licentie="AGPLv3 / SSPL / Elastic License 2.0", diensten=["elasticsearch"], biedt=["elastic"], gebruikt=[]),
        C(naam="BRP personen-mock", maker="RvIG", licentie="EUPL-1.2", diensten=["personen-mock"], biedt=["brp"], gebruikt=[]),
     ]},
    {"id": "zac", "naam": "Zaakafhandeling Dimpact (PodiumD): ZAC", "profiel": "zac",
     "uitleg": "Zaakafhandelcomponent van Dimpact (INFO.nl). Werkvoorraad, taken via CMMN/BPMN, documenten, mail. Autorisatie per zaaktype via PABC en OPA.",
     "componenten": [
        C(naam="ZAC", maker="INFO.nl / Dimpact", licentie="EUPL-1.2", diensten=["zac"], biedt=[],
          gebruikt=["zaken", "catalogi", "documenten", "besluiten", "objecten", "klantinteracties", "notificaties", "brp", "kvk", "bag",
                    "pabc", "solr", "oidc"]),
        C(naam="PABC", maker="Dimpact", licentie="EUPL-1.2", diensten=["pabc-api"], biedt=["pabc"], gebruikt=["oidc"]),
        C(naam="Solr", maker="Apache", licentie="Apache-2.0", diensten=["solr"], biedt=["solr"], gebruikt=[]),
        C(naam="Open Policy Agent", maker="CNCF", licentie="Apache-2.0", diensten=["opa"], biedt=[], gebruikt=[]),
        C(naam="Gotenberg", maker="Gotenberg", licentie="MIT", diensten=["office-converter"], biedt=[], gebruikt=[]),
     ]},
    {"id": "gzac", "naam": "Zaakafhandeling Ritense: GZAC (Valtimo)", "profiel": "gzac",
     "uitleg": "Generieke zaakafhandelcomponent op Valtimo. Dossiers, taken en processen (BPMN/DMN), ZGW-koppelingen via plugins. Hier met de voorbeeldcasus evenementenvergunning.",
     "componenten": [
        C(naam="GZAC (Valtimo)", maker="Ritense", licentie="EUPL-1.2", diensten=["gzac-backend", "gzac", "gzac-permissions"], biedt=[],
          gebruikt=["oidc"], kan_gebruiken=["zaken", "catalogi", "documenten", "besluiten", "objecten", "objecttypen", "klantinteracties", "notificaties"]),
     ]},
]


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE.parent).stdout


def api_version(url):
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            text = r.read(20000).decode("utf-8", "replace")
        m = re.search(r"^info:.*?^\s+version:\s*['\"]?([^'\"\n]+)", text, re.S | re.M)
        return re.sub(r"\s*\(.*\)$", "", m.group(1).strip()) if m else None
    except Exception:
        return None


def main():
    images = {}
    cfg = json.loads(sh("docker", "compose", "--profile", "kcc", "--profile", "gzac", "--profile", "zac", "config", "--format", "json"))
    for name, svc in cfg["services"].items():
        images[name] = svc.get("image")
    sizes = {}
    for img in set(filter(None, images.values())):
        out = sh("docker", "image", "inspect", "-f", "{{.Size}}", img).strip()
        sizes[img] = int(out) if out.isdigit() else 0
    mem = {}
    for line in sh("docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}").splitlines():
        name, usage = line.split(" ", 1)
        m = re.match(r"([\d.]+)(KiB|MiB|GiB)", usage)
        if m:
            mem[name] = float(m.group(1)) * {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024}[m.group(2)]
    versions = {k: api_version(u) for k, (_, u) in APIS.items()}

    out = []
    for st in STACKS:
        aan = st["profiel"] is None or st["profiel"] in ACTIVE
        tot_mem, tot_img, seen_img, n = 0.0, 0, set(), 0
        comps = []
        for c in st["componenten"]:
            c_mem, c_imgs = 0.0, []
            for svc in c["diensten"]:
                img = images.get(svc)
                if img and img not in c_imgs:
                    c_imgs.append(img)
                c_mem += mem.get(f"kern-{svc}-1", 0.0)
                n += 1
            c_img = sum(sizes.get(i, 0) for i in c_imgs)
            for i in c_imgs:
                if i not in seen_img:
                    seen_img.add(i); tot_img += sizes.get(i, 0)
            tot_mem += c_mem
            versie = (c_imgs[0].split(":")[-1].split("@")[0] if c_imgs else "")
            comps.append({**{k: c[k] for k in ("naam", "maker", "licentie")}, "versie": versie, "images": c_imgs,
                          "geheugen_mb": round(c_mem), "image_mb": round(c_img / 1e6),
                          "biedt": [{"id": a, "naam": APIS[a][0], "versie": versions.get(a)} for a in c["biedt"]],
                          "gebruikt": [{"id": a, "naam": APIS[a][0]} for a in c["gebruikt"]],
                          "kan_gebruiken": [{"id": a, "naam": APIS[a][0]} for a in c.get("kan_gebruiken", [])]})
        out.append({"id": st["id"], "naam": st["naam"], "uitleg": st["uitleg"], "profiel": st["profiel"], "aan": aan,
                    "containers": n, "geheugen_mb": round(tot_mem), "image_mb": round(tot_img / 1e6), "componenten": comps})
    (HERE / "public").mkdir(exist_ok=True)
    (HERE / "public" / "stacks.json").write_text(json.dumps({"domein": D, "stacks": out}, indent=1, ensure_ascii=False))
    (HERE / "public" / "stacks.html").write_text(render(out))


def gb(mb):
    return f"{mb / 1024:.1f} GB" if mb >= 1024 else f"{mb} MB"


def render(stacks):
    e = html.escape
    parts = []
    for st in stacks:
        status = ('<span class="state ok">Draait</span>' if st["aan"] else '<span class="state soon">Staat uit</span>')
        if st["profiel"] is None:
            status = '<span class="state ok">Altijd aan</span>'
        rows = []
        for c in st["componenten"]:
            biedt = ", ".join(f'{e(a["naam"])}{" " + e(a["versie"]) if a["versie"] else ""}' for a in c["biedt"]) or "-"
            gebruikt = ", ".join(e(a["naam"]) for a in c["gebruikt"]) or "-"
            if c["kan_gebruiken"]:
                gebruikt += '<br><small>Kan via plugins: ' + ", ".join(e(a["naam"]) for a in c["kan_gebruiken"]) + "</small>"
            rows.append(f'<tr><td><strong>{e(c["naam"])}</strong><br><small>{e(c["maker"])}</small></td>'
                        f'<td>{e(c["versie"]) or "-"}</td><td>{biedt}</td><td>{gebruikt}</td>'
                        f'<td>{e(c["licentie"])}</td><td class="num">{gb(c["geheugen_mb"]) if st["aan"] else "-"}</td>'
                        f'<td class="num">{gb(c["image_mb"])}</td></tr>')
        parts.append(f'''<section class="stack" id="stack-{st["id"]}">
    <div class="stack-head"><h3>{e(st["naam"])}</h3>{status}</div>
    <p class="sub">{e(st["uitleg"])}</p>
    <div class="facts">
      <div><span>Geheugen nu</span><strong>{gb(st["geheugen_mb"]) if st["aan"] else "uit"}</strong></div>
      <div><span>Images (los geteld)</span><strong>{gb(st["image_mb"])}</strong></div>
      <div><span>Containers</span><strong>{st["containers"]}</strong></div>
      <div><span>Licenties</span><strong>{e(", ".join(sorted({c["licentie"].split(",")[0].split(" /")[0] for c in st["componenten"]})))}</strong></div>
    </div>
    <div class="tbl"><table>
      <thead><tr><th>Component</th><th>Versie</th><th>Biedt API's</th><th>Gebruikt</th><th>Licentie</th><th class="num">Geheugen</th><th class="num">Image</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table></div>
  </section>''')
    chips = "".join(
        f'<a class="chip {"on" if st["aan"] else "off"}" href="#stack-{st["id"]}"><span class="dot"></span>{e(st["naam"].split(":")[-1].strip())}'
        f'<small>{"altijd aan" if st["profiel"] is None else ("aan" if st["aan"] else "uit")}</small></a>' for st in stacks)
    return f'<nav class="switcher" aria-label="Stacks">{chips}</nav>' + "\n".join(parts)


if __name__ == "__main__":
    main()
