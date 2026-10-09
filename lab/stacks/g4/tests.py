"""Stack-specifieke tests van stack "g4" (geladen door tests/run.py).

1. De tests van stack maykin voor wat G4 met het Maykin-landschap deelt: Open
   Formulieren (met isolatietype "openformulieren"), Open VTB en de BRP-vertaler.
2. NL Portal: burger logt in via de DigiD-simulatie (authorization code flow tegen
   realm voorbeeldstad, client nlportal), het backend wisselt het token in (token
   exchange) en de tests vragen zaken, taken, berichten en persoon op via GraphQL.
   Isolatietype "nlportal": burger A probeert gegevens van burger B te zien.
3. GZAC: de aanvraag parkeervergunning die de seed startte, staat als zaak in Open Zaak
   (rol, status), als taak in de werkvoorraad en als portaaltaak in Open Object.
4. IKO: het profiel "zaken-van-burger" met een medewerkerstoken.
"""
import html
import importlib.util
import os
import re
import urllib.parse

import requests

from checks.isolatie import CAT as ISO, isolatietype
from checks.rook import REGISTER, jwt_claims, rook
from kader import ROOT, Context, eis
from lib import KEYCLOAK, env, objecttype_url, open_object, zgw_client

# ------------------------------------------------- tests van stack maykin
_spec = importlib.util.spec_from_file_location("stack_tests_maykin_via_g4", ROOT / "stacks" / "maykin" / "tests.py")
MAYKIN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MAYKIN)
# Open Inwoner draait in G4 niet (NL Portal is het burgerportaal)
REGISTER[:] = [t for t in REGISTER if t["component"] != "openinwoner"]


def poort(naam, standaard):
    return os.environ.get(f"PORT_{naam}", str(standaard))


NLPORTAL_API = "http://nlportal-backend.local:8000"
NLPORTAL = "http://nlportal.local:8080"
NLPORTAL_REDIRECT = f"http://localhost:{poort('NLPORTAL', 8203)}/oidc/callback"
GZAC_API = "http://gzac-backend.local:8000"
GZAC = "http://gzac.local:8080"
IKO = "http://iko.local:8000"
IKO_BEHEER = "http://iko.local:9090"
OPENZAAK = "http://openzaak.local:8000"
OBJECTTYPE_PORTAALTAAK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c3"
VERWACHTE_ZAKEN_A = {"VBS-2026-000101", "VBS-2026-000102"}
# Testburger D (Jeroen Altena): zijn aanvraag parkeervergunning loopt via GZAC (stacks/g4/seed.py)
BURGER_D = "999991991"


# ------------------------------------------------------------------ NL Portal
def nlportal_token(bsn):
    """Authorization code flow zoals de NL Portal-frontend die doet, vanuit de tools-container."""
    realm = f"{KEYCLOAK}/realms/voorbeeldstad/protocol/openid-connect"
    s = requests.Session()
    r = s.get(f"{realm}/auth", timeout=30, params={
        "client_id": "nlportal", "redirect_uri": NLPORTAL_REDIRECT, "response_type": "code", "scope": "openid"})
    m = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', r.text)
    eis(m, f"geen Keycloak-loginformulier voor client nlportal ({r.status_code})")
    actie = html.unescape(m.group(1)).replace("http://localhost:8080", KEYCLOAK)
    r = s.post(actie, allow_redirects=False, timeout=30,
               data={"username": bsn, "password": env("DIGID_SIM_WACHTWOORD"), "credentialId": ""})
    eis(r.status_code in (302, 303), f"Keycloak weigert de login van {bsn} ({r.status_code})")
    locatie = r.headers["Location"]
    eis(locatie.startswith(NLPORTAL_REDIRECT), f"onverwachte redirect {locatie[:80]}")
    code = urllib.parse.parse_qs(urllib.parse.urlsplit(locatie).query)["code"][0]
    r = requests.post(f"{realm}/token", timeout=30, data={
        "grant_type": "authorization_code", "client_id": "nlportal", "code": code, "redirect_uri": NLPORTAL_REDIRECT})
    eis(r.status_code == 200, f"code inwisselen gaf {r.status_code}")
    return r.json()["access_token"]


def np_token(ctx, letter):
    tokens = ctx.gedeeld.setdefault("nlportal_tokens", {})
    if letter not in tokens:
        tokens[letter] = nlportal_token(BURGER_D if letter == "D" else ctx.burger(letter))
    return tokens[letter]


def gql(token, query, **variabelen):
    """GraphQL-aanroep; geeft (status, data, fouten)."""
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(f"{NLPORTAL_API}/graphql", json={"query": query, "variables": variabelen}, headers=h, timeout=90)
    if r.status_code != 200:
        return r.status_code, None, r.text[:200]
    body = r.json()
    return 200, body.get("data"), body.get("errors")


def gql_ok(token, query, **variabelen):
    status, data, fouten = gql(token, query, **variabelen)
    eis(status == 200 and not fouten and data is not None, f"GraphQL gaf {status}: {str(fouten)[:300]}")
    return data


Q_ZAKEN = "{ getZaken(pageSize: 100) { content { uuid identificatie omschrijving status { statustype { omschrijving } } " \
          "documenten { identificatie titel } } } }"
Q_TAKEN = "{ getTakenV2(pageSize: 100) { totalElements content { id titel status identificatie { type value } } } }"
Q_BERICHTEN = "{ getBerichten(pageSize: 100) { totalElements content { id onderwerp identificatie { type value } } } }"


@rook("nlportal", "DigiD-login, token exchange en persoon uit de BRP", vereist=("keycloak", "brp-api"))
def _(ctx):
    token = np_token(ctx, "A")
    claims = jwt_claims(token)
    eis(claims.get("bsn") == ctx.burger("A"), "geen claim bsn in het token van de DigiD-simulatie")
    p = gql_ok(token, "{ getPersoonV2 { burgerservicenummer naam { voornamen geslachtsnaam } } }")["getPersoonV2"]
    eis(p and p["burgerservicenummer"] == ctx.burger("A"), f"verkeerde persoon: {p}")
    return f"ingelogd als {p['naam']['voornamen']} {p['naam']['geslachtsnaam']} ({p['burgerservicenummer']})"


@rook("nlportal", "zaken van burger A", vereist=("openzaak",))
def _(ctx):
    zaken = gql_ok(np_token(ctx, "A"), Q_ZAKEN)["getZaken"]["content"]
    nummers = {z["identificatie"] for z in zaken}
    eis(nummers == VERWACHTE_ZAKEN_A, f"zaken van A: {sorted(nummers)}")
    return ", ".join(f"{z['identificatie']} ({z['status']['statustype']['omschrijving']})" for z in zaken)


@rook("nlportal", "burger D ziet zijn aanvraag uit GZAC met de actuele status", vereist=("openzaak", "gzac"))
def _(ctx):
    zaken = gql_ok(np_token(ctx, "D"), Q_ZAKEN)["getZaken"]["content"]
    gzac = [z for z in zaken if not z["identificatie"].startswith("VBS-")]
    eis(gzac, f"de zaak parkeervergunning uit GZAC staat niet in Mijn zaken van D ({[z['identificatie'] for z in zaken]})")
    status = gzac[0]["status"]["statustype"]["omschrijving"]
    eis(status == "In behandeling", f"status {status}, verwacht In behandeling (gezet door het GZAC-proces)")
    return f"{gzac[0]['identificatie']}, status {status}; D heeft {len(zaken)} zaken"


@rook("nlportal", "zaakdetail met status en documenten", vereist=("openzaak",))
def _(ctx):
    token = np_token(ctx, "A")
    zaken = gql_ok(token, Q_ZAKEN)["getZaken"]["content"]
    z = next(z for z in zaken if z["identificatie"] == "VBS-2026-000101")
    d = gql_ok(token, "query($id: UUID!) { getZaak(id: $id) { identificatie statusGeschiedenis { statustype { omschrijving } } "
                      "documenten { identificatie titel } } }", id=z["uuid"])["getZaak"]
    eis(d["documenten"], "geen documenten bij VBS-2026-000101")
    r = requests.get(f"{NLPORTAL_API}/api/zakenapi/zaakdocument/{d['documenten'][0]['identificatie']}/content",
                     headers={"Authorization": f"Bearer {token}"}, timeout=60)
    eis(r.status_code == 200 and r.content, f"document downloaden gaf {r.status_code}")
    return f"{len(d['statusGeschiedenis'])} statussen, {len(d['documenten'])} documenten, download {len(r.content)} bytes"


@rook("nlportal", "taken van burger A (Open Object, taak v2)", vereist=("openobject",))
def _(ctx):
    taken = gql_ok(np_token(ctx, "A"), Q_TAKEN)["getTakenV2"]
    eis(taken["totalElements"] >= 2, f"{taken['totalElements']} taken, verwacht er 2")
    vreemd = [t for t in taken["content"] if t["identificatie"]["value"] != ctx.burger("A")]
    eis(not vreemd, f"taken van een ander BSN: {vreemd}")
    return f"{taken['totalElements']} taken: " + "; ".join(t["titel"] for t in taken["content"])


@rook("nlportal", "berichten van burger A (Open Object)", vereist=("openobject",))
def _(ctx):
    b = gql_ok(np_token(ctx, "A"), Q_BERICHTEN)["getBerichten"]
    eis(b["totalElements"] >= 1, "geen berichten")
    return f"{b['totalElements']} bericht(en): " + "; ".join(x["onderwerp"] for x in b["content"])


@rook("nlportal", "GZAC-portaaltaak zichtbaar als taak in NL Portal", vereist=("gzac", "openobject"))
def _(ctx):
    taken = gql_ok(np_token(ctx, "D"), Q_TAKEN)["getTakenV2"]["content"]
    eis(any("Kenteken" in t["titel"] for t in taken),
        "de portaaltaak van GZAC (taak v1, objecttype Portaaltaak) staat niet in NL Portal, dat alleen taak v2 leest")
    return "portaaltaak zichtbaar"


@rook("nlportal", "frontend levert de configuratie voor DigiD (client nlportal)")
def _(ctx):
    r = requests.get(f"{NLPORTAL}/config.js", timeout=30)
    eis(r.status_code == 200, f"config.js gaf {r.status_code}")
    eis("nlportal" in r.text and "voorbeeldstad" in r.text, "config.js noemt client of realm niet")
    r = requests.get(f"{NLPORTAL}/zaken", timeout=30)
    eis(r.status_code == 200 and "<div id=\"root\"" in r.text, f"SPA-route /zaken gaf {r.status_code}")
    return "config.js en SPA-routes"


@isolatietype("nlportal")
def _nlportal(ctx: Context, kanaal: dict):
    kid = kanaal["id"]
    g = {}

    def b_heeft_data():
        tb = np_token(ctx, "B")
        g["zaken"] = gql_ok(tb, Q_ZAKEN)["getZaken"]["content"]
        g["taken"] = gql_ok(tb, Q_TAKEN)["getTakenV2"]["content"]
        g["berichten"] = gql_ok(tb, Q_BERICHTEN)["getBerichten"]["content"]
        g["docs"] = [d["identificatie"] for z in g["zaken"] for d in z["documenten"]]
        eis(g["zaken"] and g["taken"] and g["berichten"] and g["docs"],
            f"B mist data om mee te testen: {len(g['zaken'])} zaken, {len(g['taken'])} taken, "
            f"{len(g['berichten'])} berichten, {len(g['docs'])} documenten")
        return (f"B ziet {len(g['zaken'])} zaken, {len(g['taken'])} taak, {len(g['berichten'])} bericht, "
                f"{len(g['docs'])} documenten")

    def lijsten_a():
        ta = np_token(ctx, "A")
        lek = []
        zaken = {z["uuid"] for z in gql_ok(ta, Q_ZAKEN)["getZaken"]["content"]}
        lek += [z["identificatie"] for z in g["zaken"] if z["uuid"] in zaken]
        taken = {t["id"] for t in gql_ok(ta, Q_TAKEN)["getTakenV2"]["content"]}
        lek += [t["titel"] for t in g["taken"] if t["id"] in taken]
        berichten = {b["id"] for b in gql_ok(ta, Q_BERICHTEN)["getBerichten"]["content"]}
        lek += [b["onderwerp"] for b in g["berichten"] if b["id"] in berichten]
        eis(not lek, f"A ziet gegevens van B: {lek}")
        return f"zaken, taken en berichten van A bevatten niets van B ({len(zaken)}/{len(taken)}/{len(berichten)})"

    def filter_op_zaaknummer_b():
        nummer = g["zaken"][0]["identificatie"]
        status, data, fouten = gql(np_token(ctx, "A"), "query($n: String) { getZaken(identificatie: $n) "
                                   "{ content { identificatie } } }", n=nummer)
        gevonden = (data or {}).get("getZaken") or {"content": []}
        eis(not gevonden["content"], f"A vindt zaak {nummer} van B via het filter identificatie")
        return f"filter op {nummer}: niets ({status}{', fout' if fouten else ''})"

    def detail(query, veld, id_, wat):
        status, data, fouten = gql(np_token(ctx, "A"), query, id=id_)
        waarde = (data or {}).get(veld)
        eis(not waarde, f"A krijgt {wat} van B: {str(waarde)[:150]}")
        return f"{wat} van B: {'fout ' + str(fouten)[:80] if fouten else 'leeg'} (HTTP {status})"

    def zaak_b():
        return detail("query($id: UUID!) { getZaak(id: $id) { identificatie } }", "getZaak", g["zaken"][0]["uuid"], "zaak")

    def taak_b():
        return detail("query($id: UUID!) { getTaakByIdV2(id: $id) { id titel } }", "getTaakByIdV2", g["taken"][0]["id"], "taak")

    def bericht_b():
        return detail("query($id: UUID!) { getBericht(id: $id) { id onderwerp } }", "getBericht",
                      g["berichten"][0]["id"], "bericht")

    def document_b():
        r = requests.get(f"{NLPORTAL_API}/api/zakenapi/zaakdocument/{g['docs'][0]}/content",
                         headers={"Authorization": f"Bearer {np_token(ctx, 'A')}"}, timeout=60)
        eis(r.status_code in (401, 403, 404), f"A krijgt {r.status_code} op een document van B")
        return f"{r.status_code} op een document van B"

    def zonder_token():
        # GraphQL antwoordt met HTTP 200 en een fout per veld ("No Authentication"), zonder data
        status, data, fouten = gql(None, Q_ZAKEN)
        eis(status == 401 or (status == 200 and not (data or {}).get("getZaken") and fouten),
            f"{status} zonder token met data: {str(data)[:150]}")
        r = requests.get(f"{NLPORTAL_API}/api/zakenapi/zaakdocument/{g['docs'][0]}/content", timeout=30)
        eis(r.status_code == 401, f"document zonder token gaf {r.status_code}")
        return "GraphQL: " + (str(status) if status != 200 else f"geen data, fout '{fouten[0]['message']}'") + \
            f"; document: {r.status_code}"

    def medewerkerstoken():
        r = requests.post(f"{KEYCLOAK}/realms/g4/protocol/openid-connect/token", timeout=30, data={
            "grant_type": "password", "client_id": "valtimo-console", "username": "behandelaar.bakker",
            "password": env("MEDEWERKER_WACHTWOORD"), "scope": "openid"})
        eis(r.status_code == 200, f"token medewerker gaf {r.status_code}")
        status, data, _ = gql(r.json()["access_token"], Q_ZAKEN)
        eis(status == 401, f"{status} met een token uit realm g4, verwacht 401")
        return "401 met een medewerkerstoken (andere issuer)"

    for sub, naam, fn in (
        ("b-heeft-data", "burger B heeft eigen data (voorwaarde)", b_heeft_data),
        ("lijst", "zaken, taken en berichten van A bevatten niets van B", lijsten_a),
        ("filter-zaaknummer-van-b", "A kan niet op het zaaknummer van B filteren", filter_op_zaaknummer_b),
        ("detail", "A kan de zaak van B niet openen", zaak_b),
        ("taak", "A kan de taak van B niet openen", taak_b),
        ("bericht", "A kan het bericht van B niet openen", bericht_b),
        ("document", "A kan een document van B niet downloaden", document_b),
        ("zonder-token", "zonder token geen gegevens", zonder_token),
        ("medewerkerstoken", "token van een medewerker (realm g4) geeft geen burgergegevens", medewerkerstoken),
    ):
        ctx.voer_uit(f"{ISO}/{kid}/{sub}", ISO, kid, naam, fn)


# ------------------------------------------------------------------ GZAC
def medewerker_token(gebruiker, client="valtimo-console", secret=None):
    data = {"grant_type": "password", "client_id": client, "username": gebruiker,
            "password": env("MEDEWERKER_WACHTWOORD"), "scope": "openid"}
    if secret:
        data["client_secret"] = secret
    r = requests.post(f"{KEYCLOAK}/realms/g4/protocol/openid-connect/token", data=data, timeout=30)
    eis(r.status_code == 200, f"token voor {gebruiker} ({client}) gaf {r.status_code}")
    return r.json()["access_token"]


def gzac(methode, pad, token, **kw):
    return requests.request(methode, GZAC_API + pad, headers={"Authorization": f"Bearer {token}"}, timeout=60, **kw)


def gzac_zaak():
    oz = zgw_client(OPENZAAK, "gzac", env("ZGW_GZAC_SECRET"), "Open Zaak (gzac)")
    zaken = oz.lijst("zaken/api/v1/zaken", rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=BURGER_D)
    zaak = next((z for z in zaken if not z["identificatie"].startswith("VBS-")), None)
    eis(zaak, "geen zaak uit GZAC voor burger D (seed gedraaid?)")
    return oz, zaak


@rook("gzac", "medewerker logt in en ziet de zaakdefinitie parkeervergunning", vereist=("keycloak",))
def _(ctx):
    t = medewerker_token("behandelaar.bakker")
    r = gzac("GET", "/api/v1/document-definition", t)
    eis(r.status_code == 200, f"document-definition gaf {r.status_code}")
    namen = [d["id"]["name"] for d in r.json()["content"]]
    eis("parkeervergunning" in namen, f"geen parkeervergunning in {namen}")
    r = gzac("POST", "/api/v1/case/parkeervergunning/search?page=0&size=10", t, json={})
    eis(r.status_code == 200 and r.json()["totalElements"] >= 1, f"dossierlijst gaf {r.status_code}")
    return f"definities {namen}; {r.json()['totalElements']} dossier(s) parkeervergunning"


@rook("gzac", "aanvraag uit GZAC staat als zaak in Open Zaak (initiator, statussen)", vereist=("openzaak",))
def _(ctx):
    oz, zaak = gzac_zaak()
    rollen = oz.lijst("zaken/api/v1/rollen", zaak=zaak["url"])
    eis(any(r["omschrijvingGeneriek"] == "initiator" and r["betrokkeneIdentificatie"].get("inpBsn") == BURGER_D
            for r in rollen), "geen initiator met het BSN van burger D")
    statussen = oz.lijst("zaken/api/v1/statussen", zaak=zaak["url"])
    eis(len(statussen) >= 2, f"{len(statussen)} statussen, verwacht Ontvangen en In behandeling")
    return f"{zaak['identificatie']}: initiator {BURGER_D}, {len(statussen)} statussen"


@rook("gzac", "taak 'Aanvraag beoordelen' in de werkvoorraad van de behandelaar")
def _(ctx):
    r = gzac("GET", "/api/v2/task?filter=all&page=0&size=50", medewerker_token("behandelaar.bakker"))
    eis(r.status_code == 200, f"/api/v2/task gaf {r.status_code}")
    taken = [t["name"] for t in r.json()["content"]]
    eis("Aanvraag beoordelen" in taken, f"taken: {taken}")
    return f"{len(taken)} open taak/taken: {', '.join(sorted(set(taken)))}"


@rook("gzac", "portaaltaak voor burger D in Open Object (Portaaltaak v1)", vereist=("openobject",))
def _(ctx):
    oo = open_object("OPENOBJECT_GZAC_TOKEN")
    objecten = oo.lijst("objects", type=objecttype_url(OBJECTTYPE_PORTAALTAAK))
    eigen = [o["record"]["data"] for o in objecten
             if (o["record"]["data"].get("identificatie") or {}).get("value") == BURGER_D]
    eis(eigen, "geen portaaltaak voor burger D")
    return f"{len(eigen)} portaaltaak: {eigen[0].get('title')} (status {eigen[0].get('status')})"


@rook("gzac", "zonder token geen dossiers; frontend bereikbaar")
def _(ctx):
    r = requests.post(f"{GZAC_API}/api/v1/case/parkeervergunning/search?page=0&size=10", json={}, timeout=30)
    eis(r.status_code in (401, 403), f"{r.status_code} zonder token")
    f = requests.get(f"{GZAC}/", timeout=30)
    eis(f.status_code == 200 and "<app-root" in f.text, f"frontend gaf {f.status_code}")
    return f"{r.status_code} zonder token; frontend 200"


# ------------------------------------------------------------------ IKO
@rook("iko", "profiel zaken-van-burger met medewerkerstoken", vereist=("keycloak", "openzaak"))
def _(ctx):
    t = medewerker_token("behandelaar.bakker", client="iko", secret=env("KEYCLOAK_IKO_SECRET"))
    r = requests.get(f"{IKO}/aggregated-data-profiles/zaken-van-burger", params={"id": ctx.burger("A")},
                     headers={"Authorization": f"Bearer {t}"}, timeout=90)
    eis(r.status_code == 200, f"profiel gaf {r.status_code}: {r.text[:200]}")
    nummers = {z["identificatie"] for z in r.json()["zaken"]}
    eis(VERWACHTE_ZAKEN_A <= nummers, f"mis {sorted(VERWACHTE_ZAKEN_A - nummers)}")
    eis(not nummers & {"VBS-2026-000103", "VBS-2026-000104"}, "zaken van burger B in het klantbeeld van A")
    return f"{r.json()['aantal']} zaken voor {ctx.burger('A')}: {', '.join(sorted(nummers))}"


@rook("iko", "API weigert zonder token, met een burgertoken en zonder rol ROLE_KLANTBEELD")
def _(ctx):
    url = f"{IKO}/aggregated-data-profiles/zaken-van-burger"
    params = {"id": ctx.burger("A")}
    r0 = requests.get(url, params=params, timeout=30)
    eis(r0.status_code == 401, f"{r0.status_code} zonder token")
    burger = np_token(ctx, "A")  # andere realm (DigiD-simulatie)
    r1 = requests.get(url, params=params, headers={"Authorization": f"Bearer {burger}"}, timeout=30)
    eis(r1.status_code == 401, f"{r1.status_code} met een burgertoken")
    # serviceaccount van GZAC: geldig token uit realm g4, maar zonder IKO-rollen
    r = requests.post(f"{KEYCLOAK}/realms/g4/protocol/openid-connect/token", timeout=30, data={
        "grant_type": "client_credentials", "client_id": "valtimo-user-m2m-client",
        "client_secret": env("KEYCLOAK_GZAC_M2M_SECRET")})
    eis(r.status_code == 200, f"token serviceaccount gaf {r.status_code}")
    r2 = requests.get(url, params=params, headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)
    eis(r2.status_code in (401, 403), f"{r2.status_code} zonder rol ROLE_KLANTBEELD")
    return f"{r0.status_code} zonder token, {r1.status_code} met burgertoken, {r2.status_code} zonder rol"


@rook("iko", "beheer-UI vraagt een login bij Keycloak (realm g4)")
def _(ctx):
    r = requests.get(f"{IKO}/admin", allow_redirects=False, timeout=30)
    eis(r.status_code in (302, 303), f"/admin gaf {r.status_code}")
    r = requests.get(urllib.parse.urljoin(f"{IKO}/admin", r.headers["Location"]), allow_redirects=False, timeout=30)
    eis(r.status_code in (302, 303) and "/realms/g4/" in r.headers.get("Location", ""),
        f"geen doorverwijzing naar realm g4: {r.headers.get('Location', '')[:100]}")
    h = requests.get(f"{IKO_BEHEER}/actuator/health", timeout=30).json()
    return f"redirect naar Keycloak realm g4; health {h.get('status')}"
