"""Stack-specifieke tests van stack "vcg" (geladen door tests/run.py).

Per component van de VCG-basisset een rooktest op de koppeling die een gemeente
verwacht, niet alleen "draait het":

- Keycloak-realm vcg: medewerkers loggen met OIDC in bij Open Organisatie en Open Beheer
- Open Organisatie: medewerkers en teams; een wijziging komt via Open Notificaties
  (kanaal medewerkers) bij de abonnee
- GPP-publicatiebank: gepubliceerde Woo-documenten staan in de Documenten API van
  Open Zaak en zijn te downloaden
- Open Beheer: zaaktypen uit de Catalogi API van Open Zaak, na OIDC-login
- Operaton: de behandelaar rondt de gebruikerstaak af; de procesworker zet resultaat en
  eindstatus op de zaak in Open Zaak
- OpenPlan: plannen met doel en instrument, verwijzend naar zaken en medewerkers
- OpenPDC en OpenPub: openbare REST-API's met de inhoud van Voorbeeldstad
- OpenRegister: register, schema en objecten; validatie tegen het schema
- OpenFSC: contract tussen Voorbeeldstad en de BRP-leverancier, bevraging via outway en
  inway, transactielog aan beide kanten, geen toegang zonder grant of certificaat

Isolatietype "openbaar": openbare kanalen (zonder inlog) mogen geen BSN's of namen van
testburgers tonen.
"""
import html
import re
import sys
import time

import requests

from checks.isolatie import CAT as ISO, isolatietype
from checks.rook import rook
from kader import ROOT, Context, eis
from lib import KEYCLOAK, SINK, Client, env, open_zaak_beheer

sys.path.insert(0, str(ROOT / "stacks" / "vcg"))
import fsc  # noqa: E402

OPENORGANISATIE = "http://openorganisatie.local:8000"
PUBLICATIEBANK = "http://publicatiebank.local:8000"
OPENBEHEER = "http://openbeheer.local:8000"
OPERATON = "http://operaton.local:8080/engine-rest"
OPENPLAN = "http://openplan.local:8000"
WORDPRESS = "http://wordpress.local"
OPENREGISTER = "http://openregister.local/index.php/apps/openregister/api"
ZAAK_OPERATON = "VBS-2026-000110"
AUDIT = {"Audit-User-ID": "demogemeente-tests", "Audit-User-Representation": "Tests demogemeente",
         "Audit-Remarks": "rooktest stack vcg"}

# Testburgers met hun naam, voor de controle op openbare kanalen
TESTBURGERS = {
    "999990627": ["Stephan", "Janssen"], "999997609": ["Eleonora", "Crooy"],
    "999993409": ["Thea", "Kouwenhoven"], "999991991": ["Jeroen", "Altena"],
}


# ------------------------------------------------------------- helpers
def medewerker_login(basis, gebruiker):
    """OIDC-login (authorization code flow) bij een Django-beheeromgeving via realm vcg."""
    s = requests.Session()
    r = s.get(f"{basis}/auth/oidc/authenticate/?next=/admin/", allow_redirects=False, timeout=30)
    eis(r.status_code == 302, f"geen OIDC-redirect ({r.status_code})")
    locatie = r.headers["Location"]
    eis("/realms/vcg/" in locatie, f"redirect gaat niet naar realm vcg: {locatie[:80]}")
    r = s.get(locatie.replace("http://localhost:8080", KEYCLOAK), timeout=30)
    m = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', r.text)
    eis(m, f"geen Keycloak-loginformulier ({r.status_code})")
    r = s.post(html.unescape(m.group(1)).replace("http://localhost:8080", KEYCLOAK), allow_redirects=False,
               timeout=30, data={"username": gebruiker, "password": env("MEDEWERKER_WACHTWOORD"), "credentialId": ""})
    eis(r.status_code in (302, 303), f"Keycloak weigert {gebruiker} ({r.status_code})")
    r = s.get(r.headers["Location"], timeout=30)
    eis(r.status_code == 200 and "/admin/" in r.url, f"na de callback {r.status_code} op {r.url}")
    return s


def oo_client():
    return Client(f"{OPENORGANISATIE}/organisatie/api/v0",
                  lambda: {"Authorization": f"Token {env('OPENORGANISATIE_BEHEER_TOKEN')}"}, "Open Organisatie")


def gpp_client(token_var="PUBLICATIEBANK_BEHEER_TOKEN"):
    return Client(f"{PUBLICATIEBANK}/api/v2", lambda: {"Authorization": f"Token {env(token_var)}", **AUDIT},
                  "GPP-publicatiebank")


def operaton(methode, pad, auth=None, verwacht=(200, 204), **kw):
    r = requests.request(methode, f"{OPERATON}/{pad}", timeout=30,
                         auth=auth or (env("ADMIN_USERNAME"), env("ADMIN_PASSWORD")), **kw)
    eis(r.status_code in verwacht, f"Operaton {methode} {pad} gaf {r.status_code}: {r.text[:200]}")
    return r.json() if r.content else None


def openregister(methode, pad, auth=True, **kw):
    return requests.request(methode, f"{OPENREGISTER}/{pad}", timeout=30,
                            auth=(env("ADMIN_USERNAME"), env("ADMIN_PASSWORD")) if auth else None,
                            headers={"OCS-APIRequest": "true", "Accept": "application/json"}, **kw)


# ------------------------------------------------------- Keycloak-realm vcg
@rook("keycloak-vcg", "medewerker logt via OIDC in bij Open Organisatie", vereist=("openorganisatie",))
def _(ctx):
    s = medewerker_login(OPENORGANISATIE, "beheer.devos")
    r = s.get(f"{OPENORGANISATIE}/admin/", timeout=30)
    eis("logout" in r.text.lower(), "geen beheersessie na de login")
    return "beheer.devos (Superuser) in de admin van Open Organisatie"


@rook("openbeheer", "behandelaar zonder beheerrol komt niet binnen", vereist=("keycloak-vcg",))
def _(ctx):
    """Open Beheer 0.9.0 laat elke ingelogde gebruiker zaaktypen beheren (DRF
    IsAuthenticated); de inlogflow beheer-browser van realm vcg weigert daarom iedereen
    zonder de rol Functioneel-Beheerder al bij Keycloak."""
    try:
        s = medewerker_login(OPENBEHEER, "a.vermeulen")
    except AssertionError as e:
        return f"geweigerd bij de login ({e})"
    r = s.get(f"{OPENBEHEER}/api/v1/service/catalogi-api/zaaktypen/", timeout=30)
    eis(r.status_code in (401, 403), f"behandelaar a.vermeulen krijgt {r.status_code} op de zaaktypen van Open Beheer")
    return f"login lukt, maar {r.status_code} op de beheer-API"


# --------------------------------------------------------- Open Organisatie
@rook("openorganisatie", "afdelingen, teams en medewerkers van Voorbeeldstad")
def _(ctx):
    oo = oo_client()
    afdelingen = oo.lijst("organisatorische-eenheid")
    teams = oo.lijst("teams")
    medewerkers = oo.lijst("medewerkers")
    eis(len(afdelingen) >= 3 and len(teams) >= 5 and len(medewerkers) >= 5,
        f"te weinig: {len(afdelingen)} afdelingen, {len(teams)} teams, {len(medewerkers)} medewerkers")
    parkeren = [m for m in medewerkers if any(t.get("naam") == "Parkeren" for t in m.get("teams", []))]
    eis(parkeren, "team Parkeren heeft geen medewerkers")
    return (f"{len(afdelingen)} afdelingen, {len(teams)} teams, {len(medewerkers)} medewerkers; "
            f"Parkeren: {parkeren[0]['voornaam']} {parkeren[0]['achternaam']}")


@rook("openorganisatie", "wijziging medewerker > Open Notificaties > abonnee",
      vereist=("opennotificaties", "notificatie-sink"))
def _(ctx):
    oo = oo_client()
    m = next(x for x in oo.lijst("medewerkers") if x["medewerkerId"] == "mdw-0404")

    def treffers():
        return [n["notificatie"] for n in requests.get(f"{SINK}/notificaties", timeout=10).json()["notificaties"]
                if n["notificatie"].get("kanaal") == "medewerkers" and n["notificatie"].get("resourceUrl") == m["url"]
                and n["notificatie"].get("actie") in ("partial_update", "update")]

    voor = len(treffers())
    start = time.time()
    oo.patch(m["url"], {"telefoonnummer": m.get("telefoonnummer") or "14 0999"})
    while time.time() - start < 60:
        nu = treffers()
        if len(nu) > voor:
            return f"'medewerkers/{nu[-1]['actie']}' afgeleverd na {time.time() - start:.1f}s"
        time.sleep(2)
    raise AssertionError("geen notificatie op kanaal medewerkers binnen 60s")


# -------------------------------------------------------- GPP-publicatiebank
@rook("publicatiebank", "gepubliceerde Woo-documenten staan in Open Zaak", vereist=("openzaak",))
def _(ctx):
    gpp = gpp_client()
    pubs = [p for p in gpp.lijst("publicaties") if p["publicatiestatus"] == "gepubliceerd"]
    eis(len(pubs) >= 2, f"{len(pubs)} gepubliceerde publicaties, verwacht 2")
    docs = gpp.lijst("documenten")
    eis(docs and all(d["uploadVoltooid"] for d in docs), "niet elk document is volledig geupload")
    oz = open_zaak_beheer()
    gevonden = 0
    for d in docs:
        eios = oz.lijst("documenten/api/v1/enkelvoudiginformatieobjecten", bronorganisatie=env("GEMEENTE_RSIN"))
        if any(e["titel"] == d["officieleTitel"] for e in eios):
            gevonden += 1
    eis(gevonden == len(docs), f"{gevonden} van {len(docs)} documenten gevonden in de Documenten API")
    r = requests.get(f"{PUBLICATIEBANK}/api/v2/documenten/{docs[0]['uuid']}/download", timeout=30,
                     headers={"Authorization": f"Token {env('PUBLICATIEBANK_PUBLIEK_TOKEN')}", **AUDIT})
    eis(r.status_code == 200 and r.content.startswith(b"%PDF"), f"download gaf {r.status_code}")
    return f"{len(pubs)} publicaties, {len(docs)} documenten in Open Zaak, download {len(r.content)} bytes PDF"


@rook("publicatiebank", "leestoken kan niet schrijven")
def _(ctx):
    r = requests.post(f"{PUBLICATIEBANK}/api/v2/organisaties", timeout=30, json={"naam": "Test", "isActief": True},
                      headers={"Authorization": f"Token {env('PUBLICATIEBANK_PUBLIEK_TOKEN')}", **AUDIT})
    eis(r.status_code == 403, f"schrijven met het leestoken gaf {r.status_code}")
    return "403"


# ------------------------------------------------------------- Open Beheer
@rook("openbeheer", "zaaktypen uit Open Zaak na OIDC-login", vereist=("openzaak", "keycloak-vcg"))
def _(ctx):
    s = medewerker_login(OPENBEHEER, "beheer.devos")
    wie = s.get(f"{OPENBEHEER}/api/v1/whoami/", timeout=30).json()
    r = s.get(f"{OPENBEHEER}/api/v1/service/catalogi-api/zaaktypen/", timeout=30)
    eis(r.status_code == 200, f"zaaktypen gaf {r.status_code}")
    data = r.json()
    zaaktypen = data.get("results", data if isinstance(data, list) else [])
    eis(zaaktypen, "geen zaaktypen")
    return f"{wie['firstName']} {wie['lastName']} ziet {data.get('count', len(zaaktypen))} zaaktypen"


# ---------------------------------------------------------------- Operaton
@rook("operaton", "behandelaar rondt taak af, worker sluit de zaak in Open Zaak", vereist=("openzaak",))
def _(ctx):
    oz = open_zaak_beheer()
    zaak = oz.eerste("zaken/api/v1/zaken", identificatie=ZAAK_OPERATON)
    eis(zaak, f"zaak {ZAAK_OPERATON} ontbreekt (seed gedraaid?)")
    taken = operaton("GET", "task", params={"processInstanceBusinessKey": ZAAK_OPERATON})
    stap = "taak was al afgerond"
    if taken:
        taak = taken[0]
        eis(taak["name"] == "Aanvraag beoordelen", f"onverwachte taak {taak['name']}")
        # De behandelaar (team Parkeren) claimt en rondt af met zijn eigen account
        auth = ("l.smits", env("MEDEWERKER_WACHTWOORD"))
        operaton("POST", f"task/{taak['id']}/claim", auth=auth, json={"userId": "l.smits"})
        operaton("POST", f"task/{taak['id']}/complete", auth=auth,
                 json={"variables": {"besluit": {"value": "verleend", "type": "String"}}})
        stap = "l.smits rondt 'Aanvraag beoordelen' af"
    start = time.time()
    while time.time() - start < 90:
        zaak = oz.get(zaak["url"])
        if zaak.get("einddatum"):
            break
        time.sleep(3)
    eis(zaak.get("einddatum"), "zaak niet afgesloten binnen 90s (procesworker?)")
    resultaat = oz.get(zaak["resultaat"])
    rt = oz.get(resultaat["resultaattype"])
    rollen = oz.lijst("zaken/api/v1/rollen", zaak=zaak["url"], omschrijvingGeneriek="behandelaar")
    eis(rollen, "geen behandelaar op de zaak")
    hist = operaton("GET", "history/process-instance", params={"processInstanceBusinessKey": ZAAK_OPERATON})
    eis(hist and hist[0]["state"] == "COMPLETED", f"proces niet afgerond: {hist[0]['state'] if hist else 'onbekend'}")
    return (f"{stap}; zaak {ZAAK_OPERATON}: resultaat {rt['omschrijving']}, einddatum {zaak['einddatum']}, "
            f"behandelaar {rollen[0]['betrokkeneIdentificatie'].get('identificatie')}")


@rook("operaton", "REST-API weigert zonder inlog")
def _(ctx):
    r = requests.get(f"{OPERATON}/process-instance", timeout=30)
    eis(r.status_code == 401, f"zonder inlog {r.status_code}")
    return "401"


# ---------------------------------------------------------------- OpenPlan
@rook("openplan", "plannen met doel en instrument")
def _(ctx):
    op = Client(f"{OPENPLAN}/plannen/api/v0", lambda: {"Authorization": f"Token {env('OPENPLAN_BEHEER_TOKEN')}"},
                "OpenPlan")
    plannen = op.lijst("plan")
    doelen = op.lijst("doel")
    instrumenten = op.lijst("instrument")
    eis(len(plannen) >= 2 and len(doelen) >= 2 and len(instrumenten) >= 2,
        f"{len(plannen)} plannen, {len(doelen)} doelen, {len(instrumenten)} instrumenten")
    zaken = sorted(p["zaak"].rsplit(":", 1)[-1] for p in plannen if p.get("zaak"))
    return f"{len(plannen)} plannen ({', '.join(zaken)}), {len(doelen)} doelen, {len(instrumenten)} instrumenten"


@rook("openplan", "zonder token geen persoonsgegevens")
def _(ctx):
    r = requests.get(f"{OPENPLAN}/plannen/api/v0/persoon", timeout=30)
    eis(r.status_code in (401, 403), f"zonder token {r.status_code}")
    return f"{r.status_code}"


# ------------------------------------------------------- OpenPDC en OpenPub
@rook("openpdc", "producten en diensten met thema")
def _(ctx):
    items = requests.get(f"{WORDPRESS}/wp-json/owc/pdc/v1/items", timeout=30).json()["data"]
    eis(len(items) >= 3, f"{len(items)} items")
    pv = next((i for i in items if i["slug"] == "parkeervergunning-bewoners"), None)
    eis(pv, "item parkeervergunning-bewoners ontbreekt")
    detail = requests.get(f"{WORDPRESS}/wp-json/owc/pdc/v1/items/{pv['id']}", timeout=30).json()
    themas = [t["title"] for t in detail.get("connected", {}).get("pdc-category", [])]
    eis(themas, "item hangt niet aan een thema (Posts 2 Posts)")
    return f"{len(items)} items; '{pv['title']}' onder thema {', '.join(themas)}"


@rook("openpub", "nieuwsberichten")
def _(ctx):
    r = requests.get(f"{WORDPRESS}/wp-json/owc/openpub/v1/items", timeout=30)
    eis(r.status_code == 200, f"{r.status_code}")
    items = r.json()["data"]
    eis(len(items) >= 2, f"{len(items)} berichten")
    return "; ".join(i["title"] for i in items[:2])


# ------------------------------------------------------------ OpenRegister
@rook("openregister", "register, schema en objecten; validatie tegen het schema")
def _(ctx):
    r = openregister("GET", "objects/openbare-ruimte/speelplek")
    eis(r.status_code == 200, f"objecten gaf {r.status_code}")
    objecten = r.json()["results"]
    eis(len(objecten) >= 3, f"{len(objecten)} speelplekken")
    fout = openregister("POST", "objects/openbare-ruimte/speelplek", json={"wijk": "Centrum", "toestellen": "veel"})
    eis(fout.status_code in (400, 422), f"ongeldig object gaf {fout.status_code}, verwacht 400/422")
    return f"{len(objecten)} speelplekken; ongeldig object geweigerd ({fout.status_code})"


@rook("openregister", "zonder inlog geen objecten")
def _(ctx):
    r = openregister("GET", "objects/openbare-ruimte/speelplek", auth=False)
    if r.status_code in (401, 403):
        return f"{r.status_code}"
    aantal = len(r.json().get("results", []))
    eis(aantal == 0, f"zonder inlog {aantal} objecten zichtbaar")
    return "200 met een lege lijst (objecten zijn niet gepubliceerd)"


# ----------------------------------------------------------------- OpenFSC
@rook("openfsc", "alle FSC-componenten gereed")
def _(ctx):
    status = {n: fsc.gezond(n) for n in fsc.MONITORING}
    niet = [n for n, s in status.items() if s != 200]
    eis(not niet, f"niet gereed: {niet}")
    return f"{len(status)} componenten /health/ready 200"


@rook("openfsc", "contract Voorbeeldstad en BRP-leverancier geldig")
def _(ctx):
    pub = fsc.contracten("brp", "GRANT_TYPE_SERVICE_PUBLICATION")
    eis(pub and pub[0]["state"] == "CONTRACT_STATE_VALID", "dienstpublicatie niet geldig")
    contract, grant = fsc.grant_dienstverbinding()
    eis(contract, "geen contract voor de dienstverbinding (seed gedraaid?)")
    eis(contract["state"] == "CONTRACT_STATE_VALID", f"contract {contract['state']}")
    ondertekend = sorted(contract["signatures"]["accept"])
    eis(ondertekend == sorted([fsc.VOORBEELDSTAD_ID, fsc.BRP_ID]), f"getekend door {ondertekend}")
    ctx.gedeeld["fsc_grant"] = grant["hash"]
    return f"dienst {fsc.DIENST} gepubliceerd; verbinding getekend door beide peers"


@rook("openfsc", "BRP bevragen via outway en inway, met transactielog", vereist=("brp-mock",))
def _(ctx):
    _, grant = fsc.grant_dienstverbinding()
    eis(grant, "geen grant")
    r = fsc.roep_brp_aan(ctx.burger("C"), grant["hash"])
    eis(r.status_code == 200, f"outway gaf {r.status_code}: {r.text[:200]}")
    p = r.json()["personen"][0]
    eis(p["burgerservicenummer"] == ctx.burger("C"), "verkeerde persoon")
    tid = r.headers.get("Fsc-Transaction-Id")
    time.sleep(2)
    uit = fsc.api("voorbeeldstad", "manager", "GET", "/v1/logs", params={"limit": 50})["records"]
    inn = fsc.api("brp", "manager", "GET", "/v1/logs", params={"limit": 50})["records"]
    if tid:
        eis(any(x["transaction_id"] == tid for x in uit), f"transactie {tid} niet in de log van Voorbeeldstad")
        eis(any(x["transaction_id"] == tid for x in inn), f"transactie {tid} niet in de log van de BRP-leverancier")
    else:
        eis(uit and inn, "transactielog leeg")
    return (f"{p['naam']['voornamen']} {p['naam']['geslachtsnaam']} via FSC; transactie "
            f"{(tid or uit[0]['transaction_id'])[:13]}... gelogd bij afnemer en aanbieder")


@rook("openfsc", "geen toegang zonder grant of certificaat")
def _(ctx):
    r = requests.post(f"{fsc.OUTWAY}/personen", json={}, timeout=30)
    eis(r.status_code in (400, 403), f"outway zonder grant gaf {r.status_code}")
    try:
        r2 = requests.post("https://inway.brp.fsc.local:443/personen", json={}, timeout=15,
                           verify=str(fsc.PKI / "groep" / "ca" / "root.pem"))
        geweigerd = r2.status_code in (400, 401, 403)
        detail = f"inway zonder clientcertificaat: {r2.status_code}"
    except requests.exceptions.SSLError:
        geweigerd, detail = True, "inway zonder clientcertificaat: TLS-handshake geweigerd"
    except requests.exceptions.ConnectionError:
        geweigerd, detail = True, "inway zonder clientcertificaat: verbinding verbroken"
    eis(geweigerd, detail)
    return f"outway zonder grant {r.status_code} ({r.json().get('code')}); {detail}"


# -------------------------------------------------- isolatie: openbare kanalen
@isolatietype("openbaar")
def _openbaar(ctx: Context, kanaal: dict):
    kid = kanaal["id"]
    headers = {}
    if kanaal.get("token_env"):
        headers = {"Authorization": f"Token {env(kanaal['token_env'])}", **AUDIT}

    def controleer(url):
        def fn():
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code in (401, 403):
                return f"{r.status_code}: niet openbaar"
            eis(r.status_code == 200, f"{r.status_code}")
            tekst = r.text
            lek = [bsn for bsn in TESTBURGERS if bsn in tekst]
            lek += [" ".join(n) for n in TESTBURGERS.values() if all(d in tekst for d in n)]
            eis(not lek, f"persoonsgegevens van testburgers zichtbaar: {lek}")
            return f"200, {len(tekst)} bytes zonder BSN of naam van een testburger"
        return fn

    for url in kanaal.get("urls", []):
        sub = url.rstrip("/").rsplit("/", 1)[-1]
        ctx.voer_uit(f"{ISO}/{kid}/{sub}", ISO, kid, f"openbaar: {url.split('//', 1)[-1]}", controleer(url))
