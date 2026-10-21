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
    "taken": ("Portaaltaken (TaakV2 in Objecten)", None),
    "lab": ("VNG API Lab: MijnZaken en MijnTaken (next)", None),
    "iko": ("IKO aggregatie-API", None),
    "cloudevents": ("JSONCommit / CloudEvents (ZaakChat)", None),
    "vtb-verzoeken": ("Verzoeken API (Open VTB)", f"https://vtb.{D}/verzoeken/api/v1/openapi.yaml"),
    "vtb-taken": ("Taken API (Open VTB)", f"https://vtb.{D}/taken/api/v1/openapi.yaml"),
    "vtb-berichten": ("Berichten API (Open VTB)", f"https://vtb.{D}/berichten/api/v1/openapi.yaml"),
    "producttypen": ("Producttypen API (Open Product)", f"https://producten.{D}/producttypen/api/v1/openapi.yaml"),
    "producten": ("Producten API (Open Product)", f"https://producten.{D}/producten/api/v1/openapi.yaml"),
    "og-zgw": ("ZGW-API's in OneGround: Zaken 1.5, Catalogi 1.3, Documenten 1.7, Besluiten 1.0, Autorisaties 1.1, Notificaties 1.0", None),
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
          gebruikt=["oidc"], kan_gebruiken=["zaken", "catalogi", "documenten", "besluiten", "objecten", "objecttypen", "klantinteracties", "notificaties", "iko"]),
     ]},
    {"id": "oip", "naam": "Inwonerportaal PodiumD: Open Inwoner", "profiel": "oip",
     "uitleg": "Mijn omgeving voor inwoners (Maykin, onderdeel van PodiumD). Mijn zaken, documenten, taken en vragen, plus een CMS voor de pagina's. Ontvangt zaaknotificaties en mailt de inwoner.",
     "componenten": [
        C(naam="Open Inwoner", maker="Maykin / Dimpact", licentie="EUPL-1.2", diensten=["openinwoner", "openinwoner-celery", "openinwoner-beat"],
          biedt=[], gebruikt=["zaken", "catalogi", "documenten", "notificaties", "klantinteracties", "objecten", "objecttypen", "taken", "brp", "elastic", "oidc"]),
     ]},
    {"id": "nlportal", "naam": "Inwonerportaal Ritense: NL Portal", "profiel": "nlportal",
     "uitleg": "Portaal voor inwoners en ondernemers (Ritense), hoort bij de GZAC-stack. Haalt alles live op, bewaart zelf geen zaakgegevens; het BSN komt via token exchange in Keycloak.",
     "componenten": [
        C(naam="NL Portal", maker="Ritense", licentie="EUPL-1.2", diensten=["nlportal-backend", "nlportal"], biedt=[],
          gebruikt=["zaken", "catalogi", "documenten", "besluiten", "objecten", "taken", "klantinteracties", "brp", "oidc"]),
     ]},
    {"id": "mijnoverheid", "naam": "Overheidsbreed: MijnOverheid-demo (VNG API Lab)", "profiel": "mijnoverheid",
     "uitleg": "Experiment van VNG Realisatie: één omgeving voor gemeente en Rijk, met de Lab-API's MijnZaken en MijnTaken. Hier met een adapter die zaken, taken en BRP-gegevens van de ingelogde inwoner uit de echte registers haalt; de rest is mockdata van het Lab.",
     "componenten": [
        C(naam="MijnOverheid-demo + adapter", maker="VNG Realisatie (app), DemoStack (adapter)", licentie="EUPL-1.2",
          diensten=["mijnoverheid"], biedt=["lab"], gebruikt=["zaken", "catalogi", "documenten", "objecten", "taken", "brp", "oidc"]),
     ]},
    {"id": "zaakchat", "naam": "Gesprekken over zaken: ZaakChat", "profiel": "zaakchat",
     "uitleg": "Experiment: inwoner en behandelaar chatten over een lopende zaak, met realtime updates via CloudEvents (JSONCommit). Een koppeling logt in via Keycloak en zet zaken en statuswijzigingen uit Open Zaak door via Open Notificaties.",
     "componenten": [
        C(naam="ZaakChat", maker="Joep Meindertsma", licentie="MIT", diensten=["zaakchat"], biedt=["cloudevents"], gebruikt=[]),
        C(naam="ZaakChat-koppeling", maker="DemoStack", licentie="EUPL-1.2", diensten=["zaakchat-koppeling"], biedt=[],
          gebruikt=["zaken", "catalogi", "notificaties", "cloudevents", "oidc"]),
     ]},
    {"id": "oneground", "naam": "Tweede ZGW-implementatie: OneGround", "profiel": "oneground",
     "uitleg": "De ZGW-API's van Visma Roxit (open source sinds 2025), naast Open Zaak met dezelfde demo-catalogus en -meldingen. Eigen Autorisaties- en Notificaties-API, eigen Keycloak met een plugin voor ZGW-tokens, RabbitMQ. Multi-tenant op RSIN. Laat zien waar twee implementaties van dezelfde standaard verschillen.",
     "componenten": [
        C(naam="OneGround ZGW-API's", maker="Visma Roxit", licentie="BSD-3-Clause",
          diensten=["og-zaken", "og-catalogi", "og-documenten", "og-documenten-listener", "og-besluiten", "og-autorisaties",
                    "og-notificaties", "og-notificaties-listener", "og-referentielijsten"], biedt=["og-zgw"], gebruikt=["oidc"]),
        C(naam="Keycloak met ZGW-introspectie", maker="Red Hat / Visma Roxit (plugin)", licentie="Apache-2.0, BSD-3-Clause",
          diensten=["og-keycloak"], biedt=[], gebruikt=[]),
        C(naam="RabbitMQ", maker="Broadcom", licentie="MPL-2.0", diensten=["og-rabbitmq"], biedt=[], gebruikt=[]),
     ]},
    {"id": "openvtb", "naam": "Verzoeken, taken en berichten: Open VTB", "profiel": "openvtb",
     "uitleg": "Het register van Maykin voor Platform Dienstverlening: verzoeken (de aanvraag los van de zaak), taken voor de inwoner (formulier, link of betaling) en berichten aan de inwoner, met een vlag voor de MijnOverheid Berichtenbox. Hier met testdata voor Suzanne; de portalen en KISS lezen het nog niet.",
     "componenten": [
        C(naam="Open VTB", maker="Maykin / Platform Dienstverlening", licentie="EUPL-1.2", diensten=["openvtb", "openvtb-celery"],
          biedt=["vtb-verzoeken", "vtb-taken", "vtb-berichten"], gebruikt=["oidc"]),
     ]},
    {"id": "openproduct", "naam": "Producten: Open Product", "profiel": "openproduct",
     "uitleg": "Het register van Maykin voor producttypen (zoals de parkeervergunning, met prijzen, content en de Uniforme Productnamenlijst) en de producten van inwoners. Rechten per producttype. Hier met een parkeervergunning voor Suzanne, ontstaan uit haar zaak in Open Zaak. Open Inwoner en Open Formulieren kunnen het volgens Maykin gebruiken; hier nog niet ingericht.",
     "componenten": [
        C(naam="Open Product", maker="Maykin", licentie="EUPL-1.2", diensten=["openproduct", "openproduct-celery", "openproduct-beat"],
          biedt=["producttypen", "producten"], gebruikt=["oidc"], kan_gebruiken=["zaken"]),
     ]},
    {"id": "iko", "naam": "Klant- en objectbeeld: IKO", "profiel": "iko",
     "uitleg": "Integraal Klant- en Objectbeeld (Ritense): een aggregatielaag die gegevens uit meerdere bronnen samenvoegt tot één beeld via een eigen API. GZAC kan het tonen. De connectoren en profielen zijn hier nog niet ingericht.",
     "componenten": [
        C(naam="IKO", maker="Ritense", licentie="EUPL-1.2", diensten=["iko"], biedt=["iko"], gebruikt=["oidc"],
          kan_gebruiken=["zaken", "documenten", "klantinteracties", "objecten", "brp", "bag"]),
     ]},
]


# ---------- Stacks samenstellen: per functie de alternatieven, voorbeeldstacks en wat hier is vastgesteld ----------
# Elke rij is een functie; de opties zijn alternatieven voor elkaar. "nodig" zegt welke andere functies een
# onderdeel gebruikt; de status van zo'n koppeling komt uit KOPPELINGEN (wat in deze DemoStack is vastgesteld).
ROLLEN = [
    {"id": "portaal", "naam": "Inwonerportaal", "wie": "Inwoner", "opties": [
        {"id": "oip", "naam": "Open Inwoner", "maker": "Maykin / Dimpact", "profiel": "oip", "nodig": ["zaakregister", "taken", "klantregister", "producten"]},
        {"id": "nlportal", "naam": "NL Portal", "maker": "Ritense", "profiel": "nlportal", "nodig": ["zaakregister", "taken"]},
        {"id": "mijnoverheid", "naam": "MijnOverheid-demo", "maker": "VNG API Lab", "profiel": "mijnoverheid", "nodig": ["zaakregister", "taken"]}]},
    {"id": "formulieren", "naam": "Formulieren", "wie": "Inwoner", "opties": [
        {"id": "openforms", "naam": "Open Formulieren", "maker": "Maykin", "profiel": None, "nodig": ["zaakregister"]}]},
    {"id": "chat", "naam": "Chatten over een zaak", "wie": "Inwoner", "opties": [
        {"id": "zaakchat", "naam": "ZaakChat", "maker": "experiment", "profiel": "zaakchat", "nodig": ["zaakregister"]}]},
    {"id": "kcc", "naam": "Klantcontact (KCC)", "wie": "Medewerker", "opties": [
        {"id": "kiss", "naam": "KISS", "maker": "Dimpact / Icatt", "profiel": "kcc", "nodig": ["zaakregister", "klantregister"]}]},
    {"id": "afhandeling", "naam": "Zaken afhandelen", "wie": "Medewerker", "opties": [
        {"id": "zac", "naam": "ZAC", "maker": "Dimpact", "profiel": "zac", "nodig": ["zaakregister", "klantregister"]},
        {"id": "gzac", "naam": "GZAC (Valtimo)", "maker": "Ritense", "profiel": "gzac", "nodig": ["zaakregister", "taken"]}]},
    {"id": "klantbeeld", "naam": "Klantbeeld over bronnen heen", "wie": "Medewerker", "opties": [
        {"id": "iko", "naam": "IKO", "maker": "Ritense", "profiel": "iko", "nodig": ["zaakregister", "klantregister"]}]},
    {"id": "zaakregister", "naam": "Zaakregister (ZGW)", "wie": "Register", "opties": [
        {"id": "openzaak", "naam": "Open Zaak", "maker": "Maykin / Dimpact", "profiel": None, "nodig": []},
        {"id": "oneground", "naam": "OneGround", "maker": "Visma Roxit", "profiel": "oneground", "nodig": []}]},
    {"id": "taken", "naam": "Taken en berichten voor de inwoner", "wie": "Register", "opties": [
        {"id": "taakv2", "naam": "Objecten (TaakV2)", "maker": "Maykin", "profiel": None, "nodig": []},
        {"id": "openvtb", "naam": "Open VTB", "maker": "Maykin", "profiel": "openvtb", "nodig": []}]},
    {"id": "producten", "naam": "Producten en vergunningen", "wie": "Register", "opties": [
        {"id": "openproduct", "naam": "Open Product", "maker": "Maykin", "profiel": "openproduct", "nodig": []}]},
    {"id": "klantregister", "naam": "Klantgegevens en contactmomenten", "wie": "Register", "opties": [
        {"id": "openklant", "naam": "Open Klant", "maker": "Maykin", "profiel": None, "nodig": []}]},
]
# Voorbeeldstacks: per functie het gekozen onderdeel (None = deze stack heeft er geen)
VOORBEELDEN = [
    {"id": "podiumd", "naam": "PodiumD", "door": "Dimpact", "kies": {"portaal": "oip", "formulieren": "openforms", "kcc": "kiss",
     "afhandeling": "zac", "zaakregister": "openzaak", "taken": "taakv2", "klantregister": "openklant"}},
    {"id": "gzac", "naam": "GZAC-stack", "door": "Ritense", "kies": {"portaal": "nlportal", "formulieren": "openforms",
     "afhandeling": "gzac", "klantbeeld": "iko", "zaakregister": "openzaak", "taken": "taakv2", "klantregister": "openklant"}},
    {"id": "dienstverlening", "naam": "Platform Dienstverlening", "door": "Maykin, in ontwikkeling", "kies": {"portaal": "oip",
     "formulieren": "openforms", "kcc": "kiss", "zaakregister": "openzaak", "taken": "openvtb", "producten": "openproduct", "klantregister": "openklant"}},
    {"id": "oneground", "naam": "Met OneGround", "door": "register van Visma Roxit", "kies": {"portaal": "nlportal", "formulieren": "openforms",
     "kcc": "kiss", "zaakregister": "oneground", "taken": "taakv2", "klantregister": "openklant"}},
    {"id": "lab", "naam": "MijnServices", "door": "VNG API Lab", "kies": {"portaal": "mijnoverheid", "formulieren": "openforms",
     "zaakregister": "openzaak", "taken": "taakv2", "klantregister": "openklant"}},
]
# Wat in deze DemoStack is vastgesteld: (gebruiker, bron, status, toelichting). Status: werkt, deels, werkt-niet,
# niet-getest. Alleen "werkt" als het hier aantoonbaar draait; een koppeling die hier niet staat, is niet getest.
KOPPELINGEN = [
    ("openforms", "openzaak", "werkt", "Een melding wordt een zaak (rooktest test_submission.py)."),
    ("openforms", "oneground", "werkt", "Formulier melding-openbare-ruimte-oneground registreert in OneGround."),
    ("kiss", "openzaak", "werkt", "KISS toont de zaken van een persoon."),
    ("kiss", "oneground", "deels", "KISS toont zaken uit OneGround, maar contactmomenten staan dubbel: KISS gaat uit van één zaaksysteem per klantregister."),
    ("kiss", "openklant", "werkt", "Contactmomenten en klantbeeld."),
    ("oip", "openzaak", "werkt", "Mijn aanvragen, met notificaties bij een nieuwe status."),
    ("oip", "taakv2", "werkt", "Portaaltaak van Suzanne in het takenblok."),
    ("oip", "openklant", "werkt", "Klantgegevens en contactmomenten."),
    ("nlportal", "openzaak", "werkt", "Lopende zaken van de ingelogde inwoner."),
    ("nlportal", "taakv2", "werkt", "Portaaltaak van Suzanne onder Mijn taken."),
    ("nlportal", "oneground", "werkt-niet", "NL Portal stuurt zoekfilters in _zoek als lijst; Open Zaak accepteert dat, OneGround antwoordt 415."),
    ("mijnoverheid", "openzaak", "werkt", "Via de adapter (Lab-API MijnZaken naar ZGW)."),
    ("mijnoverheid", "taakv2", "werkt", "Via de adapter (Lab-API MijnTaken naar Objecten)."),
    ("zaakchat", "openzaak", "werkt", "Elke zaak van een testinwoner wordt een gesprek, via notificaties."),
    ("zac", "openzaak", "werkt", "Werkvoorraad en afhandeling."),
    ("zac", "openklant", "werkt", "Klantgegevens bij de zaak."),
    ("gzac", "openzaak", "werkt", "Demo-casus evenementenvergunning."),
    ("gzac", "taakv2", "deels", "GZAC schrijft portaaltaken in het oude formaat; die verschijnen niet in de portalen."),
    ("iko", "openzaak", "niet-getest", "IKO draait, maar de connectoren zijn nog niet ingericht."),
    ("iko", "openklant", "niet-getest", "IKO draait, maar de connectoren zijn nog niet ingericht."),
    ("oip", "openvtb", "niet-getest", "Open Inwoner leest Open VTB hier nog niet; taken komen uit Objecten."),
    ("oip", "openproduct", "niet-getest", "Volgens Maykin te koppelen; hier nog niet ingericht."),
    ("nlportal", "openvtb", "niet-getest", "NL Portal kent Open VTB (nog) niet; taken komen uit Objecten."),
]


def render_samenstellen():
    data = {"rollen": ROLLEN, "voorbeelden": VOORBEELDEN, "actief": sorted(ACTIVE),
            "koppelingen": [{"van": a, "naar": b, "status": st, "uitleg": u} for a, b, st, u in KOPPELINGEN]}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<div id="samenstellen" class="samenstellen"></div><script type="application/json" id="samenstellen-data">{js}</script>'


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
    profielen = [a for st in STACKS if st["profiel"] for a in ("--profile", st["profiel"])]
    cfg = json.loads(sh("docker", "compose", *profielen, "config", "--format", "json"))
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
    (HERE / "public" / "functies.html").write_text(render_functies(out))
    (HERE / "public" / "samenstellen.html").write_text(render_samenstellen())


def lic_samenvatting(componenten):
    """Unieke licenties; meervoudige (bijv. Elasticsearch, Redis) met naam erbij, zodat ze niet als gewone open source ogen."""
    out = set()
    for c in componenten:
        for part in c["licentie"].split(", "):
            out.add(f'{c["naam"].split(" ")[0]}: {part}' if " / " in part else part)
    return sorted(out, key=lambda x: (":" in x, x))


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
      <div><span>Licenties</span><strong>{e(", ".join(lic_samenvatting(st["componenten"])))}</strong></div>
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


# Functies (rijen) per stack (kolommen). Status: "hier" = draait in deze omgeving, "niet-hier" = hoort bij de stack maar
# is hier nog niet geïnstalleerd, "geen" = deze stack heeft er geen eigen onderdeel voor.
STACK_KOLOMMEN = [
    {"id": "podiumd", "naam": "PodiumD", "door": "Dimpact", "lagen": ["registers", "kcc", "zac", "oip"]},
    {"id": "gzac", "naam": "GZAC-stack", "door": "Ritense", "lagen": ["registers", "gzac", "nlportal", "iko"]},
]
FUNCTIES = [
    {"functie": "Melden en aanvragen", "wie": "Inwoner", "apis": ["formulieren", "zaken", "documenten", "objecten"],
     "podiumd": ("Open Formulieren", "hier"), "gzac": ("Open Formulieren", "hier")},
    {"functie": "Inloggen inwoner", "wie": "Inwoner", "apis": ["oidc"],
     "podiumd": ("DigiD/eHerkenning via makelaar (hier: demo-DigiD in Keycloak)", "hier"),
     "gzac": ("DigiD/eHerkenning via makelaar (hier: demo-DigiD in Keycloak)", "hier")},
    {"functie": "Mijn zaken bekijken", "wie": "Inwoner", "apis": ["zaken", "catalogi", "documenten"],
     "podiumd": ("Open Inwoner", "hier"), "gzac": ("NL Portal", "hier")},
    {"functie": "Taken voor de inwoner", "wie": "Inwoner", "apis": ["objecten", "taken"],
     "podiumd": ("Open Inwoner (TaakV2)", "hier"), "gzac": ("NL Portal (TaakV2; GZAC schrijft nog het oude formaat)", "hier")},
    {"functie": "Chatten over een zaak", "wie": "Inwoner", "apis": ["cloudevents", "notificaties"],
     "podiumd": ("Geen; hier ZaakChat als experiment", "geen"), "gzac": ("Geen; hier ZaakChat als experiment", "geen")},
    {"functie": "Gemeente en Rijk in één omgeving", "wie": "Inwoner", "apis": ["lab"],
     "podiumd": ("Geen; hier de MijnOverheid-demo van het VNG API Lab", "geen"), "gzac": ("Geen; hier de MijnOverheid-demo van het VNG API Lab", "geen")},
    {"functie": "Zaken registreren", "wie": "Register", "apis": ["zaken", "catalogi", "documenten", "besluiten"],
     "podiumd": ("Open Zaak", "hier"), "gzac": ("Open Zaak", "hier")},
    {"functie": "Andere ZGW-implementatie", "wie": "Register", "apis": ["og-zgw"],
     "podiumd": ("OneGround (Visma Roxit) draait hier naast Open Zaak", "hier"), "gzac": ("OneGround (Visma Roxit) draait hier naast Open Zaak", "hier")},
    {"functie": "Verzoeken, taken en berichten", "wie": "Register", "apis": ["vtb-verzoeken", "vtb-taken", "vtb-berichten"],
     "podiumd": ("Open VTB draait hier; nog geen afnemer", "hier"), "gzac": ("Open VTB draait hier; nog geen afnemer", "hier")},
    {"functie": "Producten en vergunningen van inwoners", "wie": "Register", "apis": ["producttypen", "producten"],
     "podiumd": ("Open Product draait hier; nog niet gekoppeld", "hier"), "gzac": ("Open Product draait hier; nog niet gekoppeld", "hier")},
    {"functie": "Klantgegevens en contactmomenten", "wie": "Register", "apis": ["klantinteracties"],
     "podiumd": ("Open Klant", "hier"), "gzac": ("Open Klant", "hier")},
    {"functie": "Overige registraties", "wie": "Register", "apis": ["objecten", "objecttypen"],
     "podiumd": ("Objecten en Objecttypen", "hier"), "gzac": ("Objecten en Objecttypen", "hier")},
    {"functie": "Berichten tussen systemen", "wie": "Register", "apis": ["notificaties"],
     "podiumd": ("Open Notificaties", "hier"), "gzac": ("Open Notificaties", "hier")},
    {"functie": "Klantcontact (KCC)", "wie": "Medewerker", "apis": ["klantinteracties", "zaken", "brp", "kvk"],
     "podiumd": ("KISS", "hier"), "gzac": ("Geen eigen KCC-werkplek; KISS is te combineren", "geen")},
    {"functie": "Klantbeeld over bronnen heen", "wie": "Medewerker", "apis": ["iko"],
     "podiumd": ("KISS (eigen samenvoeging)", "hier"), "gzac": ("IKO (bronnen nog in te richten)", "hier")},
    {"functie": "Personen en bedrijven opzoeken", "wie": "Medewerker", "apis": ["brp", "kvk"],
     "podiumd": ("KISS en ZAC (Haal Centraal BRP, KvK)", "hier"), "gzac": ("Via plugins (BRP, KvK)", "niet-hier")},
    {"functie": "Zaken afhandelen", "wie": "Medewerker", "apis": ["zaken", "catalogi", "documenten", "besluiten", "notificaties"],
     "podiumd": ("ZAC", "hier"), "gzac": ("GZAC (Valtimo)", "hier")},
    {"functie": "Interne taken en terugbelverzoeken", "wie": "Medewerker", "apis": ["klantinteracties"],
     "podiumd": ("ITA", "niet-hier"), "gzac": ("Taken in GZAC", "hier")},
    {"functie": "Processen en werkstromen", "wie": "Beheer", "apis": [],
     "podiumd": ("CMMN-model in ZAC (vast), BPMN", "hier"), "gzac": ("BPMN/DMN in Valtimo (zelf te modelleren)", "hier")},
    {"functie": "Rechten per zaaktype", "wie": "Beheer", "apis": ["oidc", "pabc"],
     "podiumd": ("Keycloak + PABC + OPA", "hier"), "gzac": ("Keycloak + rechten in Valtimo", "hier")},
]


def render_functies(stacks):
    e = html.escape
    by_id = {s["id"]: s for s in stacks}
    ver = {}
    for s in stacks:
        for c in s["componenten"]:
            for a in c["biedt"]:
                ver[a["id"]] = a["versie"]
    label = {"hier": "", "niet-hier": '<span class="tag soon">nog niet geïnstalleerd</span>', "geen": '<span class="tag off">ontbreekt</span>'}
    head = "".join(f'<th>{e(k["naam"])}<br><small>{e(k["door"])}</small></th>' for k in STACK_KOLOMMEN)
    rows, groep = [], None
    for f in FUNCTIES:
        if f["wie"] != groep:
            groep = f["wie"]
            rows.append(f'<tr class="groep"><th colspan="{2 + len(STACK_KOLOMMEN)}">{e(groep)}</th></tr>')
        apis = ", ".join(f'{e(APIS[a][0])}{" " + e(ver[a]) if ver.get(a) else ""}' for a in f["apis"]) or "-"
        cells = []
        for k in STACK_KOLOMMEN:
            comp, status = f[k["id"]]
            other = f[[x for x in STACK_KOLOMMEN if x is not k][0]["id"]][0]
            cls = "zelfde" if comp == other else "anders"
            cells.append(f'<td class="{cls} {status}">{e(comp)} {label[status]}</td>')
        rows.append(f'<tr><td><strong>{e(f["functie"])}</strong></td><td><small>{apis}</small></td>{"".join(cells)}</tr>')
    totals = []
    for k in STACK_KOLOMMEN:
        lagen = [by_id[l] for l in k["lagen"]]
        mem = sum(l["geheugen_mb"] for l in lagen); img = sum(l["image_mb"] for l in lagen); n = sum(l["containers"] for l in lagen)
        lic = lic_samenvatting([c for l in lagen for c in l["componenten"]])
        totals.append(f'<div class="stack-total"><h3>{e(k["naam"])} <small>{e(k["door"])}</small></h3>'
                      f'<div class="facts"><div><span>Geheugen</span><strong>{gb(mem)}</strong></div>'
                      f'<div><span>Images</span><strong>{gb(img)}</strong></div><div><span>Containers</span><strong>{n}</strong></div></div>'
                      f'<p class="sub"><small>Licenties: {e(", ".join(lic))}</small></p></div>')
    return (f'<div class="tbl"><table class="functies"><thead><tr><th>Functie</th><th>Standaard-API\'s</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="sub legend"><span class="sw zelfde"></span>zelfde component in beide stacks '
            f'<span class="sw anders"></span>verschillend component</p>'
            f'<div class="totals">{"".join(totals)}</div>')


if __name__ == "__main__":
    main()
