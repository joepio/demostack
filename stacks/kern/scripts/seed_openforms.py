"""Maakt het demoformulier 'Melding openbare ruimte' in Open Formulieren, met registratie als zaak in Open Zaak."""
import os, sys, requests

BASE = f"https://formulieren.{os.environ['BASE_DOMAIN']}/api/v2"
H = {"Authorization": f"Token {os.environ['OF_TOKEN']}", "Content-Type": "application/json"}

def call(method, path, **kw):
    url = path if path.startswith("http") else f"{BASE}/{path}"
    r = requests.request(method, url, headers=H, timeout=60, **kw)
    if r.status_code >= 400:
        print(method, url, r.status_code, r.text[:2000]); sys.exit(1)
    return r.json() if r.content else None

forms = call("GET", "forms")
EXISTING = any(f["slug"] == "melding-openbare-ruimte" for f in forms)

group_id = int(os.environ["ZGW_GROUP_ID"])
components = [
    {"type": "select", "key": "soortMelding", "label": "Waar gaat uw melding over?", "validate": {"required": True},
     "dataSrc": "values", "data": {"values": [
         {"label": "Losliggende stoeptegel", "value": "stoeptegel"},
         {"label": "Kapotte straatverlichting", "value": "verlichting"},
         {"label": "Zwerfafval", "value": "afval"},
         {"label": "Iets anders", "value": "anders"}]}},
    {"type": "textfield", "key": "locatie", "label": "Waar is het? (straat en huisnummer of omschrijving)",
     "validate": {"required": True}},
    {"type": "textarea", "key": "omschrijving", "label": "Omschrijving", "validate": {"required": True}},
    {"type": "textfield", "key": "naam", "label": "Uw achternaam", "validate": {"required": True},
     "registration": {"attribute": "initiator_geslachtsnaam"}},
    {"type": "email", "key": "email", "label": "Uw e-mailadres", "validate": {"required": True}},
]
if EXISTING:
    fd = next(d for d in (lambda x: x["results"] if isinstance(x, dict) else x)(call("GET", "form-definitions")) if d["slug"] == "melding-openbare-ruimte-stap")
    call("PATCH", fd["url"], json={"configuration": {"display": "form", "components": components}})
    print("formulierdefinitie bijgewerkt"); sys.exit(0)
fd = call("POST", "form-definitions", json={
    "name": "Melding", "slug": "melding-openbare-ruimte-stap", "configuration": {"display": "form", "components": components}})
form = call("POST", "forms", json={
    "name": "Melding openbare ruimte", "internalName": "Melding openbare ruimte", "slug": "melding-openbare-ruimte",
    "active": True, "showProgressIndicator": True, "submissionAllowed": "yes",
    "translations": {"nl": {"name": "Melding openbare ruimte", "beginText": "Melding starten",
                            "previousText": "", "changeText": "", "confirmText": ""}},
    "registrationBackends": [{"key": "zaak", "name": "Open Zaak", "backend": "zgw-create-zaak", "options": {
        "zgwApiGroup": group_id, "catalogue": {"domain": "DEMO", "rsin": "002220647"},
        "caseTypeIdentification": "MOR", "documentTypeDescription": "Bijlage melding",
        "organisatieRsin": "002220647", "zaakVertrouwelijkheidaanduiding": "openbaar"}}],
})
call("POST", f"forms/{form['uuid']}/steps", json={"formDefinition": fd["url"], "index": 0,
     "translations": {"nl": {"name": "Uw melding", "previousText": "", "saveText": "", "nextText": ""}}})
print("klaar:", f"https://formulieren.{os.environ['BASE_DOMAIN']}/melding-openbare-ruimte")
