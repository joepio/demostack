"""Stap 1: maakt de KISS-objecttypen (Afdeling, Groep, Medewerker, VAC, Kennisartikel) en het objecttype Taak
(TaakV2, voor portaaltaken in NL Portal en Open Inwoner) in Objecttypen. Print uuid per naam."""
import json, os, sys, requests
B = f"https://objecttypen.{os.environ['BASE_DOMAIN']}/api/v2"
H = {"Authorization": f"Token {os.environ['OT_TOKEN_SEED']}", "Content-Type": "application/json"}
TYPES = [("Afdeling", "Afdelingen", "afdeling"), ("Groep", "Groepen", "groep"), ("Medewerker", "Medewerkers", "medewerker"),
         ("VAC", "VACs", "vac"), ("Kennisartikel", "Kennisartikelen", "kennisartikel"),
         ("Taak", "Taken", "taak")]

def call(m, url, **kw):
    r = requests.request(m, url, headers=H, timeout=30, **kw)
    if r.status_code >= 400: print(m, url, r.status_code, r.text[:1000], file=sys.stderr); sys.exit(1)
    return r.json() if r.content else None

existing = {o["name"]: o for o in call("GET", f"{B}/objecttypes")["results"]}
out = {}
for name, plural, f in TYPES:
    ot = existing.get(name) or call("POST", f"{B}/objecttypes", json={
        "name": name, "namePlural": plural, "description": "Portaaltaak (TaakV2)" if f == "taak" else f"KISS {name}", "dataClassification": "open",
        "maintainerOrganization": "Demogemeente", "allowGeometry": False})
    if not call("GET", f"{ot['url']}/versions")["results"]:
        schema = json.load(open(f"/schemas/{f}.json"))
        v = call("POST", f"{ot['url']}/versions", json={"status": "draft", "jsonSchema": schema})
        call("PATCH", v["url"], json={"status": "published"})
    out[name] = ot["uuid"]
print(json.dumps(out))
