"""Stack-specifieke tests van stack "maykin" (geladen door tests/run.py).

Rooktests voor Open VTB, Open Formulieren, Open Inwoner en de BRP-vertaler, en de
isolatietypes "openinwoner" en "openformulieren": burger A logt in via de
DigiD-simulatie (Keycloak) en probeert gegevens van burger B te zien.

Inloggen gebeurt zoals een browser het doet (authorization code flow), maar vanuit de
tools-container. De browser-adressen (localhost:<poort>) herschrijven we daarom naar de
interne namen; de Keycloak-clients staan beide als redirect-URI toe.
"""
import html
import os
import re
import time
import urllib.parse

import requests

from checks.isolatie import CAT as ISO, isolatietype
from checks.rook import rook
from kader import Context, eis

KEYCLOAK_PUBLIEK = "http://localhost:8080"
OPENVTB = "http://openvtb.local:8000"
OPENFORMULIEREN = "http://openformulieren.local:8000"
OPENINWONER = "http://openinwoner.local:8000"
BRP_API = "http://brp-api.local:8080"
FORMULIER = "melding-openbare-ruimte"

HERSCHRIJF = {
    KEYCLOAK_PUBLIEK: "http://keycloak.local:8080",
    f"http://localhost:{os.environ.get('PORT_OPENFORMULIEREN', '8102')}": OPENFORMULIEREN,
    f"http://localhost:{os.environ.get('PORT_OPENINWONER', '8103')}": OPENINWONER,
}
# Testburger voor de volledige inzending in Open Formulieren: maakt bij elke testrun een
# nieuwe zaak aan, en zit daarom niet in de vaste verwachtingen voor A, B en C.
BURGER_MELDER = "999995406"


def intern(url):
    for publiek, binnen in HERSCHRIJF.items():
        if url.startswith(publiek):
            return binnen + url[len(publiek):]
    return url


def tekst(r):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def volg(s, url, max_stappen=15):
    """Volgt redirects zelf, met herschrijven van browser-adressen naar interne namen."""
    r = None
    for _ in range(max_stappen):
        r = s.get(intern(url), allow_redirects=False, timeout=60)
        if r.status_code in (301, 302, 303, 307) and r.headers.get("Location"):
            url = urllib.parse.urljoin(r.url, r.headers["Location"])
            continue
        return r
    raise AssertionError(f"te veel redirects vanaf {url}")


def digid_login(start_url, bsn):
    """Logt in via de DigiD-simulatie; geeft (sessie, laatste antwoord)."""
    s = requests.Session()
    r = volg(s, start_url)
    m = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', r.text)
    eis(m, f"geen Keycloak-loginformulier na {start_url} (status {r.status_code}, {r.url})")
    r = s.post(intern(html.unescape(m.group(1))), allow_redirects=False, timeout=60,
               data={"username": bsn, "password": os.environ["DIGID_SIM_WACHTWOORD"], "credentialId": ""})
    eis(r.status_code in (302, 303), f"Keycloak weigert de login van {bsn} ({r.status_code})")
    return s, volg(s, urllib.parse.urljoin(r.url, r.headers["Location"]))


# ------------------------------------------------------------------ Open Inwoner
def oip_login(bsn):
    s, r = digid_login(f"{OPENINWONER}/digid-oidc/authenticate/?next=/", bsn)
    if "/register/necessary" in r.url:
        # Eerste login: Open Inwoner vraagt om een e-mailadres (naam komt uit de BRP)
        velden = dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', r.text))
        csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)
        r = s.post(r.url, headers={"Referer": r.url}, timeout=60, data={
            "csrfmiddlewaretoken": csrf, "first_name": velden.get("first_name", ""),
            "last_name": velden.get("last_name", ""), "email": f"{bsn}@inwoner.voorbeeldstad.example",
            "cases_notifications": "on"})
    eis(r.status_code == 200 and "/accounts/login" not in r.url, f"login bij Open Inwoner mislukt: {r.url}")
    return s


def oip_zaken(s):
    r = s.get(f"{OPENINWONER}/cases/content/", headers={"HX-Request": "true"}, timeout=90)
    eis(r.status_code == 200, f"/cases/content/ gaf {r.status_code}")
    nummers = sorted(set(re.findall(r"VBS-\d{4}-\d{6}", tekst(r))))
    links = sorted(set(re.findall(r'href="(/cases/[^"]+/status/)"', r.text)))
    return nummers, links


def oip_detail(s, link, **kw):
    """Zaakdetail: de pagina laadt de inhoud met htmx van <link>content/."""
    return s.get(f"{OPENINWONER}{link}content/", headers={"HX-Request": "true"}, timeout=90, **kw)


def oip_documenten(r):
    return sorted(set(re.findall(r'href="(/cases/[^"]+/document/[^"]+)"', r.text)))


def oip_sessie(ctx, letter):
    sessies = ctx.gedeeld.setdefault("oip_sessies", {})
    if letter not in sessies:
        sessies[letter] = oip_login(ctx.burger(letter))
    return sessies[letter]


@rook("openinwoner", "DigiD-login en Mijn aanvragen van burger A", vereist=("keycloak", "openzaak"))
def _(ctx):
    nummers, links = oip_zaken(oip_sessie(ctx, "A"))
    eis(nummers == ["VBS-2026-000101", "VBS-2026-000102"], f"zaken: {nummers}")
    return f"{', '.join(nummers)}; {len(links)} links naar een zaak"


@rook("openinwoner", "zaakdetail met status en documenten", vereist=("openzaak",))
def _(ctx):
    s = oip_sessie(ctx, "A")
    _, links = oip_zaken(s)
    teksten = []
    docs = {}
    for link in links:
        r = oip_detail(s, link)
        eis(r.status_code == 200, f"{link}content/ gaf {r.status_code}")
        teksten.append(tekst(r))
        docs[link] = oip_documenten(r)
    nr = next(i for i, x in enumerate(teksten) if "VBS-2026-000102" in x)
    afgesloten, link = teksten[nr], links[nr]
    eis("Uw melding is afgehandeld" in afgesloten, "zaak VBS-2026-000102 toont de eindstatus niet")
    eis(len(docs[link]) == 2, f"verwacht 2 documenten, kreeg {docs[link]}")
    r = s.get(OPENINWONER + docs[link][0], timeout=90)
    eis(r.status_code == 200 and r.content.startswith(b"%PDF"), f"download gaf {r.status_code}")
    return f"VBS-2026-000102: statushistorie tot 'afgehandeld', 2 documenten, download is een PDF ({len(r.content)} bytes)"


@rook("openinwoner", "Mijn taken uit Open Object (externe taken)", vereist=("openobject",))
def _(ctx):
    t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/", timeout=90))
    eis("Aanvullende tekening dakkapel aanleveren" in t, "taak van A ontbreekt op de homepage")
    return "taken van A op de homepage: " + ", ".join(
        x for x in ("Aanvullende tekening dakkapel aanleveren", "Leges omgevingsvergunning betalen") if x in t)


@rook("openinwoner", "Mijn profiel met BRP-gegevens", vereist=("brp-api",))
def _(ctx):
    t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/profile/mydata/", timeout=90))
    eis("Janssen" in t and "Mandelaplein" in t, "naam of adres van burger A ontbreekt")
    eis("06 april 1975" in t, "geboortedatum ontbreekt (BRP-antwoord niet geldig?)")
    return "Stephan Janssen, Mandelaplein 2, geboren 06 april 1975"


@rook("openinwoner", "Mijn vragen uit Open Klant", vereist=("openklant",))
def _(ctx):
    t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/cases/contactmomenten/", timeout=90))
    eis("grofvuilpas" in t, "vraag van burger A ontbreekt")
    m = re.search(r"Mijn vragen \((\d+)\)", t)
    return f"Mijn vragen ({m.group(1) if m else '?'}): 'Wanneer wordt de grofvuilpas verstuurd?'"


@isolatietype("openinwoner")
def _openinwoner(ctx: Context, kanaal: dict):
    kid = kanaal["id"]
    g = {}

    def b_heeft_data():
        sb = oip_sessie(ctx, "B")
        nummers, links = oip_zaken(sb)
        eis(nummers, "burger B ziet geen zaken in Open Inwoner (seed gedraaid?)")
        g["b_nummers"], g["b_links"] = nummers, links
        g["b_docs"] = []
        for link in links:
            g["b_docs"] += oip_documenten(oip_detail(sb, link))
        thuis = tekst(sb.get(f"{OPENINWONER}/", timeout=90))
        eis("Medische verklaring traplift aanleveren" in thuis, "taak van B ontbreekt bij B zelf")
        vragen = tekst(sb.get(f"{OPENINWONER}/cases/contactmomenten/", timeout=90))
        eis("traplift ook in een huurwoning" in vragen, "vraag van B ontbreekt bij B zelf")
        return (f"B ziet zaken {', '.join(nummers)}, {len(g['b_docs'])} document(en), "
                "een eigen taak en een eigen vraag")

    def lijst():
        nummers, _ = oip_zaken(oip_sessie(ctx, "A"))
        lek = set(nummers) & set(g["b_nummers"])
        eis(not lek, f"A ziet zaken van B: {sorted(lek)}")
        return f"A ziet {', '.join(nummers)}, geen van B"

    def detail():
        s = oip_sessie(ctx, "A")
        uit = []
        for link in g["b_links"]:
            r = oip_detail(s, link, allow_redirects=False)
            lek = [n for n in g["b_nummers"] if n in tekst(r)] if r.status_code == 200 else []
            eis(r.status_code in (302, 403, 404) or (r.status_code == 200 and not lek),
                f"A opent {link} van B: {r.status_code}, zaaknummers {lek}")
            uit.append(str(r.status_code))
        return f"zaken van B via directe URL: {', '.join(uit)}"

    def document():
        eis(g.get("b_docs"), "geen document van B gevonden om mee te testen")
        r = oip_sessie(ctx, "A").get(OPENINWONER + g["b_docs"][0], timeout=90, allow_redirects=False)
        eis(r.status_code in (302, 403, 404) and not r.content.startswith(b"%PDF"),
            f"A krijgt {r.status_code} op een document van B")
        return f"{r.status_code} op een document van B"

    def taken():
        t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/", timeout=90))
        eis("Medische verklaring traplift aanleveren" not in t, "A ziet de taak van B")
        return "taak van B niet zichtbaar (Open Inwoner filtert zelf op BSN, zie README)"

    def vragen():
        t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/cases/contactmomenten/", timeout=90))
        eis("traplift ook in een huurwoning" not in t, "A ziet de vraag van B")
        return "vraag van B niet zichtbaar"

    def profiel():
        t = tekst(oip_sessie(ctx, "A").get(f"{OPENINWONER}/profile/mydata/", timeout=90))
        eis("Crooy" not in t and ctx.burger("B") not in t, "A ziet BRP-gegevens van B")
        return "alleen eigen BRP-gegevens"

    def zonder_login():
        r = requests.get(f"{OPENINWONER}/cases/", timeout=60, allow_redirects=False)
        lek = [n for n in g["b_nummers"] if n in r.text]
        eis(r.status_code in (302, 401, 403) and not lek, f"zonder login: {r.status_code}, {lek}")
        return f"{r.status_code} naar {r.headers.get('Location', '')[:60]}"

    for sub, naam, fn in (
        ("b-heeft-data", "burger B heeft eigen zaken, taak en vraag (voorwaarde)", b_heeft_data),
        ("lijst", "Mijn aanvragen van A bevat geen zaken van B", lijst),
        ("detail", "A kan een zaak van B niet openen via de URL", detail),
        ("document", "A kan een document van B niet downloaden", document),
        ("taken", "Mijn taken van A bevat geen taak van B", taken),
        ("vragen", "Mijn vragen van A bevat geen vraag van B", vragen),
        ("profiel", "Mijn gegevens van A tonen geen BRP-gegevens van B", profiel),
        ("zonder-login", "zonder login geen zaken", zonder_login),
    ):
        ctx.voer_uit(f"{ISO}/{kid}/{sub}", ISO, kid, naam, fn)


# -------------------------------------------------------------- Open Formulieren
def of_login(bsn):
    form = requests.get(f"{OPENFORMULIEREN}/api/v2/forms/{FORMULIER}", timeout=30).json()
    optie = next(o for o in form["loginOptions"] if o["identifier"] == "digid_oidc")
    volgende = urllib.parse.quote(f"http://localhost:{os.environ.get('PORT_OPENFORMULIEREN', '8102')}/{FORMULIER}")
    s, r = digid_login(f"{optie['url']}?next={volgende}", bsn)
    eis(r.status_code == 200, f"terug bij Open Formulieren met {r.status_code} ({r.url})")
    return s, form


def of_api(s, methode, pad, **kw):
    r0 = s.get(f"{OPENFORMULIEREN}/api/v2/forms/{FORMULIER}", timeout=30)
    headers = {"X-CSRFToken": r0.headers.get("X-CSRFToken", ""), "Referer": OPENFORMULIEREN + "/",
               "Content-Type": "application/json"}
    url = pad if pad.startswith("http") else f"{OPENFORMULIEREN}/api/v2/{pad.lstrip('/')}"
    return s.request(methode, intern(url), headers=headers, timeout=60, **kw)


def of_start(s, form):
    r = of_api(s, "POST", "submissions", json={
        "form": form["url"], "formUrl": f"http://localhost:{os.environ.get('PORT_OPENFORMULIEREN', '8102')}/{FORMULIER}"})
    eis(r.status_code == 201, f"inzending starten gaf {r.status_code}: {r.text[:300]}")
    return r.json()


def of_stap(s, inzending):
    r = of_api(s, "GET", inzending["steps"][0]["url"])
    eis(r.status_code == 200, f"stap ophalen gaf {r.status_code}")
    return r.json()


def of_sessie(ctx, letter):
    sessies = ctx.gedeeld.setdefault("of_sessies", {})
    if letter not in sessies:
        s, form = of_login(ctx.burger(letter))
        inzending = of_start(s, form)
        sessies[letter] = (s, form, inzending)
    return sessies[letter]


@rook("openformulieren", "formulier Melding openbare ruimte (DigiD, zaak in Open Zaak)")
def _(ctx):
    form = requests.get(f"{OPENFORMULIEREN}/api/v2/forms/{FORMULIER}", timeout=30).json()
    eis(form["loginRequired"], "formulier vraagt geen login")
    eis([o["identifier"] for o in form["loginOptions"]] == ["digid_oidc"], f"{form['loginOptions']}")
    return f"{form['name']}: {len(form['steps'])} stap(pen), login {form['loginOptions'][0]['label']}"


@rook("openformulieren", "inwoner logt in, BRP-prefill, verstuurt melding: zaak in Open Zaak",
      vereist=("keycloak", "openzaak", "brp-api"))
def _(ctx):
    from checks.rook import open_zaak_beheer  # noqa: PLC0415

    s, form = of_login(BURGER_MELDER)
    inzending = of_start(s, form)
    stap = of_stap(s, inzending)
    prefill = stap["data"]
    eis(prefill.get("achternaam"), f"geen prefill uit de BRP: {prefill}")
    data = {**prefill, "email": f"{BURGER_MELDER}@inwoner.voorbeeldstad.example", "categorie": "verlichting",
            "locatie": "Mandelaplein 2", "omschrijving": "Lantaarnpaal brandt niet (testmelding)."}
    r = of_api(s, "PUT", inzending["steps"][0]["url"], json={"data": data})
    eis(r.status_code in (200, 201), f"stap opslaan gaf {r.status_code}: {r.text[:300]}")
    r = of_api(s, "POST", f"{inzending['url']}/_complete", json={"privacyPolicyAccepted": True,
                                                                  "statementOfTruthAccepted": True})
    eis(r.status_code == 200, f"versturen gaf {r.status_code}: {r.text[:400]}")
    status_url = r.json()["statusUrl"]
    start = time.time()
    while time.time() - start < 120:
        st = of_api(s, "GET", status_url).json()
        if st.get("status") == "done":
            break
        time.sleep(3)
    eis(st.get("result") == "success", f"verwerking: {st}")
    kenmerk = st.get("publicReference")
    oz = open_zaak_beheer()
    zaken = oz.lijst("zaken/api/v1/zaken", rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=BURGER_MELDER)
    zaak = next((z for z in zaken if z["identificatie"] == kenmerk), None)
    eis(zaak, f"geen zaak {kenmerk} met de melder als betrokkene in Open Zaak")
    zaaktype = oz.get(zaak["zaaktype"])
    zios = oz.lijst("zaken/api/v1/zaakinformatieobjecten", zaak=zaak["url"])
    return (f"{prefill.get('voornamen')} {prefill.get('achternaam')} (uit de BRP) > zaak {kenmerk} "
            f"({zaaktype['omschrijving']}), {len(zios)} document(en)")


@isolatietype("openformulieren")
def _openformulieren(ctx: Context, kanaal: dict):
    kid = kanaal["id"]

    def b_heeft_data():
        s, _, inzending = of_sessie(ctx, "B")
        data = of_stap(s, inzending)["data"]
        eis(data.get("achternaam") == "Crooy", f"prefill van B: {data}")
        return f"B heeft inzending {inzending['id'][:8]}..., prefill {data.get('voornamen')} de {data.get('achternaam')}"

    def prefill_a():
        s, _, inzending = of_sessie(ctx, "A")
        data = of_stap(s, inzending)["data"]
        eis(data.get("achternaam") == "Janssen", f"prefill van A: {data}")
        return "A krijgt alleen eigen BRP-gegevens"

    def inzending_van_b():
        s, _, _ = of_sessie(ctx, "A")
        _, _, b = of_sessie(ctx, "B")
        r = of_api(s, "GET", b["url"])
        eis(r.status_code in (403, 404), f"A krijgt {r.status_code} op de inzending van B")
        return f"{r.status_code}"

    def stap_van_b():
        s, _, _ = of_sessie(ctx, "A")
        _, _, b = of_sessie(ctx, "B")
        r = of_api(s, "GET", b["steps"][0]["url"])
        eis(r.status_code in (403, 404) and "Crooy" not in r.text, f"A krijgt {r.status_code} op de stap van B")
        return f"{r.status_code}"

    def zonder_login():
        s = requests.Session()
        form = s.get(f"{OPENFORMULIEREN}/api/v2/forms/{FORMULIER}", timeout=30).json()
        r = of_api(s, "POST", "submissions", json={"form": form["url"], "formUrl": f"http://localhost:{os.environ.get('PORT_OPENFORMULIEREN', '8102')}/{FORMULIER}"})
        if r.status_code == 201:
            stap = of_api(s, "GET", r.json()["steps"][0]["url"])
            eis(stap.status_code in (401, 403), f"zonder login: stap gaf {stap.status_code}")
            return f"inzending mag starten, stap gaf {stap.status_code}"
        eis(r.status_code in (400, 401, 403), f"zonder login: {r.status_code}")
        return f"{r.status_code}"

    for sub, naam, fn in (
        ("b-heeft-data", "burger B heeft een eigen inzending met eigen prefill (voorwaarde)", b_heeft_data),
        ("prefill", "prefill van A bevat alleen gegevens van A", prefill_a),
        ("inzending", "A kan de inzending van B niet ophalen", inzending_van_b),
        ("stap", "A kan de stapgegevens van B niet ophalen", stap_van_b),
        ("zonder-login", "zonder DigiD-login geen inzending", zonder_login),
    ):
        ctx.voer_uit(f"{ISO}/{kid}/{sub}", ISO, kid, naam, fn)


# ------------------------------------------------------------------ Open VTB
def vtb(token_var="OPENVTB_BEHEER_TOKEN"):
    return {"Authorization": f"Token {os.environ[token_var]}"}


@rook("openvtb", "taken van burger A (Taken API, filter isToegewezenAan)")
def _(ctx):
    r = requests.get(f"{OPENVTB}/taken/api/v1/externetaken", headers=vtb(), timeout=30,
                     params={"isToegewezenAan": f"urn:nld:brp:bsn:{ctx.burger('A')}"})
    eis(r.status_code == 200, f"{r.status_code}")
    titels = sorted(t["titel"] for t in r.json()["results"])
    eis(len(titels) == 3, f"verwacht 3 taken, kreeg {titels}")
    soorten = sorted(t["taakSoort"] for t in r.json()["results"])
    return f"{len(titels)} taken ({', '.join(soorten)})"


@rook("openvtb", "filter matcht een URN-segment: alleen het BSN vindt ook de taken")
def _(ctx):
    # Open VTB 0.2 filtert op een volledig segment van de URN. Een afnemer die alleen op
    # het BSN filtert, krijgt ook taken van een bedrijf met hetzelfde nummer; een afnemer
    # moet de volledige URN daarom zelf nog eens controleren.
    r = requests.get(f"{OPENVTB}/taken/api/v1/externetaken", headers=vtb(), timeout=30,
                     params={"isToegewezenAan": ctx.burger("A")})
    eis(r.status_code == 200, f"{r.status_code}")
    return f"isToegewezenAan={ctx.burger('A')} geeft {r.json()['count']} taken (segment-match, gedocumenteerd gedrag)"


@rook("openvtb", "zonder token geen taken; token burgerportaal mag lezen")
def _(ctx):
    r = requests.get(f"{OPENVTB}/taken/api/v1/externetaken", timeout=30)
    eis(r.status_code in (401, 403), f"zonder token: {r.status_code}")
    r2 = requests.get(f"{OPENVTB}/taken/api/v1/externetaken", headers=vtb("OPENVTB_PORTAAL_TOKEN"), timeout=30)
    eis(r2.status_code == 200, f"token burgerportaal: {r2.status_code}")
    return f"zonder token {r.status_code}; token burgerportaal ziet {r2.json()['count']} taken (alle inwoners)"


# ---------------------------------------------------------------- BRP-vertaler
@rook("brp-api", "BRP API Personen 2 in officieel formaat")
def _(ctx):
    r = requests.post(f"{BRP_API}/haalcentraal/api/brp/personen", timeout=30, json={
        "type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": [ctx.burger("A")],
        "fields": ["naam", "geboorte", "verblijfplaats"]})
    eis(r.status_code == 200, f"{r.status_code}")
    p = r.json()["personen"][0]
    eis(p["geboorte"]["datum"].get("datum") == "1975-04-06", f"geboorte: {p['geboorte']}")
    eis(p["verblijfplaats"]["verblijfadres"]["officieleStraatnaam"] == "Mandelaplein", "verblijfadres ontbreekt")
    return "geboorte.datum als Datum-object, verblijfplaats.verblijfadres genest"
