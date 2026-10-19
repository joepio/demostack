# VNG DemoStack (werknaam)

Een demo- en testomgeving die bestaande open source Common Ground-componenten draait met
fictieve data, en ze test tegen de specificaties en aansluitprofielen van VNG. Met een
commando start je een complete stack: componenten met werkende configuratie, gekoppeld
aan elkaar en gevuld met de testdata van de fictieve "Gemeente Voorbeeldstad".

- **Wat het is.** Een set stacks (landschappen zoals een gemeente die kiest), een gedeelde
  seed en een gedeelde testsuite. Elke stack krijgt dezelfde testdata en dezelfde tests.
- **Waar de testcriteria vandaan komen.** Uit de VNG-specificaties: de ZGW API's, de
  Mijn-API's (MijnZaken en MijnTaken) en de aansluitprofielen (Arazzo) uit het VNG API Lab.
  Afwijkingen staan per check in het rapport, met de bron.
- **Eigen component aansluiten.** Een leverancier kan een eigen component als plug-in bij
  een stack zetten en laten testen tegen dezelfde criteria. Het contract staat in
  [`docs/PLUGINS.md`](docs/PLUGINS.md).
- **Licentie.** EUPL-1.2.

Het doel lijkt op dat van de Voorziening Common Ground (VCG): een vaste set componenten
([VCG-basisset](https://code.overheid.nl/CommonGround/vcg-basisset)) die je in een keer
goed geconfigureerd neerzet. De versies hieronder volgen die basisset waar dat kan.

> Alleen voor demo, test en ontwikkeling. Geheimen worden lokaal gegenereerd,
> alles draait over HTTP, en tweestapsverificatie staat uit.

## Stacks

DemoStack bestaat uit stacks: complete landschappen zoals een gemeente die zou
kiezen, elk met dezelfde testdata en dezelfde testsuite. Opbouw, afspraken en hoe je
een stack toevoegt: [`stacks/README.md`](stacks/README.md).

| Stack | Inhoud | Status |
|---|---|---|
| `kern` | variant 1: Open Zaak, Open Notificaties, Open Object, Open Klant, Open Product, Referentielijsten, VNG Selectielijst | werkt: 34 geslaagd, 7 bekende fouten, 5 overgeslagen |
| `maykin` | kern plus Open VTB, Open Formulieren, Open Inwoner | werkt: 62 geslaagd, 7 bekende fouten, 6 overgeslagen |
| `dimpact` | wat PodiumD 4.9.3 draait: KISS, ITA, PABC, Open Formulieren, Open Inwoner, Objecten, Objecttypen, Open Archiefbeheer, Open Beheer, OMC (zonder ZAC) | werkt: 85 geslaagd, 8 bekende fouten, 11 overgeslagen |
| `g4` | NL Portal, IKO, Valtimo/GZAC, Open Formulieren op de registers en Open VTB | werkt: 73 geslaagd, 8 bekende fouten, 5 overgeslagen |
| `vcg` | de VCG-basisset op de kern: Open Organisatie, GPP-publicatiebank, Open Beheer, Operaton, OpenPlan, OpenPDC en OpenPub, OpenRegister, OpenFSC (zonder Operaton Modeler en OpenFTV) | werkt: 69 geslaagd, 7 bekende fouten, 6 overgeslagen |

Alle stacks delen de basis (`stacks/basis/compose.yml`: Postgres, Redis, Keycloak als
DigiD-simulatie, BRP-mock, notificatie-sink), de seed (`seed/`) en de testsuite
(`tests/`). De tellingen zijn zonder plug-ins; die van maykin, dimpact, g4 en vcg zijn
afgeleid van de runs van 7 en 8 oktober 2026 (zie de kop van `results/<stack>.md`). De
vergelijking (welk component draait waar, testresultaten, isolatie, footprint en lessen)
staat in [`docs/STACKS.md`](docs/STACKS.md). De oude indeling in
varianten, met inspanning en blokkades per stap en een advies voor hosting, staat in
[`docs/VARIANTEN.md`](docs/VARIANTEN.md).

## Snel starten

Nodig: Docker met Compose v2, `openssl`, `python3`, en Node.js met `npm` (alleen voor de
eerste testrun, om Redocly CLI te installeren). Geheugen en schijf per stack (gemeten,
zie [`docs/STACKS.md`](docs/STACKS.md#footprint)):

| Stack | Geheugen | Images op schijf | Start inclusief seed |
|---|---|---|---|
| `kern` | 4,2 GiB | 8,3 GB | ruim 3 minuten |
| `maykin` | 7,5 GiB | 13,9 GB | ongeveer 5,5 minuten |
| `dimpact` | 9,0 GiB | 17,9 GB | ongeveer 6 minuten |
| `g4` | 8,0 GiB | 12,4 GB | ongeveer 5,5 minuten |
| `vcg` | 7,1 GiB | 17,4 GB | ongeveer 5 minuten |

```bash
scripts/stack.sh list               # welke stacks er zijn, en wat er nog draait
scripts/stack.sh up maykin          # maakt of vult .env aan, haalt of bouwt images,
                                    # start alles en laadt de testdata
scripts/stack.sh test maykin        # testsuite: results/maykin.json en results/maykin.md
scripts/stack.sh seed maykin        # testdata opnieuw laden (idempotent)
scripts/stack.sh down maykin        # stoppen en volumes wissen (--behoud-data om te bewaren)
scripts/stack.sh opruimen           # ongebruikte images en build-cache weg

scripts/stack.sh up kern --plugin ../leverancier/demostack   # met een plug-in
scripts/stack.sh test kern          # results/kern+<plug-in>.json en .md
```

Vervang `maykin` door `kern`, `dimpact`, `g4` of `vcg`. Er draait steeds één stack
tegelijk: `up` weigert te starten zolang er containers van een andere stack staan. Wissel
dus met `down` van de oude stack en `up` van de nieuwe; bij weinig schijf eerst
`opruimen`.

De eerste start duurt langer: images ophalen (bij een 429 van Docker Hub via
`mirror.gcr.io`) en, voor dimpact, g4 en vcg, een aantal componenten uit broncode bouwen
(`stacks/<naam>/bouw.sh`). Wat elke stack bevat en hoe je inlogt staat in
`stacks/<naam>/README.md`.

## Testsuite

`scripts/stack.sh test <naam>` draait voor elke stack dezelfde vijf categorieen en
schrijft per check geslaagd, gefaald of overgeslagen (altijd met reden) naar
`results/<naam>.json`, met een leesbare samenvatting in `results/<naam>.md`:

1. **gezondheid:** draaien de containers van elk component, en antwoordt het;
2. **rook:** per component echte API-aanroepen op de geseede data;
3. **zgw:** het ZGW-aansluitprofiel (Arazzo) rechtstreeks op Open Zaak, in de modi
   "gedrag" en "strikt";
4. **burger-isolatie:** kan burger A bij elk portaal of elke burger-API gegevens van
   burger B zien;
5. **mijn-apis:** de aansluitprofielen MijnZaken next en MijnTaken next (VNG API Lab) op
   elke Mijn-API die een plug-in aanbiedt, plus controles op de geseede data. Zonder
   plug-in overgeslagen, met die reden.

Met `--alleen zgw,mijn-apis` draai je een deel. Details: [`tests/README.md`](tests/README.md).

## Wat draait er (stack kern)

| Component | Image | Host-poort | Intern adres | Opmerking |
|---|---|---|---|---|
| Open Zaak | `openzaak/open-zaak:1.29.0` | 8001 | `http://openzaak.local:8000` | Zaken, Catalogi, Besluiten, Documenten, Autorisaties API |
| Open Notificaties | `openzaak/open-notificaties:1.16.1` | 8002 | `http://opennotificaties.local:8000` | worker en celery-beat |
| Open Object | `maykinmedia/open-object:4.1.0` | 8003 | `http://openobject.local:8000` | Objecten en Objecttypen in een applicatie |
| Open Klant | `maykinmedia/open-klant:2.17.0` | 8004 | `http://openklant.local:8000` | Klantinteracties API |
| Open Product | `maykinmedia/open-product:1.8.0` | 8005 | `http://openproduct.local:8000` | met de Uniforme Productnamenlijst (UPL) |
| Referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | 8006 | `http://referentielijsten.local:8000` | tabel KANAAL voor Open Klant |
| VNG Selectielijst | `openzaak/vng-selectielijst:1.0.5` | 8007 | `http://selectielijst.local:8000` | selectielijst 2020 |
| BRP-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | 8010 | `http://brp-mock.local:80` | Haal Centraal BRP personen, RvIG-testpersonen |
| Keycloak | `keycloak/keycloak:26.4` | 8080 | `http://keycloak.local:8080` | realm `voorbeeldstad` = DigiD-simulatie |
| Notificatie-sink | (Open Zaak-image, eigen script) | 8090 | `http://notificatie-sink.local:8080` | abonnee die alle notificaties bewaart |
| Postgres/PostGIS | `postgis/postgis:17-3.5-alpine` | 55432 | `postgres:5432` | een database per component |
| Redis | `redis:8-alpine` | - | `redis:6379` | een database-index per component |

Poorten luisteren standaard alleen op `127.0.0.1`; zet `BIND_ADDRESS=0.0.0.0`
in `.env` om de demo op het netwerk beschikbaar te maken.

Beheer: elke Django-applicatie heeft `/admin/` met gebruiker `admin` en het
wachtwoord `ADMIN_PASSWORD` uit `.env`. Keycloak-beheer: `http://localhost:8080/admin/`.

### Interne hostnamen

De componenten praten met elkaar via hostnamen met een punt
(`openzaak.local` en zo verder), omdat Django geen URL's zonder punt in de
hostnaam accepteert. Seed- en rooktest draaien daarom in een hulpcontainer
binnen het docker-netwerk (`tools`, zie `stacks/basis/compose.yml`). Resources hebben
dus URL's als `http://openzaak.local:8000/zaken/api/v1/zaken/...`.

Let op bij Open Zaak vanaf de host: de autorisaties van applicaties met
rechten per zaaktype (zoals `burgerportaal`) zijn gebonden aan de hostnaam. Via
`http://localhost:8001` werkt het zoeken in zaken, maar geeft het detail van
een zaak, status of document 403. Gebruik vanaf de host de canonieke URL:

```bash
echo "127.0.0.1 openzaak.local" | sudo tee -a /etc/hosts
python3 tools/poort_doorsturen.py 8000 8001 &    # of PORT_OPENZAAK=8000 in .env
curl http://openzaak.local:8000/zaken/api/v1/...
```

Zie bevinding D1 in [`docs/openzaak-bevindingen.md`](docs/openzaak-bevindingen.md).
Voor de beheeraccount (`demogemeente-beheer`, alle rechten) maakt de
hostnaam niet uit.

## Koppelingen

```
            notificaties (ZGW-JWT)                 abonnement
 Open Zaak ----------------------> Open Notificaties ---------> notificatie-sink
 Open Object, Open Klant,      ^         |
 Open Product -----------------+         | autorisaties opvragen (ZGW-JWT)
                                         v
                                     Open Zaak (Autorisaties API)

 Open Zaak --(selectielijst)--> VNG Selectielijst
 Open Zaak --(zaakobject-URL's controleren, token)--> Open Object
 Open Klant --(kanaalcodes)--> Referentielijsten
 Open Product --(aanvraag_zaak_url)--> Open Zaak
```

- **ZGW-autorisaties.** Clients ondertekenen een JWT (HS256) met hun
  `client_id` en secret. De secrets staan in `.env`; de koppeling staat in
  `config/openzaak/data.yaml` en `config/opennotificaties/data.yaml`.
- **Leesclient voor portalen.** Client `burgerportaal` mag alleen lezen: `zaken.lezen`
  per zaaktype, `catalogi.lezen` en `documenten.lezen` per informatieobjecttype
  (tot en met zeer geheim). `seed/seed.py` zet deze autorisaties via de
  Autorisaties API, omdat de zaaktype-URL's pas na het seeden bestaan.
  Schrijven en de Autorisaties API geven 403 (dat test de rooktest ook).
  Voor Open Object en Open Klant is er een eigen token
  (`OPENOBJECT_PORTAAL_TOKEN`, alleen lezen, en `OPENKLANT_PORTAAL_TOKEN`). Een plug-in
  met een portaal of Mijn-API gebruikt deze client (zie `docs/PLUGINS.md`).
- **Notificaties.** Open Zaak, Open Object, Open Klant en Open Product
  publiceren naar Open Notificaties. Open Notificaties levert af aan de
  notificatie-sink (`http://localhost:8090/notificaties` toont wat er binnenkwam).
- **Objecten en Objecttypen.** Sinds Open Object 4.0 zitten die in een
  applicatie. De objecttypen hebben vaste UUID's (`config/openobject/data.yaml`);
  de JSON-schema's staan in `seed/data.py`.

## Clients, tokens en geheimen

Alle geheimen staan in `.env` (aangemaakt uit `.env.example`, nooit
committen). Overzicht:

| Wie | Soort | Variabelen in `.env` |
|---|---|---|
| Seed-scripts / beheer | ZGW-JWT, alle autorisaties | `ZGW_BEHEER_CLIENT_ID` (`demogemeente-beheer`), `ZGW_BEHEER_SECRET` |
| Portaal of Mijn-API (plug-in) | ZGW-JWT, alleen lezen | `ZGW_PORTAAL_CLIENT_ID` (`burgerportaal`), `ZGW_PORTAAL_SECRET` |
| Portaal of Mijn-API (plug-in) | Keycloak client credentials | client `burgerportaal`, `KEYCLOAK_PORTAAL_CLIENT_SECRET` |
| Portaal of Mijn-API (plug-in) | API-token Open Object / Open Klant | `OPENOBJECT_PORTAAL_TOKEN`, `OPENKLANT_PORTAAL_TOKEN` |
| Beheer | API-token Open Object / Open Klant / Open Product | `OPENOBJECT_BEHEER_TOKEN`, `OPENKLANT_BEHEER_TOKEN`, `OPENPRODUCT_BEHEER_TOKEN` |
| Componenten onderling | ZGW-JWT | `ZGW_OPENZAAK_SECRET`, `ZGW_OPENNOTIFICATIES_SECRET`, `ZGW_OPENOBJECT_SECRET`, `ZGW_OPENKLANT_SECRET`, `ZGW_OPENPRODUCT_SECRET` |
| Inwoners (DigiD-simulatie) | wachtwoord | `DIGID_SIM_WACHTWOORD` |

Voorbeeld: zaken van een inwoner opvragen met de leesclient, vanaf de host.

```bash
set -a; . ./.env; set +a
TOKEN=$(python3 scripts/lib/env.py zgw-jwt ZGW_PORTAAL_CLIENT_ID ZGW_PORTAAL_SECRET)
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept-Crs: EPSG:4326" \
  "http://openzaak.local:8000/zaken/api/v1/zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=999990627"
```

Inloggen als inwoner (DigiD-simulatie) en een token met claim `bsn` krijgen:

```bash
curl -s -d grant_type=password -d client_id=mijnservices -d username=999990627 \
  -d "password=$DIGID_SIM_WACHTWOORD" \
  http://localhost:8080/realms/voorbeeldstad/protocol/openid-connect/token
```

In de browser: client `mijnservices` (publiek, PKCE) met redirect naar
`http://localhost:*`. Het inlogscherm heet "DigiD-simulatie"; het is geen
echte DigiD.

## Plug-ins

Een plug-in voegt een component van een leverancier toe aan een stack: een compose-overlay,
optioneel eigen configuratie, en een manifest (`plugin.yaml`) met de naam, de leverancier,
welke burgerkanalen en Mijn-API's het component aanbiedt en hoe je inlogt. DemoStack test
het daarna met dezelfde suite: gezondheid, isolatie tussen burgers en de
VNG-aansluitprofielen voor de Mijn-API's.

```bash
scripts/stack.sh up kern --plugin ../leverancier/demostack
scripts/stack.sh test kern          # results/kern+<naam>.md
scripts/stack.sh down kern
```

Het contract, met een voorbeeld en de clients die een stack een plug-in aanbiedt, staat in
[`docs/PLUGINS.md`](docs/PLUGINS.md). Er zijn geen plug-ins ingebouwd.

Achter een proxy met TLS-inspectie kan een Docker-build die pakketten ophaalt (pnpm, pip,
Gradle) het register niet bereiken. Zie "Images ophalen en bouwen" in
[`stacks/README.md`](stacks/README.md).

## Testdata

Alle data is fictief of open:

- **Personen:** de RvIG-testpersonen uit
  [BRP-API/Haal-Centraal-BRP-bevragen](https://github.com/BRP-API/Haal-Centraal-BRP-bevragen)
  (`test-data/personen-mock/test-data.json`, EUPL-1.2, commit `e028a8e`),
  gefilterd op BSN's in de officiele testreeks 999990000 tot en met 999999999
  die de elfproef halen (788 personen, `config/brp/test-data.json`, filter:
  `scripts/lib/filter_brp_testdata.py`). Hun adressen liggen in
  's-Gravenhage; in de demo speelt dat de rol van Voorbeeldstad.
- **Gemeente:** "Gemeente Voorbeeldstad", fictief RSIN `999990007`.
- **Medewerkers, kentekens, e-mailadressen:** verzonnen (`*.example`).
- **UPL:** kopie van de Uniforme Productnamenlijst (`config/openproduct/UPL-actueel.csv`).
- **Selectielijst:** selectielijst 2020 uit het image, aangevuld met de
  generieke resultaattypeomschrijvingen (`config/selectielijst/`).

| BSN | Naam | Zaken | Overig |
|---|---|---|---|
| 999990627 | Stephan Janssen | VBS-2026-000101 omgevingsvergunning dakkapel (in behandeling), VBS-2026-000102 melding losliggende trottoirtegels (afgehandeld) | klantcontact (telefoon), meldingsobject |
| 999997609 | Eleonora de Crooy | VBS-2026-000103 parkeervergunning (afgehandeld), VBS-2026-000104 Wmo traplift (gesprek gepland) | parkeervergunning in Open Object en Open Product, klantcontact (balie) |
| 999993409 | Thea Kouwenhoven | VBS-2026-000105 Wmo huishoudelijke ondersteuning (verstrekt) | klantcontact (e-mail) |
| 999995406 | Paula Prins | VBS-2026-000106 melding zwerfafval (ontvangen) | meldingsobject, klantcontact (webformulier) |
| 999991991 | Jeroen Altena | VBS-2026-000107 parkeervergunning (in behandeling), VBS-2026-000108 kapvergunning (geweigerd) | klantcontact (telefoon) |

De catalogus "Zaaktypecatalogus Gemeente Voorbeeldstad" (domein `VBSTD`)
bevat vier gepubliceerde zaaktypen: Omgevingsvergunning aanvragen, Melding
openbare ruimte, Wmo-maatwerkvoorziening aanvragen en Parkeervergunning
bewoners aanvragen. Elk heeft statustypen, roltypen (aanvrager,
behandelaar), resultaattypen gekoppeld aan de selectielijst en
documenttypen. Elke zaak heeft rollen, statussen, PDF-documenten en waar
dat past een resultaat en een object.

Alle andere 788 testpersonen zijn ook op te vragen bij de BRP-mock.

## Footprint (gemeten op 2026-10-07)

Gemeten met `docker stats` na een verse start en de rooktest (variant 1), op een
machine met 4 CPU's en 16 GB geheugen. Opbouw vanaf nul (lege volumes, images
al aanwezig) inclusief seed en rooktest: ruim 3 minuten.

| Container | Geheugen |
|---|---|
| keycloak | 587 MiB |
| openzaak + openzaak-celery | 435 + 369 MiB |
| openproduct + celery | 320 + 264 MiB |
| openobject + celery | 272 + 233 MiB |
| opennotificaties + celery + celery-beat | 254 + 124 + 127 MiB |
| openklant + celery | 199 + 230 MiB |
| referentielijsten | 251 MiB |
| brp-mock | 176 MiB |
| postgres | 156 MiB |
| selectielijst | 99 MiB |
| notificatie-sink, redis | 11 + 7 MiB |
| **Totaal** | **ongeveer 4,9 GiB** |

Images samen ongeveer 8,3 GB op schijf (grootste: vng-selectielijst 1,5 GB,
open-object 1,1 GB, open-zaak 1,1 GB). De database is na het seeden 207 MB.
Het geheugen per component regel je met `UWSGI_PROCESSES`,
`UWSGI_THREADS` en `CELERY_WORKER_CONCURRENCY` in `.env`.

## Mappen

```
stacks/             basis (infra) en per stack compose.yml, stack.env, stack.yaml en README.md
config/             setup-configuration per component, Keycloak-realm, BRP-data, fixtures
seed/               seed.py (idempotent), data.py (de testdata), lib.py (API-clients)
tests/              gedeelde testsuite: run.py, rapport.py, checks/, respect/
results/            testrapporten per stack (<naam>.json, <naam>.md); raw/ niet in git
scripts/            stack.sh (up, seed, test, down, list, pull, opruimen; --plugin)
aansluitprofielen/  ZGW-aansluitprofiel (Arazzo) met het Open Zaak-schema
vendor/vng-api-lab/ ongewijzigde kopie van de Mijn-API-specs en aansluitprofielen (VNG API Lab)
docs/               STACKS.md (vergelijking), PLUGINS.md (plug-in-contract),
                    openzaak-bevindingen.md, VARIANTEN.md, landschap/, screenshots/<stack>/
tools/              notificatie-sink, Keycloak-realmgenerator, poort_doorsturen.py
```

## Bekende beperkingen

- De BRP-mock (`iswish/...gba-mock`) negeert het veld `fields` en geeft altijd
  de hele persoon terug. Het officiele image `ghcr.io/brp-api/personen-mock`
  kon in de bouwomgeving niet worden opgehaald; het is een directe vervanger.
- Open Notificaties 1.16 levert notificaties in batches af (celery-beat,
  hier elke 5 seconden), dus een notificatie komt na enkele seconden binnen.
- Objecttypen 3.4.2 en Objectenregister 4.1.0 uit de VCG-lijst zijn sinds
  Open Object 4.0 een applicatie; een losse Objecttypen-API is niet nodig.
- Admin-login via OIDC (Keycloak) is nog niet ingesteld; gebruik `admin`.
