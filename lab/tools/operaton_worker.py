"""Procesworker voor Operaton (stack vcg): voert de externe taken van het proces
"Parkeervergunning behandelen" uit tegen Open Zaak.

Een gemeente met de VCG-basisset heeft Operaton als procesengine en Open Zaak als
zaakregistratie; de koppeling is een worker die externe taken ophaalt (fetchAndLock),
de zaak bijwerkt en de taak afrondt. Topics:

  zaak-in-behandeling  status "In behandeling" op de zaak en de behandelaar uit Open
                       Organisatie (medewerker van team "parkeren") als rol
  zaak-afhandelen      resultaat (Geleverd bij besluit "verleend", anders Niet geleverd)
                       en de eindstatus "Afgehandeld"

Procesvariabelen: zaakUrl (verplicht), besluit (na de gebruikerstaak).
Omgeving: OPERATON_ADMIN_USERNAME, OPERATON_ADMIN_PASSWORD, ZGW_OPERATON_SECRET,
OPENORGANISATIE_BEHEER_TOKEN. Draait in de tools-image (requests en PyJWT).
"""
import datetime
import os
import sys
import time
import traceback

import jwt
import requests

OPERATON = os.environ.get("OPERATON_URL", "http://operaton.local:8080/engine-rest")
OPENORGANISATIE = os.environ.get("OPENORGANISATIE_URL", "http://openorganisatie.local:8000")
AUTH = (os.environ["OPERATON_ADMIN_USERNAME"], os.environ["OPERATON_ADMIN_PASSWORD"])
WORKER = "voorbeeldstad-zaakworker"
TOPICS = ["zaak-in-behandeling", "zaak-afhandelen"]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def zgw_headers():
    token = jwt.encode({"iss": "operaton", "iat": int(time.time()), "client_id": "operaton",
                        "user_id": "operaton", "user_representation": "Operaton procesengine"},
                       os.environ["ZGW_OPERATON_SECRET"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}


def oz(methode, url, **kw):
    r = requests.request(methode, url, headers=zgw_headers(), timeout=30, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"Open Zaak {methode} {url} -> {r.status_code}: {r.text[:500]}")
    return r.json() if r.content else None


def statustype(zaak, omschrijving):
    basis = zaak["url"].split("/zaken/api/")[0]
    st = oz("GET", f"{basis}/catalogi/api/v1/statustypen", params={"zaaktype": zaak["zaaktype"]})["results"]
    gevonden = [s for s in st if s["omschrijving"] == omschrijving]
    if not gevonden:
        raise RuntimeError(f"statustype {omschrijving} ontbreekt bij het zaaktype")
    return gevonden[0]["url"]


def heeft_status(zaak, statustype_url):
    basis = zaak["url"].split("/zaken/api/")[0]
    st = oz("GET", f"{basis}/zaken/api/v1/statussen", params={"zaak": zaak["url"]})["results"]
    return any(s["statustype"] == statustype_url for s in st)


def zet_status(zaak, omschrijving, toelichting):
    url = statustype(zaak, omschrijving)
    if heeft_status(zaak, url):
        return False
    basis = zaak["url"].split("/zaken/api/")[0]
    nu = datetime.datetime.now(datetime.timezone.utc).isoformat()
    oz("POST", f"{basis}/zaken/api/v1/statussen",
       json={"zaak": zaak["url"], "statustype": url, "datumStatusGezet": nu, "statustoelichting": toelichting})
    return True


def behandelaar_uit_open_organisatie(team="Parkeren"):
    """Eerste medewerker van het team in Open Organisatie (of None)."""
    try:
        r = requests.get(f"{OPENORGANISATIE}/organisatie/api/v0/medewerkers",
                         headers={"Authorization": f"Token {os.environ['OPENORGANISATIE_BEHEER_TOKEN']}"},
                         timeout=20)
        r.raise_for_status()
        for m in r.json().get("results", []):
            if any(t.get("naam") == team for t in m.get("teams", []) if isinstance(t, dict)):
                return m
    except Exception as e:  # noqa: BLE001
        log("Open Organisatie niet bereikbaar of zonder team:", e)
    return None


def zet_behandelaar(zaak):
    basis = zaak["url"].split("/zaken/api/")[0]
    rollen = oz("GET", f"{basis}/zaken/api/v1/rollen", params={"zaak": zaak["url"], "omschrijvingGeneriek": "behandelaar"})
    if rollen["results"]:
        return None
    m = behandelaar_uit_open_organisatie()
    if not m:
        return None
    rt = oz("GET", f"{basis}/catalogi/api/v1/roltypen", params={"zaaktype": zaak["zaaktype"], "omschrijvingGeneriek": "behandelaar"})
    if not rt["results"]:
        return None
    oz("POST", f"{basis}/zaken/api/v1/rollen", json={
        "zaak": zaak["url"], "betrokkeneType": "medewerker", "roltype": rt["results"][0]["url"],
        "roltoelichting": "behandelaar, toegewezen door Operaton",
        "betrokkeneIdentificatie": {"identificatie": m["medewerkerId"], "achternaam": m["achternaam"],
                                    "voorletters": m["voornaam"][:1] + "."},
    })
    return f"{m['voornaam']} {m['achternaam']}"


def zaak_in_behandeling(zaak, variabelen):
    gezet = zet_status(zaak, "In behandeling", "Uw aanvraag is in behandeling genomen.")
    wie = zet_behandelaar(zaak)
    return {"behandelaar": {"value": wie or "", "type": "String"}}, f"status gezet={gezet}, behandelaar={wie}"


def zaak_afhandelen(zaak, variabelen):
    basis = zaak["url"].split("/zaken/api/")[0]
    besluit = (variabelen.get("besluit") or {}).get("value", "verleend")
    omschrijving = "Geleverd" if besluit == "verleend" else "Niet geleverd"
    if not zaak.get("resultaat"):
        rt = oz("GET", f"{basis}/catalogi/api/v1/resultaattypen", params={"zaaktype": zaak["zaaktype"]})["results"]
        rt = [r for r in rt if r["omschrijving"] == omschrijving]
        oz("POST", f"{basis}/zaken/api/v1/resultaten", json={"zaak": zaak["url"], "resultaattype": rt[0]["url"],
                                                               "toelichting": f"besluit: {besluit}"})
    gezet = zet_status(zaak, "Afgehandeld", "Uw aanvraag is afgehandeld.")
    return {}, f"resultaat {omschrijving}, eindstatus gezet={gezet}"


HANDLERS = {"zaak-in-behandeling": zaak_in_behandeling, "zaak-afhandelen": zaak_afhandelen}


def ronde():
    r = requests.post(f"{OPERATON}/external-task/fetchAndLock", auth=AUTH, timeout=40, json={
        "workerId": WORKER, "maxTasks": 5, "usePriority": True, "asyncResponseTimeout": 20000,
        "topics": [{"topicName": t, "lockDuration": 60000, "variables": ["zaakUrl", "besluit"]} for t in TOPICS],
    })
    r.raise_for_status()
    for taak in r.json():
        tid, topic = taak["id"], taak["topicName"]
        try:
            zaak = oz("GET", taak["variables"]["zaakUrl"]["value"])
            nieuw, uitleg = HANDLERS[topic](zaak, taak["variables"])
            requests.post(f"{OPERATON}/external-task/{tid}/complete", auth=AUTH, timeout=30,
                          json={"workerId": WORKER, "variables": nieuw}).raise_for_status()
            log(f"{topic} {zaak['identificatie']}: {uitleg}")
        except Exception as e:  # noqa: BLE001
            log(f"{topic} mislukt: {e}")
            pogingen = (taak.get("retries") if taak.get("retries") is not None else 3) - 1
            requests.post(f"{OPERATON}/external-task/{tid}/failure", auth=AUTH, timeout=30, json={
                "workerId": WORKER, "errorMessage": str(e)[:600], "errorDetails": traceback.format_exc()[-3000:],
                "retries": max(pogingen, 0), "retryTimeout": 15000,
            })


def main():
    log(f"worker {WORKER} start; topics {', '.join(TOPICS)}")
    while True:
        try:
            ronde()
        except Exception as e:  # noqa: BLE001
            log("Operaton niet bereikbaar:", e)
            time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
