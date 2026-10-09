"""Maakt of werkt bij: het demoformulier 'Melding openbare ruimte' in Open Formulieren.

De zaak in Open Zaak krijgt een leesbare omschrijving en toelichting uit het formulier, een locatie (kaart)
en, als de inwoner inlogt met DigiD (demo), een initiator met BSN.
"""
import os, sys, requests

BASE = f"https://formulieren.{os.environ['BASE_DOMAIN']}/api/v2"
H = {"Authorization": f"Token {os.environ['OF_TOKEN']}", "Content-Type": "application/json"}


def call(method, path, **kw):
    url = path if path.startswith("http") else f"{BASE}/{path}"
    r = requests.request(method, url, headers=H, timeout=60, **kw)
    if r.status_code >= 400:
        print(method, url, r.status_code, r.text[:2000]); sys.exit(1)
    return r.json() if r.content else None


def results(x):
    return x["results"] if isinstance(x, dict) else x


group_id = int(os.environ["ZGW_GROUP_ID"])
SOORTEN = ["Losliggende stoeptegel", "Kapotte straatverlichting", "Zwerfafval", "Overhangend groen", "Iets anders"]
components = [
    {"type": "select", "key": "soortMelding", "label": "Waar gaat uw melding over?", "validate": {"required": True},
     "dataSrc": "values", "data": {"values": [{"label": s, "value": s} for s in SOORTEN]}},
    {"type": "map", "key": "locatieKaart", "label": "Waar is het? Klik op de kaart",
     "useConfigDefaultMapSettings": True, "interactions": {"marker": True, "polygon": False, "polyline": False},
     "registration": {"attribute": "locatie_coordinaat"}},
    {"type": "textfield", "key": "locatie", "label": "Adres of omschrijving van de plek", "validate": {"required": True}},
    {"type": "textarea", "key": "omschrijving", "label": "Wat is er aan de hand?", "validate": {"required": True}},
    {"type": "textfield", "key": "naam", "label": "Uw achternaam", "validate": {"required": True},
     "registration": {"attribute": "initiator_geslachtsnaam"}},
    {"type": "email", "key": "email", "label": "Uw e-mailadres", "validate": {"required": True}},
]
options = {
    "zgwApiGroup": group_id, "catalogue": {"domain": "DEMO", "rsin": "002220647"},
    "caseTypeIdentification": "MOR", "documentTypeDescription": "Bijlage melding",
    "organisatieRsin": "002220647", "zaakVertrouwelijkheidaanduiding": "openbaar",
    "zaakOmschrijving": "{{ variables.soortMelding }}: {{ variables.locatie }}",
    "zaakToelichting": "{{ variables.omschrijving }}\n\nMelder: {{ variables.naam }} ({{ variables.email }})",
}
form_fields = {
    "name": "Melding openbare ruimte", "internalName": "Melding openbare ruimte", "slug": "melding-openbare-ruimte",
    "active": True, "showProgressIndicator": True, "submissionAllowed": "yes",
    "translations": {"nl": {"name": "Melding openbare ruimte", "beginText": "Melding starten",
                            "previousText": "Vorige", "changeText": "Wijzigen", "confirmText": "Melding versturen"}},
    # Inloggen is niet verplicht; met DigiD (demo) komt het BSN als initiator op de zaak
    "authBackends": [{"backend": "digid_oidc", "options": {}}], "loginRequired": False,
    "registrationBackends": [{"key": "zaak", "name": "Open Zaak", "backend": "zgw-create-zaak", "options": options}],
}

STEP_NL = {"name": "Uw melding", "previousText": "Vorige", "saveText": "Tussentijds opslaan", "nextText": "Volgende"}
forms = results(call("GET", "forms"))
form = next((f for f in forms if f["slug"] == "melding-openbare-ruimte"), None)
config = {"display": "form", "components": components}
if form:
    fd = next(d for d in results(call("GET", "form-definitions")) if d["slug"] == "melding-openbare-ruimte-stap")
    call("PATCH", fd["url"], json={"configuration": config, "name": "Uw melding",
                                   "translations": {"nl": {"name": "Uw melding"}, "en": {"name": "Your report"}}})
    call("PATCH", form["url"], json=form_fields)
    for step in results(call("GET", f"forms/{form['uuid']}/steps")):
        call("PATCH", step["url"], json={"translations": {"nl": STEP_NL}})
    print("formulier bijgewerkt")
else:
    fd = call("POST", "form-definitions", json={"name": "Uw melding", "slug": "melding-openbare-ruimte-stap",
                                                 "translations": {"nl": {"name": "Uw melding"}, "en": {"name": "Your report"}},
                                                 "configuration": config})
    form = call("POST", "forms", json=form_fields)
    call("POST", f"forms/{form['uuid']}/steps", json={"formDefinition": fd["url"], "index": 0,
         "translations": {"nl": STEP_NL}})
    print("klaar:", f"https://formulieren.{os.environ['BASE_DOMAIN']}/melding-openbare-ruimte")
