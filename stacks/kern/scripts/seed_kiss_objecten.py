"""Stap 2: demodata voor KISS in de Objecten API: afdelingen, groepen, medewerkers en veelgestelde vragen (VAC)."""
import json, os, sys, requests
D = os.environ["BASE_DOMAIN"]
B = f"https://objecten.{D}/api/v2"
H = {"Authorization": f"Token {os.environ['OBJ_TOKEN_KISS']}", "Content-Type": "application/json", "Content-Crs": "EPSG:4326"}
U = {n: os.environ[f"KISS_OT_{n.upper()}"] for n in ["Afdeling", "Groep", "Medewerker", "VAC", "Kennisartikel"]}
OT = lambda n: f"https://objecttypen.{D}/api/v2/objecttypes/{U[n]}"

def call(m, url, **kw):
    r = requests.request(m, url, headers=H, timeout=30, **kw)
    if r.status_code >= 400: print(m, url, r.status_code, r.text[:1000]); sys.exit(1)
    return r.json() if r.content else None

def ensure(typ, key, data):
    found = call("GET", f"{B}/objects", params={"type": OT(typ), "data_attr": f"{key}__exact__{data[key]}"})["results"]
    if found: return
    call("POST", f"{B}/objects", json={"type": OT(typ), "record": {"typeVersion": 1, "data": data, "startAt": "2026-01-01"}})
    print("+", typ, data[key])

AFD = [("AFD-OR", "Openbare Ruimte"), ("AFD-BZ", "Burgerzaken"), ("AFD-BEL", "Belastingen")]
for i, n in AFD: ensure("Afdeling", "identificatie", {"identificatie": i, "naam": n})
GRP = [("GRP-MOR", "Team Meldingen", "AFD-OR"), ("GRP-BALIE", "Balie Burgerzaken", "AFD-BZ")]
for i, n, a in GRP: ensure("Groep", "identificatie", {"identificatie": i, "naam": n, "afdelingId": a})

def mw(ident, vn, an, functie, afd, grp=None, tel="14 0000"):
    d = {"identificatie": ident, "voornaam": vn, "achternaam": an, "volledigeNaam": f"{vn} {an}", "functie": functie,
         "emails": [{"email": f"{ident}@demogemeente.local"}], "telefoonnummers": [{"telefoonnummer": tel}],
         "afdelingen": [{"afdelingId": a, "afdelingnaam": dict(AFD)[a]} for a in afd]}
    if grp: d["groepen"] = [{"groepsId": g, "groepsnaam": {x[0]: x[1] for x in GRP}[g]} for g in grp]
    ensure("Medewerker", "identificatie", d)

mw("kcc", "Kim", "Contact", "Klantcontactmedewerker", ["AFD-BZ"])
mw("redacteur", "Rik", "Redacteur", "Redacteur kennisbank", ["AFD-BZ"])
mw("j.dewit", "Jasmijn", "de Wit", "Medewerker meldingen openbare ruimte", ["AFD-OR"], ["GRP-MOR"], "06 1234 5678")
mw("m.bakker", "Mehmet", "Bakker", "Opzichter wegen", ["AFD-OR"], ["GRP-MOR"], "06 2345 6789")
mw("s.jansen", "Sanne", "Jansen", "Baliemedewerker", ["AFD-BZ"], ["GRP-BALIE"])

VAC = [
    ("Hoe lang duurt het voordat een losse stoeptegel is gerepareerd?",
     "Een losliggende stoeptegel wordt binnen 14 dagen gerepareerd. Is er direct gevaar, dan komen we binnen 24 uur.", "AFD-OR",
     ["stoeptegel", "stoep", "melding", "reparatie"]),
    ("Hoe kan ik de status van mijn melding volgen?",
     "U krijgt een e-mail bij elke statuswijziging. Het KCC kan de status ook opzoeken met het zaaknummer.", "AFD-OR",
     ["melding", "status", "zaak"]),
    ("Wat moet ik meenemen voor een nieuw paspoort?",
     "Uw oude paspoort of ID-kaart en een recente pasfoto. Maak eerst een afspraak.", "AFD-BZ", ["paspoort", "afspraak"]),
    ("Kan ik uitstel van betaling krijgen voor de gemeentelijke belastingen?",
     "Ja, u kunt een betalingsregeling aanvragen via het formulier op de website of via het KCC.", "AFD-BEL",
     ["belasting", "betalingsregeling", "uitstel"]),
    ("Wanneer wordt mijn grofvuil opgehaald?",
     "Grofvuil wordt op afspraak opgehaald, meestal binnen twee weken. Twee keer per jaar is gratis.", "AFD-OR",
     ["grofvuil", "afval", "ophalen"]),
    ("Hoe verhuis ik naar een ander adres in de gemeente?",
     "Geef de verhuizing online door, uiterlijk vijf dagen na de verhuisdatum. Inloggen met DigiD is nodig.", "AFD-BZ",
     ["verhuizen", "adres", "brp"]),
    ("Kan ik kwijtschelding krijgen van de afvalstoffenheffing?",
     "Bij een laag inkomen en weinig vermogen kunt u kwijtschelding aanvragen. Dat kan tot drie maanden na de dagtekening van de aanslag.", "AFD-BEL",
     ["kwijtschelding", "afvalstoffenheffing", "belasting"]),
    ("Er ligt een boom over de weg, wat moet ik doen?",
     "Bij direct gevaar: bel 112. Anders doorverbinden met team Meldingen; zij sturen binnen 2 uur iemand langs.", "AFD-OR",
     ["boom", "gevaar", "storm", "melding"]),
]
for vraag, antw, afd, tw in VAC:
    ensure("VAC", "vraag", {"vraag": vraag, "antwoord": antw, "status": "actief", "doelgroep": "eu-burger",
                            "afdelingen": [{"afdelingId": afd, "afdelingNaam": dict(AFD)[afd]}],
                            "trefwoorden": [{"trefwoord": t} for t in tw]})
print("klaar")
