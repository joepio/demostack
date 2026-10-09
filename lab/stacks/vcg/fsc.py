"""OpenFSC in stack vcg: hulpfuncties voor seed en tests.

Drie peers in de FSC-testgroep "fsc-voorbeeldstad" (zie compose.yml en fsc-pki.sh):
directory, Gemeente Voorbeeldstad (afnemer, outway) en BRP-leverancier Testland (fictief,
aanbieder van "brp-personen" via een inway voor de BRP-mock).

De beheer-API's (controller-administratie, manager-intern) zijn alleen bereikbaar met
mTLS en een certificaat van de interne CA van de organisatie ("beheer" uit de test-PKI).

Het pad van de keten:
  1. BRP-leverancier registreert de dienst bij de eigen controller (naam, endpoint,
     inway-adres)
  2. BRP-leverancier publiceert de dienst in de directory (contract met een
     servicePublication-grant; de directory tekent automatisch)
  3. Voorbeeldstad vraagt een verbinding aan (contract met een serviceConnection-grant
     voor de eigen outway, op basis van de vingerafdruk van de publieke sleutel)
  4. BRP-leverancier accepteert het contract (tekent)
  5. Een applicatie van Voorbeeldstad roept de outway aan met de grant-hash in de header
     Fsc-Grant-Hash; de outway haalt een token bij de manager van de aanbieder en gaat
     via mTLS naar de inway, die de BRP-mock aanroept
"""
import os
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
PKI = Path(os.environ.get("FSC_PKI_DIR", ROOT / "stacks" / "vcg" / ".fsc-pki"))
GROEP = "fsc-voorbeeldstad"
DIRECTORY_ID = "00000099000000000000"
VOORBEELDSTAD_ID = "00000099000000000001"
BRP_ID = "00000099000000000002"
DIENST = "brp-personen"
OUTWAY = "http://outway.voorbeeldstad.fsc.local:8080"

ORGS = {
    "voorbeeldstad": {"manager": "https://manager.voorbeeldstad.fsc.local:7443",
                      "controller": "https://controller.voorbeeldstad.fsc.local:7444"},
    "brp": {"manager": "https://manager.brp.fsc.local:7443",
            "controller": "https://controller.brp.fsc.local:7444"},
    "directory": {"manager": "https://directory.fsc.local:7443",
                  "controller": "https://controller.directory.fsc.local:7444"},
}
MONITORING = {
    "directory-manager": "directory.fsc.local", "directory-controller": "controller.directory.fsc.local",
    "voorbeeldstad-manager": "manager.voorbeeldstad.fsc.local",
    "voorbeeldstad-controller": "controller.voorbeeldstad.fsc.local",
    "voorbeeldstad-outway": "outway.voorbeeldstad.fsc.local", "voorbeeldstad-txlog": "txlog.voorbeeldstad.fsc.local",
    "brp-manager": "manager.brp.fsc.local", "brp-controller": "controller.brp.fsc.local",
    "brp-inway": "inway.brp.fsc.local", "brp-txlog": "txlog.brp.fsc.local",
}


def beschikbaar():
    return (PKI / "klaar").exists()


def sessie(org):
    """requests-sessie met het beheercertificaat van de interne CA van org."""
    s = requests.Session()
    d = PKI / "intern" / org
    s.cert = (str(d / "beheer" / "cert.pem"), str(d / "beheer" / "key.pem"))
    s.verify = str(d / "ca" / "root.pem")
    return s


def api(org, deel, methode, pad, **kw):
    r = sessie(org).request(methode, ORGS[org][deel] + pad, timeout=30, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"FSC {org}/{deel} {methode} {pad} -> {r.status_code}: {r.text[:500]}")
    return r.json() if r.content else None


def gezond(naam):
    r = requests.get(f"http://{MONITORING[naam]}:8081/health/ready", timeout=5)
    return r.status_code


def contracten(org, grant_type=None):
    params = {"limit": 100}
    if grant_type:
        params["grant_type"] = grant_type
    return api(org, "manager", "GET", "/v1/contracts", params=params).get("contracts", [])


def nieuw_contract(org, grants):
    nu = int(time.time())
    inhoud = {
        "iv": str(uuid7()), "group_id": GROEP, "hash_algorithm": "HASH_ALGORITHM_SHA3_512",
        "created_at": nu, "validity": {"not_before": nu - 60, "not_after": nu + 365 * 86400},
        "grants": grants,
    }
    return api(org, "manager", "POST", "/v1/contracts", json={"contract_content": inhoud})["content_hash"]


def uuid7():
    """UUID versie 7 (tijdgeordend), zoals FSC voor de IV van een contract eist."""
    ms = int(time.time() * 1000)
    r = int.from_bytes(os.urandom(10), "big")
    waarde = (ms & ((1 << 48) - 1)) << 80 | 0x7 << 76 | (r >> 62 & 0xFFF) << 64 | 0b10 << 62 | (r & ((1 << 62) - 1))
    return uuid.UUID(int=waarde)


def grant_dienstverbinding():
    """Het geldige serviceConnection-contract van Voorbeeldstad voor de BRP-dienst: (contract, grant)."""
    for c in contracten("voorbeeldstad", "GRANT_TYPE_SERVICE_CONNECTION"):
        for g in c["content"]["grants"]:
            dienst = g.get("service", {})
            if dienst.get("name") == DIENST and dienst.get("peer_id") == BRP_ID:
                return c, g
    return None, None


def roep_brp_aan(bsn, grant_hash, velden=("burgerservicenummer", "naam")):
    """Personen bevragen bij de BRP-leverancier via de outway van Voorbeeldstad."""
    return requests.post(
        f"{OUTWAY}/personen", timeout=30,
        headers={"Fsc-Grant-Hash": grant_hash, "Content-Type": "application/json"},
        json={"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": [bsn], "fields": list(velden)},
    )
