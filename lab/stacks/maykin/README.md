# Stack maykin: het Maykin-landschap

Wat een gemeente draait die "alles van Maykin" kiest: de kern (Open Zaak, Open
Notificaties, Open Object, Open Klant, Open Product, Referentielijsten, Selectielijst)
plus Open VTB voor taken, Open Formulieren voor e-formulieren en Open Inwoner als
burgerportaal. Open VTB is ook de takenbron voor een portaal of Mijn-API die als plug-in
meedraait (token `OPENVTB_PORTAAL_TOKEN`, gebruiker `burgerportaal`).

```bash
scripts/stack.sh up maykin      # starten, wachten tot gezond, testdata laden
scripts/stack.sh test maykin    # results/maykin.json en results/maykin.md
scripts/stack.sh down maykin
```

Alles wordt automatisch geconfigureerd: setup-configuration (YAML), omgevingsvariabelen
en een paar idempotente scripts voor wat setup-configuration in deze versies nog niet
kan. Er is geen handwerk in een admin nodig.

## Componenten

| Component | Image | Host-poort | Intern adres | Status |
|---|---|---|---|---|
| kern (7 registers) | zie `stacks/kern/README.md` | 8001 tot 8007 | `*.local:8000` | draait en getest |
| Open VTB 0.2.0 (Verzoeken, Taken, Berichten) | `maykinmedia/open-vtb:0.2.0` | 8101 | `http://openvtb.local:8000` | draait en getest |
| Open Formulieren 4.0.1 (SDK 4.0.2 meegebundeld) | `openformulieren/open-forms:4.0.1` | 8102 | `http://openformulieren.local:8000` | draait en getest |
| Open Inwoner 2.4.5 | `maykinmedia/open-inwoner:2.4.5` | 8103 | `http://openinwoner.local:8000` | draait en getest |
| Elasticsearch 9.0.3 (zoeken in Open Inwoner) | `elasticsearch:9.0.3` | geen | `http://elasticsearch.local:9200` | draait (gezondheid) |
| BRP-vertaler | `openzaak/open-zaak:1.29.0` met `tools/brp_vertaler.py` | geen | `http://brp-api.local:8080` | draait en getest |
| Keycloak-clients (init) | `keycloak/keycloak:26.4.7` | geen | | eenmalig, exit 0 |
| Open Archiefbeheer | | | | niet in deze stack, zie hieronder |
| Open Beheer | | | | niet in deze stack, zie hieronder |
| Officiele BRP Personen-mock | `ghcr.io/brp-api/personen-mock` | | | niet draaibaar hier, zie hieronder |

Celery-workers: `openvtb-celery`, `openformulieren-celery`, `openformulieren-celery-beat`,
`openinwoner-celery`. Elasticsearch komt van Docker Hub (`elasticsearch:9.0.3`) omdat
`docker.elastic.co` in de bouwomgeving geblokkeerd was. Het is hetzelfde image.

Beheerders: `admin` met `ADMIN_PASSWORD` uit `.env` in Open VTB en Open Formulieren, en
`admin@voorbeeldstad.example` met hetzelfde wachtwoord in Open Inwoner.

## Koppelingen

```
            DigiD-simulatie (Keycloak, realm voorbeeldstad)
              |  clients openinwoner en openformulieren, claims bsn en loa
              v
 burger --> Open Inwoner ----------> Open Zaak (zaken tot vertrouwelijk, documenten tot zaakvertrouwelijk)
    |          |  \----------------> Open Klant (Mijn vragen: klantcontacten, kanaal webformulier)
    |          |   \---------------> Open Object (objecttype "Externe taak": Mijn taken)
    |          |    \--------------> BRP-vertaler --> BRP-mock (Mijn profiel)
    |          '-- link naar formulier
    v
 Open Formulieren --- prefill -----> BRP-vertaler --> BRP-mock (naam)
         '--- registratie ---------> Open Zaak (zaak VBS-MOR "Melding openbare ruimte" plus PDF)

 Open VTB --------- notificaties --> Open Notificaties (kanaal taken, cloud events)
```

- **Inloggen.** `config/keycloak/extra-clients.sh` maakt in Keycloak de clients
  `openinwoner` en `openformulieren` met de mappers `bsn` en `loa`. Beide portalen
  gebruiken het OIDC-DigiD-plugin met expliciete endpoints: de browser gaat naar
  `localhost:8080`, de server praat met `keycloak.local:8080`. Het uitlog-endpoint van
  Open Formulieren is intern (`keycloak.local`), want Open Formulieren roept het bij het
  versturen van een inzending vanaf de server aan.
- **ZGW.** Open Zaak kent drie extra applicaties (`config/openzaak/stack-maykin.yaml`,
  autorisaties in `stacks/maykin/seed.py`): `open-formulieren` (zaken aanmaken op VBS-MOR,
  documenten Melding en Foto), `open-inwoner` (lezen, zaken tot vertrouwelijk, documenten
  tot zaakvertrouwelijk) en `open-vtb` (notificaties).
- **Taken.** De gemeente zet een taak op twee plekken, zoals een Maykin-gemeente nu zou
  doen: als "Externe taak" in Open Object (dat leest Open Inwoner 2.4) en als taak in
  Open VTB (Taken API, voor een portaal als plug-in). Elke taak verwijst naar het zaaknummer en de BSN.
- **BRP.** De BRP-mock van de basis geeft de GBA-variant terug (datums als JJJJMMDD,
  platte verblijfplaats). Open Inwoner valideert het officiele formaat van BRP API
  Personen 2 en weigert dat. `tools/brp_vertaler.py` zet het antwoord om; Open
  Formulieren gebruikt hem ook.

## Configuratie

| Waar | Wat |
|---|---|
| `stacks/maykin/compose.yml` | services, plus extra YAML voor de init-containers van de kern |
| `stacks/maykin/env.example` | geheimen (`__GENEREER__`), `up` vult `.env` aan |
| `config/openvtb/data.yaml`, `tokens.py` | notificaties via setup-configuration; superuser en API-tokens met een script (0.2.0 heeft daar geen stap voor) |
| `config/openformulieren/data.yaml`, `configureer.py` | OIDC DigiD, ZGW-groep, Objecten-groep en services via setup-configuration; superuser, API-token, Haal Centraal-prefill, catalogus en algemene instellingen met een script |
| `config/openinwoner/data.yaml`, `configureer.py` | OIDC DigiD, services, ZGW-groep en Open Klant 2 via setup-configuration; superuser, siteconfiguratie, Haal Centraal, Objecten API, actor voor Mijn vragen en CMS-pagina's met een script |
| `config/{openzaak,opennotificaties,openobject,openklant}/stack-maykin.yaml` | extra applicaties, tokens en het objecttype "Externe taak" in de kern |
| `config/keycloak/extra-clients.sh` | Keycloak-clients van de portalen |
| `stacks/maykin/seed.py` | testdata, idempotent |

Databases (met postgis en pg_trgm) komen uit `DB_EXTRA` in `stack.env`, Redis gebruikt
databases 12 tot en met 17.

## Testdata (Voorbeeldstad)

Bovenop de gedeelde seed (zaken VBS-2026-000101 tot en met -000105 voor burgers A, B, C):

| Burger | Taken (Open Object en Open VTB) | Vragen (Open Klant) |
|---|---|---|
| A, 999990627, Stephan Janssen | aanvullende tekening dakkapel (101), leges betalen 131,75 euro (101), vragenlijst melding (102) | "Wanneer wordt de grofvuilpas verstuurd?" |
| B, 999997609, Eleonora de Crooy | medische verklaring traplift (104) | "Kan de traplift ook in een huurwoning?" |

Open Formulieren krijgt het formulier `melding-openbare-ruimte`: DigiD verplicht, naam
uit de BRP, registratie als zaak VBS-MOR in Open Zaak met de PDF van de inzending.

## Testresultaat

Zonder plug-ins: **62 geslaagd, 7 gefaald (alle 7 bekend), 6 overgeslagen**. Afgeleid van
de laatste run vanaf lege volumes (8 oktober 2026); zie `results/maykin.md` en
`results/maykin.json`.

| Categorie | Geslaagd | Gefaald | Overgeslagen |
|---|---|---|---|
| gezondheid | 16 | 0 | 2 (Open Archiefbeheer, Open Beheer: gepland) |
| rook | 30 | 0 | 3 (infra) |
| zgw | 3 | 7 (bekend, uit de kern) | 0 |
| burger-isolatie | 13 | 0 | 0 |
| mijn-apis | 0 | 0 | 1 (geen plug-in met een Mijn-API) |

De twee ZGW-aansluitprofielen falen bekend (zie `stacks/kern/README.md`). Met een plug-in
die MijnTaken next aanbiedt, draait `mijn-apis` ook het MijnTaken-profiel op Open VTB.

Rooktests van deze stack (`tests.py`): inloggen via DigiD en Mijn aanvragen, zaakdetail
met statushistorie en PDF-download, Mijn taken, Mijn profiel uit de BRP en Mijn vragen in
Open Inwoner; formulier ophalen en een volledige melding (DigiD, prefill, versturen, zaak
in Open Zaak) in Open Formulieren; taken per burger, segmentfilter en tokencontrole in
Open VTB; het formaat van de BRP-vertaler.

### Isolatie tussen burgers

Getest met burgers A en B, ingelogd via de DigiD-simulatie.

- **Open Inwoner.** A ziet alleen eigen zaken (101, 102), B alleen 103 en 104. De
  zaakdetail-URL's en een document van B geven A een 404. Taken, vragen en profiel van A
  bevatten niets van B. Zonder login: 302 naar de loginpagina.
- **Open Formulieren.** De inzending van B geeft A een 404, de stap van B een 403. Prefill
  geeft alleen de eigen BRP-gegevens. Een inzending starten zonder login: 403.
- **Open VTB.** Schermt zelf niet af per burger (zie bevindingen). Een Mijn-API op Open
  VTB moet dat doen; met een plug-in test `mijn-apis/<id>/mijntaken/burger-a-haalt-taak-van-burger-b`
  dat.

Schermafdrukken (Playwright, Chromium): `docs/screenshots/maykin/`, gemaakt met
`stacks/maykin/screenshots.mjs`. Daarin ook A die de zaken van B opent (404).

## Bevindingen

- **Open VTB 0.2.0 kent geen afscherming per afnemer.** Elk geldig token leest alle taken
  van alle burgers; filteren op `isToegewezenAan` gebeurt door de afnemer. Het token is dus
  net zo gevoelig als een beheertoken.
- **Open Inwoner 2.4.5 haalt alle externe taken op en filtert zelf op BSN.** Het token
  van Open Inwoner in Open Object moet daarom alle taken van het objecttype kunnen lezen.
  De isolatie hangt af van het filter in Open Inwoner, niet van de bron.
- **Open Inwoner toont alleen klantcontacten met een nummer** en alleen op het ingestelde
  kanaal. Open Klant accepteert als nummer alleen cijfers (maximaal 10).
- **Open Inwoner vraagt om het officiele BRP-formaat**; de GBA-variant van de mock wordt
  geweigerd. Vandaar de BRP-vertaler.
- **Zaaktype Wmo is vertrouwelijk.** Met een maximum van zaakvertrouwelijk ziet B zaak
  104 niet in Open Inwoner (wel via de leesclient `burgerportaal`). Daarom staat de applicatie van Open Inwoner op
  vertrouwelijk.
- **Bij de eerste login vraagt Open Inwoner een e-mailadres** (registratiestap).
- **Een afgesloten zaak** toont in Open Inwoner bij de laatste status nog "Niet voltooid"
  in de tijdlijn, terwijl het resultaat wel klopt.
- **Setup-configuration dekt nog niet alles.** Open Formulieren 4.0 heeft geen stappen
  voor prefill, catalogus en tokens; Open Inwoner 2.4.5 niet voor CMS, Haal Centraal,
  Objecten API en siteconfiguratie (die staan op master); Open VTB 0.2.0 niet voor tokens.
  Daarvoor zijn de scripts in `config/<component>/`.
- **Registratieplugins van Open Formulieren** (`/api/v2/registration/plugins/...`) werken
  alleen met een sessie, niet met een token. De seed logt daarvoor in op de admin.
- **Open Object 4** levert Objecten en Objecttypen onder dezelfde root. zgw-consumers
  staat geen twee services met dezelfde `api_root` toe, dus Open Formulieren en Open
  Inwoner gebruiken een service voor beide.
- **Objecten aanmaken** vraagt de header `Content-Crs: EPSG:4326`, ook zonder geometrie.

## Voetafdruk

Gemeten op de bouwmachine (15 GB RAM, 4 CPU's), stack vanaf lege volumes:

| | |
|---|---|
| Starttijd | 327 s voor `up` tot en met seed (alle services gezond plus gedeelde en eigen seed); images lokaal aanwezig |
| Geheugen | 7,5 GiB voor 29 containers (`docker stats` een minuut na het starten). Grootste: Elasticsearch 867 MiB, Keycloak 552 MiB, Open Formulieren 522 MiB, Open Zaak 432 MiB, Open Formulieren-celery 430 MiB, Open Inwoner-celery 403 MiB, Open Inwoner 375 MiB, Open VTB-celery 350 MiB, Open VTB 273 MiB |
| Images | 14,2 GB voor alle images van de stack; daarvan nieuw ten opzichte van de kern: Elasticsearch 2,08 GB, Open Formulieren 1,84 GB, Open Inwoner 1,58 GB, Open VTB 0,96 GB |
| Volumes | 0,33 GB na seed en test, vrijwel alles Postgres |

De hele stack past in een keer; opsplitsen was niet nodig.

## Niet in deze stack, of niet draaibaar

- **Open Archiefbeheer en Open Beheer.** Ook Maykin-producten, maar ze staan in stack
  `dimpact` en `vcg`. Hier alleen als "gepland" in `stack.yaml`. Nodig: een database,
  setup-configuration op Open Zaak en een rooktest.
- **Officiele BRP Personen-mock** (`ghcr.io/brp-api/personen-mock`). Niet draaibaar in de
  bouwomgeving: de proxy blokkeert de blobs van ghcr.io (`pkg-containers.githubusercontent.com`).
  Nodig: toegang tot ghcr.io; dan kan de BRP-vertaler weg en wijzen de services
  `brp-personen` naar de mock.
- **eHerkenning, machtigen en betalen.** De betaaltaak staat in Open VTB en Open Object,
  maar er is geen betaalprovider gekoppeld. Nodig: een gesimuleerde PSP (bijvoorbeeld de
  demo-plugin van Open Formulieren) en een eHerkenning-simulatie in Keycloak.
- **Virusscan (ClamAV) en e-mail.** De virusscan staat uit in Open Inwoner en is in Open
  Formulieren niet ingesteld; e-mail gaat nergens heen (`EMAIL_HOST: localhost`). Nodig:
  een ClamAV-container en een mailcatcher.
