"""Stack-specifieke tests van stack "dimpact" (geladen door tests/run.py).

1. De tests van stack maykin voor wat PodiumD met het Maykin-landschap deelt: Open
   Inwoner, Open Formulieren en de BRP-vertaler, met de isolatietypes "openinwoner" en
   "openformulieren" (burger A probeert gegevens van burger B te zien). Open VTB draait
   PodiumD niet; die tests vallen weg.
2. Rooktests voor de PodiumD-componenten: Objecttypen API, KISS, ITA, PABC, Open
   Archiefbeheer, Open Beheer, NotifyNL OMC, ClamAV en Mailpit.

Medewerkers loggen in zoals een browser dat doet (authorization code flow tegen realm
"podiumd"), maar vanuit de tools-container. De browser-adressen (localhost:<poort>)
herschrijven we naar de interne namen en sturen de oorspronkelijke Host mee, zodat de
app dezelfde redirect-URI opbouwt als voor een echte browser.
"""
import html
import importlib.util
import json
import os
import re
import smtplib
import socket
import struct
import time
import urllib.parse
from email.message import EmailMessage

import jwt
import requests

from checks.rook import REGISTER, open_zaak_beheer, rook
from kader import ROOT, eis

# ------------------------------------------------- tests van stack maykin
_spec = importlib.util.spec_from_file_location("stack_tests_maykin_via_dimpact", ROOT / "stacks" / "maykin" / "tests.py")
MAYKIN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MAYKIN)
REGISTER[:] = [t for t in REGISTER if t["component"] != "openvtb"]


def poort(naam, standaard):
    return os.environ.get(f"PORT_{naam}", str(standaard))


KISS = f"http://localhost:{poort('KISS', 8156)}"
ITA = f"http://localhost:{poort('ITA', 8157)}"
OAB = f"http://localhost:{poort('OPENARCHIEFBEHEER', 8154)}"
KEYCLOAK_PUBLIEK = f"http://localhost:{poort('KEYCLOAK', 8080)}"
INTERN = {
    KISS: "http://kiss.local:8080",
    ITA: "http://ita.local:8080",
    OAB: "http://openarchiefbeheer.local:8000",
    KEYCLOAK_PUBLIEK: "http://keycloak.local:8080",
}
OPENBEHEER = "http://openbeheer.local:8000"
OPENARCHIEFBEHEER = "http://openarchiefbeheer.local:8000"
PABC = "http://pabc.local:8080"
OMC = "http://omc.local:8080"
NOTIFY_MOCK = "http://notify-mock.local:8080"
OBJECTTYPEN = "http://objecttypen.local:8000"
OBJECTEN = "http://objecten.local:8000"
MAILPIT = "http://mailpit.local:8025"
OPENKLANT_REGISTER = "http://openklant.local:8000/klantinteracties/api/v1"

OT = {
    "a1": "Melding", "a2": "Parkeervergunning", "b1": "Externe taak", "c1": "Afdeling", "c2": "Groep",
    "c3": "Medewerker", "c4": "Activiteitenlog",
}
OT_UUID = "7c1d4a0e-5a7b-4c1e-8f00-0000000000{}"

# Het officiele EICAR-testbestand (geen virus; elke virusscanner herkent het)
EICAR = (r"X5O!P%@AP[4\PZX54(P^)7CC)7}$" + "EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*").encode()


# ------------------------------------------------------------ hulpfuncties
def _browser(s, methode, url, headers=None, **kw):
    """Verzoek zoals een browser: intern adres, oorspronkelijke Host, navigatie-headers."""
    for publiek, binnen in INTERN.items():
        if url.startswith(publiek):
            headers = {"Host": urllib.parse.urlsplit(publiek).netloc, **(headers or {})}
            url = binnen + url[len(publiek):]
            break
    h = {"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document", **(headers or {})}
    r = s.request(methode, url, headers=h, allow_redirects=False, timeout=60, **kw)
    # .NET zet de correlatie- en sessiecookies met Secure; een browser stuurt die naar
    # http://localhost toch mee (localhost geldt als veilige context), requests niet.
    for c in s.cookies:
        c.secure = False
    return r


def _api(s, methode, url, **kw):
    """Verzoek zoals de frontend het doet (fetch, geen navigatie)."""
    headers = {"Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Accept": "application/json",
               **kw.pop("headers", {})}
    return _browser(s, methode, url, headers=headers, **kw)


def medewerker_login(start_url, gebruiker):
    """Authorization code flow tegen realm podiumd; geeft de sessie bij de app terug."""
    s = requests.Session()
    url, methode, data = start_url, "GET", None
    for _ in range(20):
        r = _browser(s, methode, url, data=data)
        methode, data = "GET", None
        if r.status_code in (301, 302, 303, 307):
            url = urllib.parse.urljoin(url, r.headers["Location"])
            continue
        m = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', r.text)
        if m:
            url, methode = html.unescape(m.group(1)), "POST"
            data = {"username": gebruiker, "password": os.environ["MEDEWERKER_WACHTWOORD"], "credentialId": ""}
            continue
        # response_mode=form_post: Keycloak geeft een formulier dat de browser zelf verstuurt
        m = re.search(r'<form[^>]*method="post"[^>]*action="([^"]+)"', r.text, re.I)
        if m and "keycloak" not in m.group(1) and "/realms/" not in m.group(1):
            url, methode = html.unescape(m.group(1)), "POST"
            data = {k: html.unescape(v) for k, v in
                    re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', r.text, re.I)}
            continue
        eis(r.status_code == 200, f"login van {gebruiker} eindigt met {r.status_code} op {url}")
        return s
    raise AssertionError(f"te veel stappen bij de login van {gebruiker}")


def sessie(ctx, app, gebruiker):
    sessies = ctx.gedeeld.setdefault("medewerkers", {})
    if (app, gebruiker) not in sessies:
        sessies[(app, gebruiker)] = medewerker_login(f"{app}/api/challenge?returnUrl=/", gebruiker)
    return sessies[(app, gebruiker)]


def django_api_login(basis, gebruiker=None, wachtwoord=None):
    """Login op de API van Open Archiefbeheer of Open Beheer (sessie + CSRF)."""
    s = requests.Session()
    s.get(f"{basis}/api/v1/auth/ensure-csrf-token/", timeout=30)
    if not s.cookies.get("csrftoken"):
        s.get(f"{basis}/admin/login/", timeout=30)
    r = s.post(f"{basis}/api/v1/auth/login/", timeout=30,
               json={"username": gebruiker or os.environ["ADMIN_USERNAME"],
                     "password": wachtwoord or os.environ["ADMIN_PASSWORD"]},
               headers={"X-CSRFToken": s.cookies.get("csrftoken", ""), "Referer": basis + "/"})
    eis(r.status_code in (200, 204), f"login op {basis} gaf {r.status_code}: {r.text[:200]}")
    return s


# ------------------------------------------------------- Objecttypen API
@rook("objecttypen", "PodiumD-objecttypen met vaste UUID's (Melding tot en met Activiteitenlog)")
def _(ctx):
    h = {"Authorization": f"Token {os.environ['OPENOBJECT_BEHEER_TOKEN']}"}
    r = requests.get(f"{OBJECTTYPEN}/api/v2/objecttypes", headers=h, timeout=30, params={"pageSize": 100})
    eis(r.status_code == 200, f"{r.status_code}")
    data = r.json()
    rijen = data["results"] if isinstance(data, dict) else data
    namen = {o["uuid"]: o["name"] for o in rijen}
    ontbreekt = [n for k, n in OT.items() if OT_UUID.format(k) not in namen]
    eis(not ontbreekt, f"ontbrekende objecttypen: {ontbreekt}")
    zonder = requests.get(f"{OBJECTTYPEN}/api/v2/objecttypes", timeout=30)
    eis(zonder.status_code in (401, 403), f"zonder token: {zonder.status_code}")
    return f"{len(OT)} objecttypen aanwezig; zonder token {zonder.status_code}"


@rook("openobject", "afdelingen, groepen en medewerkers van Voorbeeldstad (Objecten API)",
      vereist=("objecttypen",))
def _(ctx):
    h = {"Authorization": f"Token {os.environ['OBJECTEN_PODIUMD_TOKEN']}"}
    tellingen = {}
    for k in ("c1", "c2", "c3"):
        r = requests.get(f"{OBJECTEN}/api/v2/objects", headers=h, timeout=30,
                         params={"type": f"{OBJECTTYPEN}/api/v2/objecttypes/{OT_UUID.format(k)}"})
        eis(r.status_code == 200, f"{OT[k]}: {r.status_code}")
        tellingen[OT[k]] = r.json()["count"]
    eis(tellingen == {"Afdeling": 3, "Groep": 2, "Medewerker": 3}, f"{tellingen}")
    return ", ".join(f"{v} {k.lower()}" for k, v in tellingen.items())


# ---------------------------------------------------------------- KISS
def kiss(ctx, gebruiker="kcm.jansen"):
    return sessie(ctx, KISS, gebruiker)


def kiss_get(ctx, pad, **kw):
    return _api(kiss(ctx), "GET", f"{KISS}{pad}", headers={"systemIdentifier": OPENKLANT_REGISTER}, **kw)


@rook("kiss", "klantcontactmedewerker logt in via Keycloak (realm podiumd)", vereist=("keycloak",))
def _(ctx):
    me = _api(kiss(ctx), "GET", f"{KISS}/api/me").json()
    eis(me.get("isLoggedIn") and me.get("isKcm"), f"/api/me: {me}")
    return f"ingelogd, rol klantcontactmedewerker, rechten: {', '.join(me.get('permissions', [])[:4])}, ..."


@rook("kiss", "afdelingen en groepen uit de Objecten API", vereist=("openobject", "objecttypen"))
def _(ctx):
    afd = kiss_get(ctx, "/api/afdelingen/api/v2/objects")
    grp = kiss_get(ctx, "/api/groepen/api/v2/objects")
    eis(afd.status_code == 200 and grp.status_code == 200, f"{afd.status_code}, {grp.status_code}")
    namen = sorted(o["record"]["data"]["naam"] for o in afd.json()["results"])
    eis("Klantcontactcentrum" in namen, f"afdelingen: {namen}")
    return f"{afd.json()['count']} afdelingen ({', '.join(namen)}), {grp.json()['count']} groepen"


@rook("kiss", "zaak opzoeken in Open Zaak", vereist=("openzaak",))
def _(ctx):
    r = kiss_get(ctx, "/api/zaken/zaken?identificatie=VBS-2026-000101")
    eis(r.status_code == 200 and r.json()["count"] == 1, f"{r.status_code}: {r.text[:200]}")
    return f"VBS-2026-000101: {r.json()['results'][0]['omschrijving']}"


@rook("kiss", "contactverzoek opzoeken in Open Klant", vereist=("openklant",))
def _(ctx):
    r = kiss_get(ctx, "/api/klantinteracties/klantcontacten?nummer=8000000001")
    eis(r.status_code == 200 and r.json()["count"] == 1, f"{r.status_code}: {r.text[:200]}")
    return f"klantcontact 8000000001: {r.json()['results'][0]['onderwerp']}"


@rook("kiss", "persoon zoeken in de BRP", vereist=("brp-api",))
def _(ctx):
    # KISS stuurt de body opnieuw geserialiseerd door met de oude Content-Length; compacte
    # JSON (zoals de browser die stuurt) komt goed aan, JSON met spaties niet (zie README).
    body = json.dumps({"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": [ctx.burger("A")],
                       "fields": ["naam"]}, separators=(",", ":"))
    r = _api(kiss(ctx), "POST", f"{KISS}/api/haalcentraal/brp/personen", data=body,
             headers={"Content-Type": "application/json"})
    eis(r.status_code == 200, f"{r.status_code}: {r.text[:200]}")
    naam = r.json()["personen"][0]["naam"]
    return f"{naam.get('voornamen')} {naam.get('geslachtsnaam')}"


@rook("kiss", "zonder login geen zaken en geen klantcontacten")
def _(ctx):
    s = requests.Session()
    uit = []
    for pad in ("/api/zaken/zaken?identificatie=VBS-2026-000101", "/api/klantinteracties/klantcontacten"):
        r = _api(s, "GET", f"{KISS}{pad}", headers={"systemIdentifier": OPENKLANT_REGISTER})
        naar_login = r.status_code == 302 and "/realms/podiumd/" in r.headers.get("Location", "")
        eis(r.status_code in (401, 403) or naar_login, f"{pad}: {r.status_code} {r.headers.get('Location', '')[:80]}")
        eis("VBS-2026" not in r.text and "klantcontact" not in r.text.lower(), f"{pad}: gegevens zonder login")
        uit.append("302 naar Keycloak" if naar_login else str(r.status_code))
    return ", ".join(uit)


# ----------------------------------------------------------------- ITA
def ita_taken(ctx, gebruiker):
    r = _api(sessie(ctx, ITA, gebruiker), "GET", f"{ITA}/api/internetaken/aan-mij-toegewezen?afgerond=false")
    eis(r.status_code == 200, f"werkvoorraad van {gebruiker}: {r.status_code}")
    return sorted(t["nummer"] for t in r.json())


def ita_detail(ctx, gebruiker, nummer):
    return _api(sessie(ctx, ITA, gebruiker), "GET", f"{ITA}/api/internetaken/{nummer}")


@rook("ita", "werkvoorraad per medewerker (contactverzoeken uit Open Klant)", vereist=("keycloak", "openklant"))
def _(ctx):
    desai, jansen = ita_taken(ctx, "behandelaar.desai"), ita_taken(ctx, "kcm.jansen")
    eis(desai == ["8000000001"], f"Desai: {desai}")
    eis(jansen == ["8000000002"], f"Jansen: {jansen}")
    return f"Desai ziet {desai}, Jansen ziet {jansen}"


@rook("ita", "medewerker opent eigen taak, niet die van een andere afdeling", vereist=("openobject",))
def _(ctx):
    eigen = ita_detail(ctx, "behandelaar.desai", "8000000001")
    ander = ita_detail(ctx, "behandelaar.desai", "8000000002")
    eis(eigen.status_code == 200, f"eigen taak: {eigen.status_code}")
    eis(ander.status_code == 403 and "De Crooy" not in ander.text, f"taak van KCC: {ander.status_code}")
    return f"eigen taak 200 ({eigen.json()['aanleidinggevendKlantcontact']['onderwerp']}), taak van KCC {ander.status_code}"


@rook("ita", "functioneel beheerder ziet alle taken; zonder login 401")
def _(ctx):
    codes = [ita_detail(ctx, "beheer.devries", n).status_code for n in ("8000000001", "8000000002")]
    eis(codes == [200, 200], f"beheerder: {codes}")
    anoniem = _api(requests.Session(), "GET", f"{ITA}/api/internetaken/aan-mij-toegewezen?afgerond=false")
    eis(anoniem.status_code == 401, f"zonder login: {anoniem.status_code}")
    return f"beheerder {codes}; zonder login {anoniem.status_code}"


# ---------------------------------------------------------------- PABC
@rook("pabc", "applicatierollen per zaaktype voor een functionele rol")
def _(ctx):
    h = {"X-API-KEY": os.environ["PABC_API_KEY"]}
    r = requests.post(f"{PABC}/api/v1/application-roles-per-entity-type", headers=h, timeout=30,
                      json={"functionalRoleNames": ["Team Wmo"]})
    eis(r.status_code == 200, f"{r.status_code}: {r.text[:200]}")
    rijen = r.json()["results"]
    namen = sorted({x["entityType"]["name"] for x in rijen})
    rollen = sorted({rol["name"] for x in rijen for rol in x["applicationRoles"]})
    eis(namen == ["Wmo-maatwerkvoorziening aanvragen"], f"zaaktypen: {namen}")
    zonder = requests.post(f"{PABC}/api/v1/application-roles-per-entity-type", timeout=30,
                           json={"functionalRoleNames": ["Team Wmo"]})
    eis(zonder.status_code == 401, f"zonder sleutel: {zonder.status_code}")
    return f"Team Wmo: {', '.join(namen)} met rollen {', '.join(rollen)}; zonder sleutel 401"


# ---------------------------------------------------- Open Archiefbeheer
@rook("openarchiefbeheer", "afgesloten zaken uit Open Zaak klaar voor een vernietigingslijst", vereist=("openzaak",))
def _(ctx):
    s = django_api_login(OPENARCHIEFBEHEER)
    r = s.get(f"{OPENARCHIEFBEHEER}/api/v1/zaken/", timeout=60)
    eis(r.status_code == 200, f"{r.status_code}")
    zaken = sorted(z["identificatie"] for z in r.json()["results"])
    eis(len(zaken) >= 4 and "VBS-2026-000102" in zaken, f"zaken: {zaken} (na-seed.sh gedraaid?)")
    return f"{len(zaken)} afgesloten zaken: {', '.join(zaken)}"


@rook("openarchiefbeheer", "medewerker logt in via Keycloak (realm podiumd)", vereist=("keycloak",))
def _(ctx):
    s = medewerker_login(f"{OAB}/oidc/authenticate/", "beheer.devries")
    r = _api(s, "GET", f"{OAB}/api/v1/whoami/")
    eis(r.status_code == 200, f"whoami na OIDC-login: {r.status_code}")
    return f"ingelogd als {r.json().get('username')}"


# ----------------------------------------------------------- Open Beheer
@rook("openbeheer", "zaaktypen van Voorbeeldstad uit Open Zaak", vereist=("openzaak",))
def _(ctx):
    s = django_api_login(OPENBEHEER)
    keuzes = s.get(f"{OPENBEHEER}/api/v1/service/choices/", timeout=30)
    eis(keuzes.status_code == 200 and keuzes.json(), f"services: {keuzes.status_code} {keuzes.text[:200]}")
    slug = keuzes.json()[0]["value"]
    r = s.get(f"{OPENBEHEER}/api/v1/service/{slug}/zaaktypen/", timeout=60)
    eis(r.status_code == 200, f"zaaktypen: {r.status_code} {r.text[:200]}")
    namen = sorted({z["omschrijving"] for z in r.json()["results"]})
    eis(len(namen) >= 4, f"zaaktypen: {namen}")
    return f"service {slug}: {len(namen)} zaaktypen ({', '.join(namen[:2])}, ...)"


@rook("openbeheer", "OIDC-configuratie wijst naar Keycloak (realm podiumd)")
def _(ctx):
    r = requests.get(f"{OPENBEHEER}/api/v1/oidc-info/", timeout=30)
    eis(r.status_code == 200, f"{r.status_code}")
    eis("/realms/podiumd" in r.text or r.json().get("enabled"), f"{r.text[:200]}")
    return r.text[:120]


# -------------------------------------------------------------- OMC
def maak_testzaak(oz, omschrijving):
    """Nieuwe zaak met eerste status voor de testmelder (zelfde zaaktype als VBS-2026-000106).

    De testmelder (MAYKIN.BURGER_MELDER) krijgt ook in de Open Formulieren-test bij elke run
    een nieuwe zaak; de vaste verwachtingen voor burgers A, B en C blijven zo kloppen.
    """
    zrc = "zaken/api/v1"
    basis = oz.eerste(f"{zrc}/zaken", identificatie="VBS-2026-000106")
    zt = oz.get(basis["zaaktype"])
    statustypen = sorted(oz.lijst("catalogi/api/v1/statustypen", zaaktype=zt["url"]), key=lambda s: s["volgnummer"])
    roltypen = {r["omschrijvingGeneriek"]: r for r in oz.lijst("catalogi/api/v1/roltypen", zaaktype=zt["url"])}
    rol = next(r for r in oz.lijst(f"{zrc}/rollen", zaak=basis["url"]) if r["betrokkeneType"] == "natuurlijk_persoon")
    ident = f"VBS-OMC-{int(time.time() * 1000) % 10**10}"
    zaak = oz.post(f"{zrc}/zaken", {
        "identificatie": ident, "bronorganisatie": basis["bronorganisatie"],
        "verantwoordelijkeOrganisatie": basis["bronorganisatie"], "zaaktype": zt["url"],
        "omschrijving": omschrijving, "startdatum": time.strftime("%Y-%m-%d"),
        "vertrouwelijkheidaanduiding": zt["vertrouwelijkheidaanduiding"]})
    oz.post(f"{zrc}/rollen", {"zaak": zaak["url"], "betrokkeneType": "natuurlijk_persoon",
                               "roltype": roltypen["initiator"]["url"], "roltoelichting": "Aanvrager",
                               "indicatieMachtiging": "", "betrokkeneIdentificatie": rol["betrokkeneIdentificatie"]})
    status = oz.post(f"{zrc}/statussen", {
        "zaak": zaak["url"], "statustype": statustypen[0]["url"],
        "datumStatusGezet": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()), "statustoelichting": ""})
    return zaak, status


def berichten_over(ident):
    r = requests.get(f"{NOTIFY_MOCK}/berichten", timeout=10)
    return [b for b in r.json()["berichten"] if ident in json.dumps(b["verzoek"])]


def omc_token():
    nu = int(time.time())
    return jwt.encode({"iss": "open-notificaties", "aud": "omc", "iat": nu, "exp": nu + 600,
                       "client_id": "open-notificaties", "user_id": "open-notificaties",
                       "user_representation": "Open Notificaties"}, os.environ["OMC_AUTH_JWT_SECRET"], algorithm="HS256")


@rook("omc", "keten: zaak in Open Zaak, Open Notificaties, OMC, e-mail via Notify",
      vereist=("openzaak", "opennotificaties", "openklant"))
def _(ctx):
    zaak, _ = maak_testzaak(open_zaak_beheer(), "Testzaak voor de OMC-keten (via Open Notificaties)")
    for _ in range(15):
        time.sleep(3)
        if berichten_over(zaak["identificatie"]):
            return f"e-mail over {zaak['identificatie']} bij de Notify-mock"
    raise AssertionError(f"geen bericht over {zaak['identificatie']} binnen 45 s: OMC 1.17.19 weigert de "
                         "notificatie van Open Notificaties 1.16 (veld 'source', 206/422), zie README")


@rook("omc", "notificatie in het OMC-formaat wordt een e-mail aan de inwoner", vereist=("openzaak", "openklant"))
def _(ctx):
    zaak, status = maak_testzaak(open_zaak_beheer(), "Testzaak voor OMC (directe notificatie)")
    body = {"actie": "create", "kanaal": "zaken", "resource": "status", "resourceUrl": status["url"],
            "hoofdObject": zaak["url"], "aanmaakdatum": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kenmerken": {"bronorganisatie": zaak["bronorganisatie"], "zaaktype": zaak["zaaktype"],
                          "vertrouwelijkheidaanduiding": zaak["vertrouwelijkheidaanduiding"]}}
    zonder = requests.post(f"{OMC}/Events/Listen", json=body, timeout=30)
    eis(zonder.status_code == 401, f"zonder JWT: {zonder.status_code}")
    r = requests.post(f"{OMC}/Events/Listen", json=body, headers={"Authorization": f"Bearer {omc_token()}"}, timeout=90)
    eis(r.status_code == 202, f"OMC: {r.status_code} {r.text[:300]}")
    for _ in range(10):
        b = berichten_over(zaak["identificatie"])
        if b:
            break
        time.sleep(2)
    eis(b, "geen bericht bij de Notify-mock")
    v = b[0]["verzoek"]
    eis(v.get("email_address") == f"{MAYKIN.BURGER_MELDER}@inwoner.voorbeeldstad.example", f"ontvanger: {v}")
    return (f"zonder JWT 401; 202, e-mail (template zaak aangemaakt) aan {v['email_address']} "
            f"voor {v['personalisation'].get('klant.voornaam')} {v['personalisation'].get('klant.achternaam')}")


# ------------------------------------------------------------ ClamAV
def clamd(opdracht, data=None):
    with socket.create_connection(("clamav.local", 3310), timeout=30) as s:
        s.sendall(b"z" + opdracht + b"\0")
        if data is not None:
            s.sendall(struct.pack("!L", len(data)) + data + struct.pack("!L", 0))
        antwoord = b""
        while not antwoord.endswith(b"\0"):
            deel = s.recv(4096)
            if not deel:
                break
            antwoord += deel
    return antwoord.rstrip(b"\0").decode()


@rook("clamav", "clamd herkent het EICAR-testbestand en laat een gewoon bestand door")
def _(ctx):
    eis(clamd(b"PING") == "PONG", "geen PONG")
    virus = clamd(b"INSTREAM", EICAR)
    schoon = clamd(b"INSTREAM", b"Gewone bijlage van een inwoner van Voorbeeldstad.")
    eis(virus.endswith("FOUND"), f"EICAR: {virus}")
    eis(schoon.endswith("OK"), f"schoon bestand: {schoon}")
    return f"{virus}; schoon bestand: {schoon}"


@rook("openformulieren", "upload met het EICAR-testvirus wordt geweigerd (ClamAV)", vereist=("clamav", "keycloak"))
def _(ctx):
    s, _, inzending = MAYKIN.of_sessie(ctx, "A")
    r0 = s.get(f"{MAYKIN.OPENFORMULIEREN}/api/v2/forms/{MAYKIN.FORMULIER}", timeout=30)
    h = {"X-CSRFToken": r0.headers.get("X-CSRFToken", ""), "Referer": MAYKIN.OPENFORMULIEREN + "/"}
    url = f"{MAYKIN.OPENFORMULIEREN}/api/v2/formio/fileupload"
    virus = s.post(url, headers=h, timeout=60, data={"submission": inzending["url"]},
                   files={"file": ("eicar.txt", EICAR, "text/plain")})
    schoon = s.post(url, headers=h, timeout=60, data={"submission": inzending["url"]},
                    files={"file": ("bijlage.txt", b"Gewone bijlage.", "text/plain")})
    eis(virus.status_code == 400, f"EICAR-upload gaf {virus.status_code}: {virus.text[:200]}")
    eis(schoon.status_code == 200, f"schone upload gaf {schoon.status_code}: {schoon.text[:200]}")
    return f"EICAR 400 ({virus.text[:80]}), schoon bestand 200"


# ----------------------------------------------------------- Mailpit
@rook("mailpit", "SMTP-opvang ontvangt en toont een bericht")
def _(ctx):
    onderwerp = f"Rooktest demogemeente {int(time.time())}"
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = "kiss@voorbeeldstad.example", "kennisbank@voorbeeldstad.example", onderwerp
    m.set_content("Testbericht.")
    with smtplib.SMTP("mailpit.local", 1025, timeout=30) as smtp:
        smtp.send_message(m)
    r = requests.get(f"{MAILPIT}/api/v1/search", params={"query": f'subject:"{onderwerp}"'}, timeout=30)
    eis(r.status_code == 200 and r.json().get("messages_count", 0) >= 1, f"{r.status_code}: {r.text[:200]}")
    return f"bericht '{onderwerp}' zichtbaar in Mailpit"
