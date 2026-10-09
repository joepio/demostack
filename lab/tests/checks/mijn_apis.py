"""Categorie 5, mijn-apis: de VNG Mijn-API's (MijnZaken next, MijnTaken next) van een plug-in.

Een plug-in die een Mijn-API aanbiedt, noemt die in plugin.yaml onder `mijn_apis`
(contract: docs/PLUGINS.md). Per Mijn-API:

- mijn-apis/<id>/login: tokens voor de testburgers A, B en C;
- mijn-apis/<id>/mijnzaken/<workflow>: aansluitprofiel MijnZaken next (Arazzo, VNG API Lab);
- mijn-apis/<id>/mijntaken/<workflow>: aansluitprofiel MijnTaken next, als de plug-in in
  deze stack een takenbron heeft;
- mijn-apis/<id>/data/<check>: controles op de geseede testdata (statushistorie,
  documenten, filter, vertrouwelijkheid), met de velden uit de MijnZaken next-spec.

De profielen en specs staan ongewijzigd in vendor/vng-api-lab. Zonder plug-in met een
Mijn-API slaat de categorie zichzelf over, met die reden.
"""
import urllib.parse

import requests

from kader import Context, Overslaan, eis

CAT = "mijn-apis"
LAB = "vendor/vng-api-lab/aansluitprofielen"
PROFIELEN = {
    "mijnzaken": ("MijnZaken next", f"{LAB}/mijnzaken/mijnzaken-next.arazzo.yaml"),
    "mijntaken": ("MijnTaken next", f"{LAB}/mijntaken/mijntaken-next.arazzo.yaml"),
}


def burger_token(api: dict, bsn: str) -> str:
    """Token voor een burger bij een Mijn-API, volgens `login` uit plugin.yaml.

    login.type:
      dev-token        POST {url} met {"<veld>": bsn} (standaard veld "bsn"), antwoord
                       met access_token; voor demo's met een eigen testlogin
      digid-simulatie  password grant op de Keycloak-realm voorbeeldstad (DigiD-simulatie),
                       client `client_id` (standaard mijnservices)
    """
    login = api.get("login") or {}
    soort = login.get("type")
    if soort == "dev-token":
        r = requests.post(login["url"], json={login.get("veld", "bsn"): bsn}, timeout=15)
        eis(r.status_code == 200, f"POST {login['url']} gaf {r.status_code}: {r.text[:200]}")
        return r.json()["access_token"]
    if soort == "digid-simulatie":
        from checks.rook import KEYCLOAK, env  # noqa: PLC0415
        r = requests.post(f"{KEYCLOAK}/realms/voorbeeldstad/protocol/openid-connect/token", data={
            "grant_type": "password", "client_id": login.get("client_id", "mijnservices"), "username": bsn,
            "password": env("DIGID_SIM_WACHTWOORD"), "scope": "openid"}, timeout=30)
        eis(r.status_code == 200, f"Keycloak gaf {r.status_code}")
        return r.json()["access_token"]
    raise Overslaan(f"onbekend login.type '{soort}' (kies dev-token of digid-simulatie, docs/PLUGINS.md)")


def tokens_voor(ctx: Context, api: dict) -> dict:
    """Tokens voor A, B en C; een keer per Mijn-API, gedeeld met burger-isolatie."""
    alle = ctx.gedeeld.setdefault("mijn_api_tokens", {})
    if api["id"] not in alle:
        alle[api["id"]] = {letter: burger_token(api, ctx.burger(letter)) for letter in ("A", "B", "C")}
    return alle[api["id"]]


def mijn_api(ctx: Context, api_id: str) -> dict | None:
    return next((a for a in ctx.manifest.get("mijn_apis", []) if a["id"] == api_id), None)


def zelfde_host(basis: str, url: str) -> str:
    """Zet scheme en host van `url` op die van `basis`: een downloadUrl mag de publieke
    host van de plug-in hebben (zoals localhost:<poort>), de test draait in het netwerk."""
    b, u = urllib.parse.urlsplit(basis), urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((b.scheme, b.netloc, u.path, u.query, ""))


def _get(url, token, **kw):
    return requests.get(url, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=30, **kw)


def uitvoeren(ctx: Context):
    apis = ctx.manifest.get("mijn_apis") or []
    if not apis:
        ctx.overslaan(f"{CAT}/geen", CAT, None, "Mijn-API's van plug-ins",
                      "geen plug-in met een Mijn-API in deze stack: start met "
                      "`scripts/stack.sh up <stack> --plugin <map>` (docs/PLUGINS.md)")
        return
    for api in apis:
        test_api(ctx, api)


def test_api(ctx: Context, api: dict):
    aid, comp = api["id"], api.get("component", api["id"])
    pre = f"{CAT}/{aid}"
    naam = api.get("naam", aid)
    try:
        tokens = tokens_voor(ctx, api)
    except Overslaan as e:
        ctx.overslaan(f"{pre}/login", CAT, comp, f"{naam}: inloggen als testburger", str(e))
        return
    except Exception as e:  # noqa: BLE001
        ctx.leg_vast(f"{pre}/login", CAT, comp, f"{naam}: inloggen als testburger", "fail", reden=str(e)[:1500])
        return
    ctx.leg_vast(f"{pre}/login", CAT, comp, f"{naam}: inloggen als testburger", "pass",
                 detail=f"tokens voor A, B en C via {api['login']['type']}")

    for profiel, (titel, arazzo) in PROFIELEN.items():
        basis = api.get(profiel)
        if not basis:
            ctx.overslaan(f"{pre}/{profiel}", CAT, comp, f"{titel} via {naam}",
                          api.get(f"{profiel}_reden") or f"{naam} biedt in deze stack geen {titel}")
            continue
        servers = {profiel: basis}
        if profiel == "mijntaken" and api.get("mijnzaken"):
            servers["mijnzaken"] = api["mijnzaken"]
        ctx.respect_jobs.append({
            "id": f"{aid}-{profiel}", "prefix": f"{pre}/{profiel}", "categorie": CAT, "component": comp,
            "naam": f"{titel} via {naam}", "arazzo": arazzo, "servers": servers,
            "inputs": {"tokenA": tokens["A"], "tokenB": tokens["B"]},
        })

    if api.get("mijnzaken"):
        data_controles(ctx, api, tokens)


def data_controles(ctx: Context, api: dict, tokens: dict):
    """Controles op de geseede data van de testburgers (seed/data.py)."""
    aid, comp, basis = api["id"], api.get("component", api["id"]), api["mijnzaken"].rstrip("/")
    ta, tc = tokens["A"], tokens["C"]
    g = ctx.gedeeld.setdefault(f"mijn_api_{aid}", {})

    def zaken_a():
        body = _get(f"{basis}/zaken", ta).json()
        zaken = {z["zaaknummer"]: z for z in body["results"]}
        g["zaken_a"] = zaken
        eis(set(zaken) == {"VBS-2026-000101", "VBS-2026-000102"}, f"zaken van A: {sorted(zaken)}")
        return ", ".join(sorted(zaken))

    def detail():
        z = g["zaken_a"]["VBS-2026-000102"]
        d = _get(f"{basis}/zaken/{z['uuid']}", ta).json()
        g["detail_a"] = d
        titels = [x["titel"] for x in d["statushistorie"]]
        eis(d["status"] == "gesloten" and titels == ["Ontvangen", "Ingepland", "Afgehandeld"], f"{d['status']}, {titels}")
        eis(len(d["documenten"]) == 2, f"{len(d['documenten'])} documenten, verwacht 2")
        return "gesloten, " + " > ".join(titels) + ", 2 documenten"

    def download():
        d = g["detail_a"]
        r = _get(zelfde_host(basis, d["documenten"][0]["downloadUrl"]), ta)
        eis(r.status_code == 200 and r.content[:4] == b"%PDF", f"status {r.status_code}")
        return f"PDF, {len(r.content)} bytes"

    def filter_open():
        body = _get(f"{basis}/zaken", ta, params={"status": "open"}).json()
        nummers = [x["zaaknummer"] for x in body["results"]]
        eis(nummers == ["VBS-2026-000101"], f"{nummers}")
        return "alleen VBS-2026-000101"

    def vertrouwelijk():
        zc = _get(f"{basis}/zaken", tc).json()["results"][0]
        namen = [x["naam"] for x in _get(f"{basis}/zaken/{zc['uuid']}", tc).json()["documenten"]]
        eis(not any("Verslag" in n for n in namen), f"documenten: {namen}")
        return f"zichtbaar: {namen}"

    for sub, naam, fn in (
        ("zaken-van-a", "burger A ziet precies zijn 2 zaken", zaken_a),
        ("detail-statushistorie", "detail: status, statushistorie en documenten", detail),
        ("download-eigen-document", "download van een eigen document geeft een PDF", download),
        ("filter-status-open", "filter status=open", filter_open),
        ("vertrouwelijk-verslag", "vertrouwelijk verslag niet zichtbaar voor burger C", vertrouwelijk),
    ):
        ctx.voer_uit(f"{CAT}/{aid}/data/{sub}", CAT, comp, naam, fn)
