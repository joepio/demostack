"""Categorie 4, burger-isolatie: kan burger A gegevens van burger B zien?

Voor elk burgerkanaal (portaal of burger-API) uit stack.yaml (`burgerkanalen`) voert de
module de controles van zijn `type` uit. Een type zonder implementatie geeft een skip met
die reden, zodat het gat zichtbaar blijft.

Types:
  mijnzaken  een MijnZaken next-API (VNG API Lab), bijvoorbeeld van een plug-in: token per
             burger zoals `login` van de Mijn-API zegt (`mijn_api` wijst naar een id uit
             `mijn_apis`, zie docs/PLUGINS.md)
  spa        portaal zonder eigen data, alleen een andere API uit `burgerkanalen` (`api`)
  zgw        ZGW-API rechtstreeks met een applicatietoken: kent geen burgers; de uitkomst
             staat in zgw/gedrag/burger-a-* (ZGW-aansluitprofiel)
Een stack of plug-in kan een type toevoegen in zijn tests.py met `@isolatietype("naam")`.
"""
import requests

from kader import Context, eis

CAT = "burger-isolatie"
TYPES = {}


def isolatietype(naam):
    def wrap(fn):
        TYPES[naam] = fn
        return fn
    return wrap


@isolatietype("mijnzaken")
def _mijnzaken(ctx: Context, kanaal: dict):
    from checks.mijn_apis import mijn_api, tokens_voor, zelfde_host  # noqa: PLC0415

    kid = kanaal["id"]
    api = mijn_api(ctx, kanaal.get("mijn_api", kid))
    if not api or not api.get("mijnzaken"):
        ctx.overslaan(f"{CAT}/{kid}", CAT, kid, f"isolatie {kid}",
                      f"kanaal verwijst naar Mijn-API '{kanaal.get('mijn_api', kid)}' zonder mijnzaken-URL (mijn_apis)")
        return
    basis = api["mijnzaken"].rstrip("/")
    tokens = {}

    def get(pad, token, **kw):
        h = {"Authorization": f"Bearer {token}"} if token else {}
        url = zelfde_host(basis, pad) if pad.startswith("http") else basis + pad
        return requests.get(url, headers=h, timeout=30, **kw)

    def lijst(token, **params):
        r = get("/zaken", token, params=params)
        eis(r.status_code == 200, f"/zaken gaf {r.status_code}")
        return r.json()["results"]

    gegevens = {}

    def b_heeft_data():
        tokens.update(tokens_voor(ctx, api))
        zaken_b = lijst(tokens["B"])
        eis(zaken_b, "burger B heeft geen zaken: de isolatietest zou niets bewijzen (seed gedraaid?)")
        gegevens["b"] = zaken_b
        detail_b = get(f"/zaken/{zaken_b[0]['uuid']}", tokens["B"]).json()
        gegevens["b_docs"] = [d["downloadUrl"] for d in detail_b.get("documenten", [])]
        return f"B ziet {len(zaken_b)} eigen zaken, {len(gegevens['b_docs'])} documenten bij de eerste"

    def lijst_a():
        nummers_b = {z["zaaknummer"] for z in gegevens["b"]}
        zaken_a = lijst(tokens["A"])
        lek = nummers_b & {z["zaaknummer"] for z in zaken_a}
        eis(not lek, f"A ziet zaken van B: {sorted(lek)}")
        return f"A ziet {len(zaken_a)} zaken, geen van B"

    def lijst_a_met_bsn_b():
        nummers_b = {z["zaaknummer"] for z in gegevens["b"]}
        r = get("/zaken", tokens["A"], params={"bsn": ctx.burger("B"), "betrokkene": ctx.burger("B")})
        if r.status_code in (400, 403):
            return f"{r.status_code} op een BSN-parameter"
        lek = nummers_b & {z["zaaknummer"] for z in r.json().get("results", [])}
        eis(not lek, f"met ?bsn=<B> ziet A zaken van B: {sorted(lek)}")
        return "BSN-parameter genegeerd: A ziet alleen eigen zaken"

    def detail_b():
        z = gegevens["b"][0]
        r = get(f"/zaken/{z['uuid']}", tokens["A"])
        eis(r.status_code in (403, 404), f"A krijgt {r.status_code} op zaak {z['zaaknummer']} van B")
        return f"{r.status_code} op de zaak van B"

    def document_b():
        eis(gegevens["b_docs"], "zaak van B heeft geen documenten om mee te testen")
        r = get(gegevens["b_docs"][0], tokens["A"])
        eis(r.status_code in (403, 404), f"A krijgt {r.status_code} op een document van B")
        return f"{r.status_code} op een document van B"

    def zonder_token():
        r = get("/zaken", None)
        eis(r.status_code == 401, f"{r.status_code} zonder token, verwacht 401")
        return "401"

    for sub, naam, fn in (
        ("b-heeft-data", "burger B heeft eigen data (voorwaarde)", b_heeft_data),
        ("lijst", "lijst van A bevat geen zaken van B", lijst_a),
        ("lijst-met-bsn-van-b", "A kan niet op het BSN van B filteren", lijst_a_met_bsn_b),
        ("detail", "A kan de zaak van B niet openen", detail_b),
        ("document", "A kan een document van B niet downloaden", document_b),
        ("zonder-token", "zonder token geen gegevens", zonder_token),
    ):
        ctx.voer_uit(f"{CAT}/{kid}/{sub}", CAT, kid, naam, fn)


@isolatietype("spa")
def _spa(ctx: Context, kanaal: dict):
    api = kanaal.get("api")
    ctx.overslaan(f"{CAT}/{kanaal['id']}", CAT, kanaal["id"], "portaal",
                  f"portaal zonder eigen data: toont alleen wat {api} teruggeeft; isolatie getest via {CAT}/{api}/*")


@isolatietype("zgw")
def _zgw(ctx: Context, kanaal: dict):
    ctx.overslaan(f"{CAT}/{kanaal['id']}", CAT, kanaal["id"], "ZGW rechtstreeks",
                  "ZGW kent alleen applicatietokens, geen burgers; zie zgw/gedrag/burger-a-* in dit rapport")


def uitvoeren(ctx: Context):
    kanalen = ctx.manifest.get("burgerkanalen", [])
    if not kanalen:
        ctx.overslaan(f"{CAT}/kanalen", CAT, None, "burgerkanalen",
                      "geen burgerkanalen (portalen of burger-API's) in stack.yaml of in een plug-in")
        return
    for kanaal in kanalen:
        fn = TYPES.get(kanaal.get("type"))
        if not fn:
            ctx.overslaan(f"{CAT}/{kanaal['id']}", CAT, kanaal["id"], f"isolatie {kanaal['id']}",
                          f"geen isolatietest voor kanaaltype '{kanaal.get('type')}': vul tests/checks/isolatie.py "
                          "of stacks/<naam>/tests.py aan")
            continue
        fn(ctx, kanaal)
