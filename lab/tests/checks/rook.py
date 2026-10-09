"""Categorie 2, rook: per component een paar echte API-aanroepen op de geseede data.

Elke rooktest hoort bij een component en kan andere componenten vereisen. Zit een
vereist component niet in de stack, dan is de check een skip met die reden. Een
component zonder rooktest geeft een skip "nog geen rooktest", zodat gaten zichtbaar zijn.

Een stack kan rooktests toevoegen in stacks/<naam>/tests.py met dezelfde decorator:

    from checks.rook import rook

    @rook("openformulieren", "formulieren opvragen")
    def _(ctx):
        ...
        return "detailtekst"
"""
import base64
import json
import sys
import time

import requests

from kader import ROOT, Context, eis

sys.path.insert(0, str(ROOT / "seed"))

from lib import (  # noqa: E402
    KEYCLOAK,
    OPENNOTIFICATIES,
    OPENOBJECT,
    REFERENTIELIJSTEN,
    SELECTIELIJST,
    SINK,
    Client,
    brp_persoon,
    env,
    objecttype_url,
    open_klant,
    open_object,
    open_product,
    open_zaak_beheer,
    open_zaak_portaal,
    zgw_client,
)

CAT = "rook"
REGISTER: list[dict] = []

VERWACHTE_ZAKEN_A = {"VBS-2026-000101", "VBS-2026-000102"}
AFGESLOTEN_ZAAK = "VBS-2026-000102"
OBJECTTYPE_MELDING = "7c1d4a0e-5a7b-4c1e-8f00-0000000000a1"


def rook(component, naam, vereist=()):
    """Registreert een rooktest voor `component`; `vereist` zijn extra componenten."""
    def wrap(fn):
        REGISTER.append({"component": component, "naam": naam, "vereist": (component, *vereist), "fn": fn})
        return fn
    return wrap


def slug(tekst):
    uit = "".join(c if c.isalnum() else "-" for c in tekst.lower())
    while "--" in uit:
        uit = uit.replace("--", "-")
    return uit.strip("-")[:60]


def jwt_claims(token):
    deel = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(deel + "=" * (-len(deel) % 4)))


# ------------------------------------------------------------------ infra
@rook("brp-mock", "testpersoon raadplegen")
def _(ctx):
    p = brp_persoon(ctx.burger("A"))
    eis(p["burgerservicenummer"] == ctx.burger("A"), "verkeerde persoon")
    return f"{p['naam'].get('voornamen')} {p['naam'].get('geslachtsnaam')}"


@rook("keycloak", "DigiD-simulatie: inloggen als inwoner, claim bsn")
def _(ctx):
    bsn = ctx.burger("A")
    r = requests.post(f"{KEYCLOAK}/realms/voorbeeldstad/protocol/openid-connect/token", data={
        "grant_type": "password", "client_id": "mijnservices", "username": bsn,
        "password": env("DIGID_SIM_WACHTWOORD"), "scope": "openid",
    }, timeout=30)
    eis(r.status_code == 200, f"token-endpoint gaf {r.status_code}: {r.text[:300]}")
    claims = jwt_claims(r.json()["access_token"])
    eis(claims.get("bsn") == bsn, f"claim bsn = {claims.get('bsn')}")
    aud = claims.get("aud")
    eis("burgerportaal" in (aud if isinstance(aud, list) else [aud]), f"aud = {aud}")
    return f"bsn={claims['bsn']}, loa={claims.get('loa')}"


@rook("keycloak", "client credentials voor burgerportaal")
def _(ctx):
    r = requests.post(f"{KEYCLOAK}/realms/voorbeeldstad/protocol/openid-connect/token", data={
        "grant_type": "client_credentials", "client_id": "burgerportaal", "client_secret": env("KEYCLOAK_PORTAAL_CLIENT_SECRET"),
    }, timeout=30)
    eis(r.status_code == 200, f"token-endpoint gaf {r.status_code}")
    return "token ontvangen"


# -------------------------------------------------------------- Open Zaak
@rook("openzaak", "zaken van burger A opvragen (applicatie burgerportaal)")
def _(ctx):
    zaken = open_zaak_portaal().lijst("zaken/api/v1/zaken",
                                    rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=ctx.burger("A"))
    ids = {z["identificatie"] for z in zaken}
    eis(VERWACHTE_ZAKEN_A <= ids, f"verwacht {sorted(VERWACHTE_ZAKEN_A)}, kreeg {sorted(ids)}")
    ctx.gedeeld["zaken"] = {z["identificatie"]: z for z in zaken}
    return f"{len(zaken)} zaken: {', '.join(sorted(ids))}"


@rook("openzaak", "zaak ophalen met zaaktype en resultaat")
def _(ctx):
    oz = open_zaak_portaal()
    zaak = oz.get(ctx.gedeeld["zaken"][AFGESLOTEN_ZAAK]["url"])
    zaaktype = oz.get(zaak["zaaktype"])
    eis(zaak["einddatum"], "zaak is niet afgesloten")
    eis(zaak["resultaat"], "zaak heeft geen resultaat")
    resultaat = oz.get(zaak["resultaat"])
    ctx.gedeeld["zaak"] = zaak
    return f"{zaak['identificatie']} ({zaaktype['omschrijving']}), einddatum {zaak['einddatum']}, resultaat '{resultaat['toelichting']}'"


@rook("openzaak", "statussen")
def _(ctx):
    oz = open_zaak_portaal()
    statussen = oz.lijst("zaken/api/v1/statussen", zaak=ctx.gedeeld["zaak"]["url"])
    eis(len(statussen) == 3, f"verwacht 3 statussen, kreeg {len(statussen)}")
    namen = [oz.get(s["statustype"])["omschrijving"] for s in sorted(statussen, key=lambda s: s["datumStatusGezet"])]
    return " > ".join(namen)


@rook("openzaak", "rollen (natuurlijk persoon met BSN)")
def _(ctx):
    rollen = open_zaak_portaal().lijst("zaken/api/v1/rollen", zaak=ctx.gedeeld["zaak"]["url"],
                                     betrokkeneType="natuurlijk_persoon")
    eis(rollen and rollen[0]["betrokkeneIdentificatie"]["inpBsn"] == ctx.burger("A"), "geen rol met het BSN van burger A")
    return f"{rollen[0]['roltoelichting']}: {rollen[0]['betrokkeneIdentificatie']['geslachtsnaam']}"


@rook("openzaak", "documenten (metadata en inhoud)")
def _(ctx):
    oz = open_zaak_portaal()
    zios = oz.lijst("zaken/api/v1/zaakinformatieobjecten", zaak=ctx.gedeeld["zaak"]["url"])
    eis(len(zios) >= 2, f"verwacht minstens 2 documenten, kreeg {len(zios)}")
    uit = []
    for zio in zios:
        eio = oz.get(zio["informatieobject"])
        eis(eio["formaat"] == "application/pdf" and eio["bestandsomvang"] > 0, f"metadata klopt niet: {eio['titel']}")
        r = requests.get(eio["inhoud"], headers={"Authorization": oz.headers_fn()["Authorization"]}, timeout=30)
        eis(r.status_code == 200 and r.content.startswith(b"%PDF"), f"download {eio['titel']} gaf {r.status_code}")
        uit.append(f"{eio['titel']} ({eio['bestandsomvang']} bytes)")
    return "; ".join(uit)


@rook("openzaak", "zaakobject verwijst naar Open Object", vereist=("openobject",))
def _(ctx):
    zo = open_zaak_portaal().lijst("zaken/api/v1/zaakobjecten", zaak=ctx.gedeeld["zaak"]["url"])
    eis(zo and zo[0]["object"].startswith(OPENOBJECT), "geen zaakobject naar Open Object")
    ctx.gedeeld["object_url"] = zo[0]["object"]
    return zo[0]["object"]


@rook("openzaak", "applicatie burgerportaal mag niet schrijven")
def _(ctx):
    zaak = ctx.gedeeld["zaak"]
    open_zaak_portaal().post("zaken/api/v1/zaken", {
        "bronorganisatie": zaak["bronorganisatie"], "verantwoordelijkeOrganisatie": zaak["bronorganisatie"],
        "zaaktype": zaak["zaaktype"], "startdatum": "2026-10-01",
    }, verwacht=(403,))
    return "POST /zaken gaf 403"


@rook("openzaak", "applicatie burgerportaal heeft geen toegang tot autorisaties")
def _(ctx):
    open_zaak_portaal().get("autorisaties/api/v1/applicaties", verwacht=(403,))
    return "GET /applicaties gaf 403"


@rook("openzaak", "catalogus met gepubliceerde zaaktypen")
def _(ctx):
    zaaktypen = open_zaak_portaal().lijst("catalogi/api/v1/zaaktypen")
    namen = sorted(z["omschrijving"] for z in zaaktypen if not z["concept"])
    eis(len(namen) >= 4, f"verwacht 4 zaaktypen, kreeg {namen}")
    return ", ".join(namen)


# ------------------------------------------------------ Open Notificaties
@rook("opennotificaties", "kanalen")
def _(ctx):
    on = zgw_client(f"{OPENNOTIFICATIES}/api/v1", env("ZGW_BEHEER_CLIENT_ID"), env("ZGW_BEHEER_SECRET"), "Open Notificaties")
    kanalen = sorted(k["naam"] for k in on.lijst("kanaal"))
    eis({"zaken", "documenten"} <= set(kanalen), f"kanalen ontbreken: {kanalen}")
    return ", ".join(kanalen)


@rook("opennotificaties", "keten Open Zaak > Open Notificaties > abonnee", vereist=("openzaak", "notificatie-sink"))
def _(ctx):
    zaak = ctx.gedeeld["zaken"]["VBS-2026-000101"]
    start = time.time()
    open_zaak_beheer().patch(zaak["url"], {"toelichting": zaak["toelichting"]})
    while time.time() - start < 60:
        data = requests.get(f"{SINK}/notificaties", timeout=10).json()
        for n in data["notificaties"]:
            b = n["notificatie"]
            if b.get("resourceUrl") == zaak["url"] and b.get("actie") == "partial_update":
                return f"'{b['kanaal']}/{b['actie']}' afgeleverd na {time.time() - start:.1f}s"
        time.sleep(2)
    raise AssertionError("geen notificatie ontvangen binnen 60s")


# ------------------------------------------------------------ Open Klant
@rook("openklant", "partij en klantcontacten van burger A (token burgerportaal)")
def _(ctx):
    ok = open_klant("OPENKLANT_PORTAAL_TOKEN")
    partijen = ok.lijst("partijen", partijIdentificator__objectId=ctx.burger("A"))
    eis(len(partijen) == 1, f"verwacht 1 partij, kreeg {len(partijen)}")
    p = partijen[0]
    contacten = ok.lijst("klantcontacten", hadBetrokkene__wasPartij__uuid=p["uuid"])
    eis(contacten, "geen klantcontacten")
    naam = p["partijIdentificatie"]["contactnaam"]
    return f"{naam['voornaam']} {naam['achternaam']}: {len(contacten)} klantcontact(en), via {contacten[0]['kanaal']}"


# ----------------------------------------------------------- Open Object
@rook("openobject", "melding openbare ruimte (token burgerportaal)", vereist=("openzaak",))
def _(ctx):
    oo = open_object("OPENOBJECT_PORTAAL_TOKEN")
    obj = oo.get(ctx.gedeeld["object_url"])
    eis(obj["record"]["data"]["melderBsn"] == ctx.burger("A"), "object hoort niet bij burger A")
    meldingen = oo.lijst("objects", type=objecttype_url(OBJECTTYPE_MELDING))
    return f"{len(meldingen)} meldingen; deze: {obj['record']['data']['categorie']}"


# ---------------------------------------------------------- Open Product
@rook("openproduct", "producten van burger B")
def _(ctx):
    producten = open_product("producten").lijst("producten", eigenaren__bsn=ctx.burger("B"))
    eis(producten, "geen producten gevonden")
    return f"{len(producten)} product(en): {producten[0]['naam']} ({producten[0]['status']})"


# ------------------------------------------- Selectielijst, Referentielijsten
@rook("selectielijst", "procestypen 2020")
def _(ctx):
    procestypen = Client(f"{SELECTIELIJST}/api/v1", lambda: {}, "Selectielijst").get("procestypen", params={"jaar": 2020})
    eis(len(procestypen) >= 29, f"{len(procestypen)} procestypen")
    return f"{len(procestypen)} procestypen"


@rook("referentielijsten", "tabel KANAAL")
def _(ctx):
    items = Client(f"{REFERENTIELIJSTEN}/api/v1", lambda: {}, "Referentielijsten").lijst("items", tabel__code="KANAAL")
    eis(items, "tabel KANAAL is leeg")
    return f"{len(items)} kanalen: {', '.join(i['code'] for i in items)}"


def uitvoeren(ctx: Context):
    gedekt = set()
    for t in REGISTER:
        cid = f"{CAT}/{t['component']}/{slug(t['naam'])}"
        if not ctx.component(t["component"]):
            continue  # component zit niet in de stack: niet relevant
        gedekt.add(t["component"])
        ontbreekt = ctx.ontbrekend(*t["vereist"])
        if ontbreekt:
            ctx.overslaan(cid, CAT, t["component"], t["naam"], f"vereist {', '.join(ontbreekt)}, dat niet in deze stack zit")
            continue
        ctx.voer_uit(cid, CAT, t["component"], t["naam"], t["fn"], ctx)
    for comp in ctx.manifest["componenten"]:
        if comp["id"] in gedekt:
            continue
        reden = ("infrastructuur: alleen gezondheid" if comp.get("rol") == "infra"
                 else "nog geen rooktest voor dit component (tests/checks/rook.py of stacks/<naam>/tests.py)")
        ctx.overslaan(f"{CAT}/{comp['id']}", CAT, comp["id"], comp["naam"], reden)
