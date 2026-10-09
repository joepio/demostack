"""Vult de demogemeente met fictieve testdata. Idempotent.

Volgorde:
 1. Catalogus, informatieobjecttypen en zaaktypen in Open Zaak (gepubliceerd)
 2. Applicatie "burgerportaal" met alleen-lezen-autorisaties
 3. Objecttype-versies (JSON-schema) in Open Object
 4. Zaken met rollen, statussen, documenten, resultaten en objecten
 5. Partijen, digitale adressen en klantcontacten in Open Klant
 6. Thema, producttype en producten in Open Product

Onderdelen van componenten die niet in de stack zitten (stacks/<naam>/stack.yaml,
DEMO_STACK) worden overgeslagen. Open Zaak en de BRP-mock zijn altijd nodig.

Gebruik (via scripts/stack.sh seed <naam>): python seed/seed.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data as D  # noqa: E402
from lib import (  # noqa: E402
    ApiFout,
    b64,
    brp_persoon,
    env,
    maak_pdf,
    objecttype_url,
    open_klant,
    open_object,
    open_product,
    open_zaak_beheer,
    stack_componenten,
    zorg_voor_objecttype,
)

RSIN = env("GEMEENTE_RSIN")
GEMEENTE = env("GEMEENTE_NAAM")

oz = open_zaak_beheer()
CAT = "catalogi/api/v1"
ZRC = "zaken/api/v1"
DRC = "documenten/api/v1"
AC = "autorisaties/api/v1"


def log(msg):
    print(msg, flush=True)


def uuid_van(url):
    return url.rstrip("/").split("/")[-1]


# --------------------------------------------------------------- catalogus
def zorg_voor_catalogus():
    bestaand = oz.eerste(f"{CAT}/catalogussen", domein=D.CATALOGUS["domein"], rsin=RSIN)
    if bestaand:
        log(f"catalogus bestaat al: {bestaand['url']}")
        return bestaand
    cat = oz.post(f"{CAT}/catalogussen", {**D.CATALOGUS, "rsin": RSIN})
    log(f"catalogus aangemaakt: {cat['url']}")
    return cat


def zorg_voor_informatieobjecttypen(catalogus):
    uit = {}
    bestaande = {i["omschrijving"]: i for i in oz.lijst(f"{CAT}/informatieobjecttypen", catalogus=catalogus["url"], status="alles")}
    for sleutel, iot in D.INFORMATIEOBJECTTYPEN.items():
        obj = bestaande.get(iot["omschrijving"])
        if not obj:
            obj = oz.post(f"{CAT}/informatieobjecttypen", {
                "catalogus": catalogus["url"],
                "beginGeldigheid": "2026-01-01",
                "trefwoorden": [],
                "omschrijvingGeneriek": {"informatieobjecttypeOmschrijvingGeneriek": iot["omschrijving"],
                                         "definitieInformatieobjecttypeOmschrijvingGeneriek": iot["omschrijving"],
                                         "herkomstInformatieobjecttypeOmschrijvingGeneriek": "Demogemeente",
                                         "hierarchieInformatieobjecttypeOmschrijvingGeneriek": "",
                                         "opmerkingInformatieobjecttypeOmschrijvingGeneriek": ""},
                **iot,
            })
            log(f"informatieobjecttype aangemaakt: {iot['omschrijving']}")
        if obj.get("concept"):
            oz.post(f"{CAT}/informatieobjecttypen/{uuid_van(obj['url'])}/publish", {})
            obj = oz.get(obj["url"])
        uit[sleutel] = obj
    return uit


def maak_zaaktype(catalogus, zt, iots):
    velden = {k: v for k, v in zt.items() if k not in ("sleutel", "statustypen", "resultaattypen", "documenten")}
    nieuw = oz.post(f"{CAT}/zaaktypen", {
        **velden,
        "catalogus": catalogus["url"],
        "indicatieInternOfExtern": "extern",
        "publicatieIndicatie": False,
        "verantwoordelijke": GEMEENTE,
        "beginGeldigheid": "2026-01-01",
        "versiedatum": "2026-01-01",
        "besluittypen": [],
        "gerelateerdeZaaktypen": [],
        "deelzaaktypen": [],
        "productenOfDiensten": zt["productenOfDiensten"],
    })
    url = nieuw["url"]
    for nr, (omschrijving, tekst) in enumerate(zt["statustypen"], 1):
        oz.post(f"{CAT}/statustypen", {"zaaktype": url, "omschrijving": omschrijving, "volgnummer": nr,
                                       "statustekst": tekst, "informeren": True})
    for omschrijving, generiek in D.ROLTYPEN:
        oz.post(f"{CAT}/roltypen", {"zaaktype": url, "omschrijving": omschrijving, "omschrijvingGeneriek": generiek})
    for omschrijving, sl_uuid, nominatie, generiek in zt["resultaattypen"]:
        oz.post(f"{CAT}/resultaattypen", {
            "zaaktype": url,
            "omschrijving": omschrijving,
            "resultaattypeomschrijving": D.sl_rto(generiek),
            "selectielijstklasse": D.sl_resultaat(sl_uuid),
            "archiefnominatie": nominatie,
            "brondatumArchiefprocedure": {"afleidingswijze": "afgehandeld", "datumkenmerk": "", "einddatumBekend": False,
                                          "objecttype": "", "registratie": "", "procestermijn": None},
        })
    for nr, (iot_sleutel, richting) in enumerate(zt["documenten"], 1):
        oz.post(f"{CAT}/zaaktype-informatieobjecttypen", {
            "zaaktype": url, "informatieobjecttype": iots[iot_sleutel]["url"], "volgnummer": nr, "richting": richting,
        })
    oz.post(f"{CAT}/zaaktypen/{uuid_van(url)}/publish", {})
    log(f"zaaktype aangemaakt en gepubliceerd: {zt['omschrijving']}")
    return oz.get(url)


def zorg_voor_zaaktypen(catalogus, iots):
    uit = {}
    for zt in D.ZAAKTYPEN:
        bestaande = oz.lijst(f"{CAT}/zaaktypen", catalogus=catalogus["url"], identificatie=zt["identificatie"], status="alles")
        gepubliceerd = [z for z in bestaande if not z.get("concept")]
        if gepubliceerd:
            uit[zt["sleutel"]] = gepubliceerd[0]
            continue
        for concept in bestaande:  # half aangemaakt bij een eerdere run: opnieuw
            oz.delete(concept["url"])
        uit[zt["sleutel"]] = maak_zaaktype(catalogus, zt, iots)
    return uit


# ----------------------------------------------------------- autorisaties
def zorg_voor_portaal_applicatie(zaaktypen, iots):
    client_id = env("ZGW_PORTAAL_CLIENT_ID")
    autorisaties = [{"component": "ztc", "scopes": ["catalogi.lezen"]}]
    for zt in zaaktypen.values():
        autorisaties.append({"component": "zrc", "scopes": ["zaken.lezen"], "zaaktype": zt["url"],
                             "maxVertrouwelijkheidaanduiding": "zeer_geheim"})
    for iot in iots.values():
        autorisaties.append({"component": "drc", "scopes": ["documenten.lezen"], "informatieobjecttype": iot["url"],
                             "maxVertrouwelijkheidaanduiding": "zeer_geheim"})
    body = {"clientIds": [client_id], "label": "Burgerportaal (alleen lezen)", "heeftAlleAutorisaties": False,
            "autorisaties": autorisaties}
    bestaand = oz.eerste(f"{AC}/applicaties", clientIds=client_id)
    if bestaand:
        oz.put(bestaand["url"], body)
        log("applicatie burgerportaal bijgewerkt")
    else:
        oz.post(f"{AC}/applicaties", body)
        log("applicatie burgerportaal aangemaakt")


# ------------------------------------------------------------- objecttypen
def zorg_voor_objecttype_versies():
    for sleutel, ot in D.OBJECTTYPEN.items():
        if zorg_voor_objecttype(ot["uuid"], ot.get("naam", sleutel), ot["schema"]):
            log(f"objecttype-versie gepubliceerd: {sleutel}")


def zorg_voor_object(soort, kenmerk, gegevens, startdatum, geometrie=None):
    oo = open_object()
    ot = D.OBJECTTYPEN[soort]
    type_url = objecttype_url(ot["uuid"])
    bestaand = oo.eerste("objects", type=type_url, data_attr=f"kenmerk__exact__{kenmerk}")
    if bestaand:
        return bestaand
    record = {"typeVersion": 1, "data": {"kenmerk": kenmerk, **gegevens}, "startAt": startdatum}
    if geometrie:
        record["geometry"] = geometrie
    obj = oo.post("objects", {"type": type_url, "record": record}, headers={"Content-Crs": "EPSG:4326"})
    log(f"object aangemaakt: {soort} {kenmerk}")
    return obj


# ------------------------------------------------------------------- zaken
def catalogus_onderdelen(zaaktype):
    statustypen = sorted(oz.lijst(f"{CAT}/statustypen", zaaktype=zaaktype["url"]), key=lambda s: s["volgnummer"])
    roltypen = {r["omschrijvingGeneriek"]: r for r in oz.lijst(f"{CAT}/roltypen", zaaktype=zaaktype["url"])}
    resultaattypen = {r["omschrijving"]: r for r in oz.lijst(f"{CAT}/resultaattypen", zaaktype=zaaktype["url"])}
    return statustypen, roltypen, resultaattypen


def persoon_identificatie(persoon):
    naam = persoon.get("naam", {})
    geslacht = persoon.get("geslacht", {}).get("code", "O").lower()
    # De GBA-mock geeft "JJJJMMDD", de officiele BRP API een object met "datum"
    geboorte = persoon.get("geboorte", {}).get("datum")
    if isinstance(geboorte, dict):
        geboorte = geboorte.get("datum")
    if isinstance(geboorte, str) and len(geboorte) == 8 and geboorte.isdigit() and geboorte[4:] != "0000":
        geboorte = f"{geboorte[:4]}-{geboorte[4:6]}-{geboorte[6:]}"
    vp = persoon.get("verblijfplaats", {}) or {}
    adres = vp.get("verblijfadres", vp)
    identificatie = {
        "inpBsn": persoon["burgerservicenummer"],
        "geslachtsnaam": naam.get("geslachtsnaam", ""),
        "voorvoegselGeslachtsnaam": naam.get("voorvoegsel", ""),
        "voornamen": naam.get("voornamen", ""),
        "geslachtsaanduiding": geslacht if geslacht in ("m", "v", "o") else "o",
        "verblijfsadres": {
            "aoaIdentificatie": vp.get("adresseerbaarObjectIdentificatie", "") or "onbekend",
            "wplWoonplaatsNaam": adres.get("woonplaats", "") or "onbekend",
            "gorOpenbareRuimteNaam": adres.get("officieleStraatnaam") or adres.get("straat", "") or "onbekend",
            "aoaPostcode": adres.get("postcode", ""),
            "aoaHuisnummer": adres.get("huisnummer") or 0,
            "aoaHuisletter": adres.get("huisletter", ""),
            "aoaHuisnummertoevoeging": adres.get("huisnummertoevoeging", ""),
        },
    }
    if geboorte and "-" in str(geboorte):
        identificatie["geboortedatum"] = geboorte
    return identificatie


def zorg_voor_zaak(spec, zaaktypen, iots, personen):
    zaaktype = zaaktypen[spec["zaaktype"]]
    zaak = oz.eerste(f"{ZRC}/zaken", identificatie=spec["identificatie"], bronorganisatie=RSIN)
    if zaak and zaak.get("einddatum"):
        return zaak  # afgesloten zaak: helemaal klaar
    statustypen, roltypen, resultaattypen = catalogus_onderdelen(zaaktype)
    if not zaak:
        body = {
            "identificatie": spec["identificatie"],
            "bronorganisatie": RSIN,
            "verantwoordelijkeOrganisatie": RSIN,
            "zaaktype": zaaktype["url"],
            "omschrijving": spec["omschrijving"],
            "toelichting": spec["toelichting"],
            "registratiedatum": spec["startdatum"],
            "startdatum": spec["startdatum"],
            "vertrouwelijkheidaanduiding": zaaktype["vertrouwelijkheidaanduiding"],
            "kenmerken": [{"kenmerk": spec["identificatie"], "bron": "demogemeente-seed"}],
        }
        if "melding" in spec:
            m = spec["melding"]
            body["zaakgeometrie"] = {"type": "Point", "coordinates": [m["lon"], m["lat"]]}
        zaak = oz.post(f"{ZRC}/zaken", body)
        log(f"zaak aangemaakt: {spec['identificatie']} ({spec['omschrijving']})")
    zaak_url = zaak["url"]

    # Rollen: aanvrager (natuurlijk persoon) en behandelaar (medewerker)
    rollen = oz.lijst(f"{ZRC}/rollen", zaak=zaak_url)
    if not any(r["betrokkeneType"] == "natuurlijk_persoon" for r in rollen):
        oz.post(f"{ZRC}/rollen", {
            "zaak": zaak_url, "betrokkeneType": "natuurlijk_persoon", "roltype": roltypen["initiator"]["url"],
            "roltoelichting": "Aanvrager", "indicatieMachtiging": "",
            "betrokkeneIdentificatie": persoon_identificatie(personen[spec["bsn"]]),
        })
    if not any(r["betrokkeneType"] == "medewerker" for r in rollen):
        oz.post(f"{ZRC}/rollen", {
            "zaak": zaak_url, "betrokkeneType": "medewerker", "roltype": roltypen["behandelaar"]["url"],
            "roltoelichting": "Behandelaar", "betrokkeneIdentificatie": D.MEDEWERKERS[spec["behandelaar"]],
        })

    # Documenten
    zios = oz.lijst(f"{ZRC}/zaakinformatieobjecten", zaak=zaak_url)
    gekoppeld = {z["informatieobject"] for z in zios}
    for nr, (iot_sleutel, titel) in enumerate(spec["documenten"], 1):
        identificatie = f"{spec['identificatie']}-D{nr}"
        eio = oz.eerste(f"{DRC}/enkelvoudiginformatieobjecten", identificatie=identificatie, bronorganisatie=RSIN)
        if not eio:
            pdf = maak_pdf(titel, [
                f"{GEMEENTE}",
                f"Zaak {spec['identificatie']}: {spec['omschrijving']}",
                f"Datum: {spec['startdatum']}",
                "Dit is een fictief document voor de demogemeente.",
            ])
            eio = oz.post(f"{DRC}/enkelvoudiginformatieobjecten", {
                "identificatie": identificatie,
                "bronorganisatie": RSIN,
                "creatiedatum": spec["startdatum"],
                "titel": titel,
                "auteur": GEMEENTE,
                "taal": "dut",
                "status": "definitief",
                "formaat": "application/pdf",
                "bestandsnaam": f"{identificatie}.pdf",
                "inhoud": b64(pdf),
                "informatieobjecttype": iots[iot_sleutel]["url"],
                "vertrouwelijkheidaanduiding": iots[iot_sleutel]["vertrouwelijkheidaanduiding"],
                "indicatieGebruiksrecht": False,
            })
        if eio["url"] not in gekoppeld:
            oz.post(f"{ZRC}/zaakinformatieobjecten", {"zaak": zaak_url, "informatieobject": eio["url"], "titel": titel})

    # Objecten in Open Object, gekoppeld als zaakobject
    obj = None
    if not aanwezig("openobject"):
        pass
    elif "melding" in spec:
        m = spec["melding"]
        obj = zorg_voor_object("melding", spec["identificatie"], {
            "categorie": m["categorie"], "omschrijving": spec["omschrijving"],
            "locatie": {"lat": m["lat"], "lon": m["lon"]}, "melderBsn": spec["bsn"], "zaak": zaak_url,
        }, spec["startdatum"], {"type": "Point", "coordinates": [m["lon"], m["lat"]]})
        omschrijving = "Melding openbare ruimte"
    elif "parkeervergunning" in spec and spec.get("resultaat"):
        obj = zorg_voor_object("parkeervergunning", spec["identificatie"], {
            "bsn": spec["bsn"], **spec["parkeervergunning"], "zaak": zaak_url,
        }, spec["parkeervergunning"]["geldigVan"])
        omschrijving = "Parkeervergunning"
    if obj:
        zaakobjecten = oz.lijst(f"{ZRC}/zaakobjecten", zaak=zaak_url)
        if not any(z["object"] == obj["url"] for z in zaakobjecten):
            oz.post(f"{ZRC}/zaakobjecten", {"zaak": zaak_url, "object": obj["url"], "objectType": "overige",
                                            "objectTypeOverige": omschrijving, "relatieomschrijving": omschrijving})

    # Statussen (en bij een afgesloten zaak eerst het resultaat)
    bestaande = {s["statustype"] for s in oz.lijst(f"{ZRC}/statussen", zaak=zaak_url)}
    datums = spec["statussen"]
    for i, datum in enumerate(datums):
        statustype = statustypen[i]
        if statustype["url"] in bestaande:
            continue
        is_eind = statustype is statustypen[-1]
        if is_eind:
            if not spec.get("resultaat"):
                raise ApiFout(f"{spec['identificatie']}: eindstatus zonder resultaat")
            if not oz.eerste(f"{ZRC}/resultaten", zaak=zaak_url):
                oz.post(f"{ZRC}/resultaten", {"zaak": zaak_url, "resultaattype": resultaattypen[spec["resultaat"]]["url"],
                                              "toelichting": spec["resultaat"]})
        oz.post(f"{ZRC}/statussen", {"zaak": zaak_url, "statustype": statustype["url"],
                                     "datumStatusGezet": f"{datum}T{9 + i:02d}:00:00+02:00",
                                     "statustoelichting": statustype.get("statustekst", "")})
    return oz.get(zaak_url)


# -------------------------------------------------------------- Open Klant
def zorg_voor_partij(ok, persoon):
    bsn = persoon["burgerservicenummer"]
    bestaand = ok.eerste("partijen", partijIdentificator__objectId=bsn)
    if bestaand:
        return bestaand
    naam = persoon.get("naam", {})
    partij = ok.post("partijen", {
        "soortPartij": "persoon",
        "indicatieActief": True,
        "indicatieGeheimhouding": False,
        "voorkeurstaal": "nld",
        "interneNotitie": "Fictieve testpersoon (demogemeente)",
        "digitaleAdressen": [],
        "rekeningnummers": [],
        "voorkeursDigitaalAdres": None,
        "voorkeursRekeningnummer": None,
        "partijIdentificatie": {"contactnaam": {
            "voorletters": "".join(v[0] + "." for v in naam.get("voornamen", "").split()),
            "voornaam": naam.get("voornamen", ""),
            "voorvoegselAchternaam": naam.get("voorvoegsel", ""),
            "achternaam": naam.get("geslachtsnaam", ""),
        }},
    })
    ok.post("partij-identificatoren", {
        "identificeerdePartij": {"uuid": partij["uuid"]},
        "partijIdentificator": {"codeObjecttype": "natuurlijk_persoon", "codeSoortObjectId": "bsn",
                                "objectId": bsn, "codeRegister": "brp"},
    })
    ok.post("digitaleadressen", {
        "verstrektDoorPartij": {"uuid": partij["uuid"]}, "verstrektDoorBetrokkene": None,
        "adres": f"{bsn}@inwoner.voorbeeldstad.example", "soortDigitaalAdres": "email", "omschrijving": "Privé",
    })
    log(f"partij aangemaakt voor BSN {bsn}")
    return ok.get(partij["url"])


def zorg_voor_klantcontact(ok, spec, partij, zaken):
    bestaande = ok.lijst("klantcontacten", hadBetrokkene__wasPartij__uuid=partij["uuid"])
    if any(k["onderwerp"] == spec["onderwerp"] for k in bestaande):
        return
    kc = ok.post("klantcontacten", {
        "kanaal": spec["kanaal"], "onderwerp": spec["onderwerp"], "inhoud": spec["inhoud"],
        "indicatieContactGelukt": True, "taal": "nld", "vertrouwelijk": False,
        "plaatsgevondenOp": spec["plaatsgevondenOp"],
    })
    naam = partij["partijIdentificatie"]["contactnaam"]
    ok.post("betrokkenen", {
        "wasPartij": {"uuid": partij["uuid"]}, "hadKlantcontact": {"uuid": kc["uuid"]},
        "rol": "klant", "initiator": True, "organisatienaam": "",
        "contactnaam": {k: naam.get(k, "") for k in ("voorletters", "voornaam", "voorvoegselAchternaam", "achternaam")},
    })
    zaak = zaken.get(spec["zaak"])
    if zaak:
        ok.post("onderwerpobjecten", {
            "klantcontact": {"uuid": kc["uuid"]}, "wasKlantcontact": None,
            "onderwerpobjectidentificator": {"codeObjecttype": "zaak", "codeSoortObjectId": "uuid",
                                             "objectId": zaak["uuid"], "codeRegister": "openzaak"},
        })
    log(f"klantcontact aangemaakt: {spec['onderwerp']}")


# ------------------------------------------------------------ Open Product
# Let op: de API van Open Product gebruikt snake_case-veldnamen.
def zorg_voor_producten(zaken):
    pt = open_product("producttypen")
    thema = next((t for t in pt.lijst("themas") if t["naam"] == D.PRODUCT_THEMA["naam"]), None)
    if not thema:
        thema = pt.post("themas", {**D.PRODUCT_THEMA, "gepubliceerd": True, "hoofd_thema": None, "producttype_uuids": []})
        log("thema aangemaakt: Parkeren")
    producttype = next((p for p in pt.lijst("producttypen") if p.get("code") == D.PRODUCTTYPE["code"]), None)
    if not producttype:
        producttype = pt.post("producttypen", {
            "code": D.PRODUCTTYPE["code"],
            "naam": D.PRODUCTTYPE["naam"],
            "samenvatting": D.PRODUCTTYPE["samenvatting"],
            "beschrijving": D.PRODUCTTYPE["beschrijving"],
            "uniforme_product_naam": D.PRODUCTTYPE["upl_naam"],
            "thema_uuids": [thema["uuid"]],
            "gepubliceerd": True,
            "toegestane_statussen": ["actief", "verlopen"],
            "keywords": ["parkeren", "vergunning"],
            "doelgroep": "burgers",
            "interne_opmerkingen": "Demogemeente",
        })
        log("producttype aangemaakt: Parkeervergunning voor bewoners")
    pr = open_product("producten")
    for spec in D.ZAKEN:
        if "parkeervergunning" not in spec or not spec.get("resultaat"):
            continue
        bestaande = pr.lijst("producten", eigenaren__bsn=spec["bsn"])
        if any(p.get("producttype", {}).get("uuid") == producttype["uuid"] for p in bestaande):
            continue
        pv = spec["parkeervergunning"]
        pr.post("producten", {
            "producttype_uuid": producttype["uuid"],
            "naam": f"Parkeervergunning {pv['zone']} ({pv['kenteken']})",
            "start_datum": pv["geldigVan"],
            "eind_datum": pv["geldigTot"],
            "status": "actief",
            "prijs": "60.00",
            "frequentie": "jaarlijks",
            "gepubliceerd": True,
            "eigenaren": [{"bsn": spec["bsn"]}],
            "aanvraag_zaak_url": zaken[spec["identificatie"]]["url"],
        })
        log(f"product aangemaakt voor BSN {spec['bsn']}")


COMPONENTEN = stack_componenten()


def aanwezig(component):
    return COMPONENTEN is None or component in COMPONENTEN


def main():
    log(f"== Seed {GEMEENTE} (RSIN {RSIN}), stack {os.environ.get('DEMO_STACK', '?')}")
    if not aanwezig("openzaak"):
        log("geen Open Zaak in deze stack: niets te seeden")
        return
    personen = {bsn: brp_persoon(bsn) for bsn in D.INWONERS}
    log(f"{len(personen)} testpersonen opgehaald uit de BRP-mock")

    catalogus = zorg_voor_catalogus()
    iots = zorg_voor_informatieobjecttypen(catalogus)
    zaaktypen = zorg_voor_zaaktypen(catalogus, iots)
    zorg_voor_portaal_applicatie(zaaktypen, iots)
    if aanwezig("openobject"):
        zorg_voor_objecttype_versies()
    else:
        log("geen Open Object in deze stack: objecttypen en objecten overgeslagen")

    zaken = {spec["identificatie"]: zorg_voor_zaak(spec, zaaktypen, iots, personen) for spec in D.ZAKEN}
    log(f"{len(zaken)} zaken klaar")

    if aanwezig("openklant"):
        zorg_voor_klant(personen, zaken)
    else:
        log("geen Open Klant in deze stack: partijen en klantcontacten overgeslagen")
    if aanwezig("openproduct"):
        zorg_voor_producten(zaken)
    else:
        log("geen Open Product in deze stack: producten overgeslagen")
    log("== Seed klaar")


def zorg_voor_klant(personen, zaken):
    ok = open_klant()
    partijen = {bsn: zorg_voor_partij(ok, p) for bsn, p in personen.items()}
    for spec in D.KLANTCONTACTEN:
        zorg_voor_klantcontact(ok, spec, partijen[spec["bsn"]], zaken)
    log(f"{len(partijen)} partijen en {len(D.KLANTCONTACTEN)} klantcontacten klaar")


if __name__ == "__main__":
    try:
        main()
    except ApiFout as e:
        print(f"FOUT: {e}", file=sys.stderr)
        sys.exit(1)
