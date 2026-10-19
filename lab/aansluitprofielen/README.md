# Aansluitprofiel MijnZaken op ZGW, tegen de echte Open Zaak

Het ZGW-aansluitprofiel van het VNG API Lab
(`aansluitprofielen/mijnzaken/zgw.arazzo.yaml`) uitgevoerd tegen Open Zaak 1.29.0
in DemoStack, met Redocly Respect 2.57.0.

Het profiel is categorie `zgw` van de gedeelde testsuite en draait in elke stack met
Open Zaak, in twee modi:

```bash
scripts/stack.sh test kern --alleen zgw
# zgw/gedrag/<workflow>: schema- en content-typecontroles als waarschuwing
# zgw/strikt/<workflow>: standaard van Respect, alle controles tellen
```

Welk profiel en welke zaken-URL: sectie `zgw` in `stacks/<naam>/stack.yaml`. Respect
draait in een container in het docker-netwerk zonder internet; daarom gebruikt de
testsuite de aangepaste kopie met het lokale schema. Het ongewijzigde profiel haalt de
gemma-zaken-spec van GitHub en heeft dus internet nodig.

- **Token:** een ZGW-JWT van applicatie `burgerportaal` (alleen lezen), gemaakt uit `.env`.
- **Testburgers:** A = 999990627 (Stephan Janssen), B = 999997609 (Eleonora de Crooy).
- **Eén token voor beide burgers:** ZGW 1.x kent alleen applicatietokens, dus `tokenA` en
  `tokenB` zijn hetzelfde token.
- **Canonieke URL:** Open Zaak moet bereikbaar zijn onder `http://openzaak.local:8000`.
  Via de hostpoort 8001 geeft het detail een 403, zie `docs/openzaak-bevindingen.md`, D1.
  In het docker-netwerk gaat dat vanzelf.
- **Uitvoer:** per workflow in `results/<stack>.json`; de ruwe uitvoer van Respect in
  `results/raw/<stack>/` (niet in git, bevat tokens).

## Bestanden

| Bestand | Wat |
|---|---|
| `mijnzaken/zgw.upstream.arazzo.yaml` | Ongewijzigde kopie uit het VNG API Lab |
| `mijnzaken/zgw.openzaak.arazzo.yaml` | Aangepaste kopie voor Open Zaak 1.29.0 |
| `mijnzaken/openzaak-zaken-1.29.0.yaml` | Schema zoals Open Zaak het serveert (`/zaken/api/v1/openapi.yaml`) |
| `mijnzaken/openzaak-zaken-1.29.0.respect.yaml` | Dat schema na `normaliseer_schema.py` |
| `normaliseer_schema.py` | Maakt het Open Zaak-schema bruikbaar voor Ajv |

## Verschillen tussen het profiel en Open Zaak

| # | Upstream (gemma-zaken 1.5.1) | Open Zaak 1.29.0 | Aanpassing in de kopie |
|---|---|---|---|
| 1 | `sourceDescription` op raw.githubusercontent.com | eigen schema op `/zaken/api/v1/openapi.yaml` (de link `schema/openapi.yaml` stuurt door) | lokale kopie van het Open Zaak-schema |
| 2 | operationId `zaak_retrieve` | `zaak_read` (ook `*_read`, `*_delete`, `*_head` bij de andere resources) | `zaak_read` |
| 3 | `Accept-Crs` en `Content-Crs` verplichte requestheaders | `Accept-Crs` optioneel, `Content-Crs` geen requestparameter | `Content-Crs` weggelaten |
| 4 | schema werkt in Ajv | `nullable` zonder `type` (79x), discriminators zonder const/enum | genormaliseerd schema, inhoud gelijk |
| 5 | `servers`: zaken-api.vng.cloud | relatief `/zaken/api/v1` | geen, `--server` overschrijft het |

De workflows, stappen en succescriteria zijn niet veranderd.

## Resultaten (7 oktober 2026)

| Profiel | Modus | Workflows | Waarom de rest faalt |
|---|---|---|---|
| upstream | strikt | 0 van 5 | content-type van 403/404, `gezetdoor: null`, plus de twee autorisatieworkflows |
| openzaak | strikt | 0 van 5 | content-type van 403/404, `opdrachtgevendeOrganisatie: ""` (schema eist minLength 9), plus de twee autorisatieworkflows |
| upstream | gedrag | 3 van 5 | de twee autorisatieworkflows |
| openzaak | gedrag | 3 van 5 | de twee autorisatieworkflows |

"Strikt" is de standaard van Respect. In de modus "gedrag" tellen schema- en
content-typecontroles als waarschuwing (`--severity`).

Per workflow, in de modus "gedrag" (beide profielen gelijk):

| Workflow | Resultaat | Toelichting |
|---|---|---|
| `overzicht-naar-detail` | geslaagd | zaken op BSN, detail, statussen en zaakinformatieobjecten kloppen met elkaar |
| `zonder-token` | geslaagd | 403 zonder token (Open Zaak geeft 403, geen 401) |
| `onbekende-zaak` | geslaagd | 404 |
| `burger-a-haalt-zaak-van-burger-b` | gefaald, verwacht | met "het token van A" (het applicatietoken) geeft de zaak van B gewoon 200 |
| `burger-a-zoekt-op-bsn-van-burger-b` | gefaald, verwacht | zoeken op het BSN van B geeft B's 2 zaken (`count` 2) |

### Waarom de twee autorisatieworkflows falen

Dat is de bedoeling van het profiel. ZGW 1.x autoriseert per **applicatie**
(client-id plus zaaktypen en vertrouwelijkheid), niet per **burger**:

- **Het token zegt niets over een burger.** Applicatie `burgerportaal` mag elke zaak van de
  geautoriseerde zaaktypen lezen. Er bestaat geen "token van burger A".
- **Het BSN is een queryfilter.** `rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn`
  is een parameter die de client zelf kiest. Open Zaak controleert niet of de
  aanroeper die burger is.

Een MijnOmgeving die rechtstreeks op ZGW aansluit, moet die controle dus zelf
doen: de burger uit een geverifieerd token halen, en per zaak en per document de rol van
die burger controleren. Een Mijn-API die dat doet, haalt hetzelfde scenario wel (profiel
MijnZaken next, categorie `mijn-apis`, zie `docs/PLUGINS.md`).

### Afwijkingen van Open Zaak die het strikte profiel vindt

1. **Foutantwoorden** (401/403/404) hebben `Content-Type: application/json`, terwijl
   zowel het eigen schema als de standaard `application/problem+json` zegt.
2. **`opdrachtgevendeOrganisatie`** is `""` als er geen opdrachtgever is; het eigen
   schema eist `minLength: 9`.
3. **`Status.gezetdoor`** is `null`. In het eigen schema mag dat, in gemma-zaken 1.5.1
   niet (daar `type: string` zonder `nullable`).
4. **`expand=status.statustype`** (stap `zoek-zaken`) vouwt in Open Zaak niets uit. Je
   hebt `expand=status,status.statustype` nodig. Het profiel faalt hier niet op,
   maar de belofte "één call met expand" klopt niet tegen Open Zaak.
