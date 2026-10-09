# Stack g4: Platform Dienstverlening van de G4

Een gemeente die de keuze van het Platform Dienstverlening (G4) volgt: NL Portal als
burgerportaal, Valtimo/GZAC als zaakafhandeling, IKO voor het klantbeeld van
medewerkers, Open Formulieren voor e-formulieren en Open VTB voor taken, op de registers
van de kern (Open Zaak, Open Notificaties, Open Object, Open Klant).

```bash
scripts/stack.sh up g4      # images bouwen die ontbreken, starten, wachten, testdata laden
scripts/stack.sh test g4    # results/g4.json en results/g4.md
scripts/stack.sh down g4
```

Alles wordt automatisch geconfigureerd: setup-configuration (YAML) voor de Django-apps,
een realm-script voor Keycloak, autodeploy-bestanden voor GZAC, een Flyway-migratie voor
IKO, omgevingsvariabelen en idempotente seedscripts. Er is geen handwerk in een admin
nodig.

**Status: werkt.** Alle componenten draaien en zijn getest. Eén bekende fout: een
portaaltaak uit GZAC verschijnt niet in NL Portal (zie "Bevindingen").

## Componenten

| Component | Image | Host-poort | Intern adres | Status |
|---|---|---|---|---|
| Open Zaak, Open Notificaties, Open Object, Open Klant, Referentielijsten, Selectielijst | kern, zie `stacks/kern/README.md` | | | draait en getest |
| Open VTB 0.2.0 | `maykinmedia/open-vtb:0.2.0` | 8201 | `openvtb.local:8000` | draait en getest |
| Open Formulieren 3.5.8 | `openformulieren/open-forms:3.5.8` | 8202 | `openformulieren.local:8000` | draait en getest |
| NL Portal backend 3.0.4 | `demogemeente/nlportal-backend:3.0.4` (gebouwd) | 8204 | `nlportal-backend.local:8000` | draait en getest |
| NL Portal frontend 3.0.3 | `demogemeente/nlportal-frontend:3.0.3` (gebouwd) | 8203 | `nlportal.local:8080` | draait en getest |
| Valtimo/GZAC 13.48.0 backend | `ritense/gzac-backend:13.48.0` | 8206 | `gzac-backend.local:8000` | draait en getest |
| Valtimo/GZAC 13.48.0 frontend | `ritense/gzac-frontend:13.48.0` | 8205 | `gzac.local:8080` | draait en getest |
| IKO 1.5.1 | `demogemeente/iko:1.5.1` (gebouwd) | 8207 | `iko.local:8000`, beheer `:9090` | draait en getest |
| BRP-vertaler | `openzaak/open-zaak:1.29.0` met `tools/brp_vertaler.py` | geen | `brp-api.local:8080` | draait en getest |
| Keycloak 26.4.7, realms `voorbeeldstad` en `g4` | `keycloak/keycloak:26.4.7` | 8080 | `keycloak.local:8080` | draait en getest |
| Officiële BRP-personen-mock 2.7.0 | | | | niet draaibaar, zie hieronder |

Open Product en Open Inwoner horen niet bij deze keuze (`zonder: [openproduct]`, en
Open Inwoner staat in `compose.yml` uit). Open VTB, Open Formulieren en de BRP-vertaler
komen uit de compose van stack maykin, met eigen poorten.

**Zelf gebouwd.** NL Portal heeft geen gepubliceerd image: het is een set bibliotheken
(backend in Kotlin, frontend in React) plus een voorbeeld-app. IKO staat alleen op
ghcr.io, dat in de bouwomgeving geblokkeerd is. `stacks/g4/bouw.sh` bouwt alle drie uit
de broncode op de releasetag (`bouw/jvm.Dockerfile` voor backend en IKO, Gradle met JDK
21; `bouw/nlportal-frontend.Dockerfile` met pnpm en nginx). `scripts/stack.sh up` roept
het aan en bouwt alleen wat ontbreekt; de broncode komt in `.bron/` (niet in git).
Achter een proxy met TLS-inspectie: `EXTRA_CA_CERT=/pad/naar/ca-bundle.crt`.

**Keycloak en localhost.** Keycloak geeft altijd de issuer `http://localhost:8080/...`
(zoals de browser hem ziet). Spring Boot-apps in een container (NL Portal, GZAC, IKO)
halen bij het starten de OIDC-configuratie van die issuer op en controleren hem in elk
token. Daarom draait elke Spring-app in het netwerk van een kleine "-net"-container
(`tools/keycloak_doorgifte.py`) die `127.0.0.1:8080` doorstuurt naar `keycloak.local:8080`.

### Niet draaibaar

| Component | Waarom niet | Wat nodig is |
|---|---|---|
| BRP-personen-mock 2.7.0 (officieel, `ghcr.io/brp-api/personen-mock`) | ghcr.io is hier geblokkeerd (403 op de blob-host) | toegang tot ghcr.io; tot die tijd vervangt de iswish-mock met `tools/brp_vertaler.py` hem (zelfde API Personen 2) |

## Gebruikers

Beheerders van de Django-componenten: `admin` met `ADMIN_PASSWORD` uit `.env`.
Burgers loggen in via de DigiD-simulatie (realm `voorbeeldstad`, BSN als
gebruikersnaam, `DIGID_SIM_WACHTWOORD`). Medewerkers loggen in via realm `g4` met
`MEDEWERKER_WACHTWOORD`:

| Gebruiker | Wie (fictief) | Rollen |
|---|---|---|
| `behandelaar.bakker` | Sanne Bakker, behandelaar vergunningen | GZAC `ROLE_USER`, IKO `ROLE_KLANTBEELD` |
| `beheer.yilmaz` | Deniz Yilmaz, functioneel beheer | GZAC `ROLE_USER`, `ROLE_ADMIN`, `ROLE_DEVELOPER`; IKO `ROLE_ADMIN`, `ROLE_KLANTBEELD` |

| Burger | BSN | Wat hij heeft |
|---|---|---|
| A, Stephan Janssen | 999990627 | zaken VBS-2026-000101 en -000102, twee taken, een bericht |
| B, Eleonora de Crooy | 999997609 | zaken VBS-2026-000103 en -000104, een taak, een bericht |
| D, Jeroen Altena | 999991991 | aanvraag parkeervergunning die via GZAC loopt (zaak ZAAK-2026-...), plus de seedzaken 107 en 108 |

## Koppelingen

```
          DigiD-simulatie (realm voorbeeldstad)            medewerkers (realm g4)
                |                                               |
 burger --> NL Portal frontend --GraphQL--> NL Portal backend   +--> GZAC frontend --> GZAC backend
                                  |  token exchange (nlportal-m2m)       |  plugins:
                                  +--> Open Zaak (zaken, documenten)     +--> Open Zaak (zaak, rol, status)
                                  +--> Open Object (taken v2, berichten) +--> Open Object (portaaltaak)
                                  +--> Open Klant, BRP-vertaler          +--> Open Notificaties
    |
    +--> Open Formulieren -- prefill --> BRP-vertaler; registratie --> Open Zaak
                                                        IKO (klantbeeld) --> Open Zaak (zaken per BSN)
```

- **NL Portal.** De frontend logt in met de publieke client `nlportal` (authorization
  code). Het backend wisselt elk burgertoken in bij Keycloak (token exchange, client
  `nlportal-m2m`) en leest het BSN uit het nieuwe token. Het praat met Open Zaak als
  ZGW-client `nl-portal` (lezen, zaken tot en met vertrouwelijk, documenten tot en met
  zaakvertrouwelijk), met Open Object via een token op de objecttypen Taak (c1) en
  Bericht (c2), met Open Klant en met de BRP-vertaler. Configuratie:
  `config/nlportal/application.yml`.
- **GZAC.** De zaakdefinitie `parkeervergunning` 1.0.0 (`config/gzac/config/case/`) wordt
  bij het starten automatisch uitgerold, met plugins voor Open Zaak, Catalogi,
  Documenten, Objecten, Objecttypen, Open Notificaties en Portaaltaak
  (`config/gzac/config/global/plugin/`). Het proces `behandelen-parkeervergunning`
  koppelt de aanvrager als initiator, zet de status Ontvangen, maakt een portaaltaak
  "Kentekenbewijs aanleveren" voor de burger en, parallel, de taak "Aanvraag beoordelen"
  voor de behandelaar met status In behandeling; na de beoordeling volgt Afgehandeld.
- **IKO.** Connector `openzaak` met endpoints `zaak_list` en `zaak_read`, instantie
  `voorbeeldstad` (ZGW-client `iko`, alleen lezen) en profiel `zaken-van-burger`:
  `GET /aggregated-data-profiles/zaken-van-burger?id=<bsn>` met een token van client `iko`
  en rol `ROLE_KLANTBEELD`.
- **Open Formulieren en Open VTB.** Zoals in stack maykin: formulier "Melding openbare
  ruimte" met DigiD en BRP-prefill, registratie als zaak in Open Zaak; taken in Open VTB
  (Taken API, ook bruikbaar voor een plug-in met MijnTaken next).

## Configuratie

| Waar | Wat |
|---|---|
| `stacks/g4/compose.yml` | services, de "-net"-containers, init-containers, aanvullingen op kern en maykin |
| `stacks/g4/stack.env` | versies, extra databases, hostpoorten 8201 tot en met 8207 |
| `stacks/g4/env.example` | geheimen (`__GENEREER__`), `up` vult `.env` aan |
| `stacks/g4/bouw.sh`, `bouw/` | NL Portal (backend en frontend) en IKO uit broncode; sleutels voor IKO en GZAC in `.env` |
| `config/keycloak-g4/` | realm `g4` (clients `valtimo-console`, `valtimo-user-m2m-client`, `iko`, rollen, medewerkers) en de clients `nlportal` en `nlportal-m2m` in realm `voorbeeldstad` |
| `config/nlportal/application.yml` | NL Portal backend: ZGW, Objecten, Open Klant, BRP, objecttypen, uitgeschakelde modules |
| `config/gzac/config/` | GZAC-autodeploy: plugins, rollen, rechten, objectbeheer, zaakdefinitie met BPMN, formulier, tabbladen, proceskoppelingen en zaaktypekoppeling |
| `config/gzac/zaaktypen.py` | init-container `gzac-zaaktypen`: zaaktype-URL's als Spring-properties voor GZAC |
| `config/gzac/frontend-nginx.conf` | GZAC-frontend: `/api` naar het backend |
| `config/iko/inrichting.py` | init-container `iko-inrichting`: connector, instantie (versleuteld), endpoints, rollen en profiel als Flyway-migratie |
| `config/{openzaak,opennotificaties,openobject,openklant}/stack-g4.yaml` | extra applicaties, tokens en objecttypen in de kern |
| `stacks/g4/seed.py` | testdata (idempotent): autorisaties, taken en berichten voor NL Portal, alles van maykin, en de GZAC-aanvraag van burger D |
| `stacks/g4/tests.py`, `screenshots.mjs` | rooktests en isolatietype `nlportal`; screenshots |

Databases komen uit `DB_EXTRA` in `stack.env` (`nlportal`, `gzac`, `iko` erbij); Redis
gebruikt databases 12 tot en met 18.

## Testresultaten

Zonder plug-ins: **73 geslaagd, 8 gefaald (alle 8 bekend), 5 overgeslagen**. Afgeleid van
`scripts/stack.sh test g4` op een schone start (lege volumes, 8 oktober 2026); zie
`results/g4.md`.

| Categorie | Geslaagd | Gefaald (bekend) | Overgeslagen |
|---|---|---|---|
| gezondheid | 17 | 0 | 1 (officiële BRP-mock, niet draaibaar) |
| rook | 39 | 1 (1) | 3 (infra) |
| zgw | 3 | 7 (7) | 0 |
| burger-isolatie | 14 | 0 | 0 |
| mijn-apis | 0 | 0 | 1 (geen plug-in met een Mijn-API) |

Per component: NL Portal 17 geslaagd en 1 bekend gefaald, GZAC 6, IKO 4, Open
Formulieren 8, Open VTB 4. De 7 bekende ZGW-fouten zijn die van de kern (Open Zaak 1.29
tegen het aansluitprofiel).

### Isolatie in NL Portal

Burger A en burger B loggen allebei in via de DigiD-simulatie; A probeert de gegevens van
B te zien. Alles wordt geweigerd:

- de lijsten van A (zaken, taken, berichten) bevatten niets van B;
- filteren op het zaaknummer van B geeft niets;
- de zaak, de taak en het bericht van B openen geeft een fout ("Access denied to this
  zaak", "Access denied to this taak", "User is not authorized for this Bericht");
- een document van B downloaden geeft 401;
- zonder token geeft GraphQL geen data (fout "No Authentication") en de download 401;
- een geldig token van een medewerker (realm `g4`) geeft 401.

NL Portal controleert bij elke zaak, taak, bericht en document of het BSN uit het
ingewisselde token erbij hoort. Een fout geeft het als GraphQL-fout met HTTP 200, niet als
HTTP-status. De screenshot `nlportal-burger-b-7-probeert-zaak-van-a.png` laat zien wat B
in de browser krijgt: "Er ging iets niet goed".

Ook in Open Formulieren (isolatietype van stack maykin) is de isolatie getest en in orde. IKO weigert zonder token, met een burgertoken en met een token
zonder rol `ROLE_KLANTBEELD` (alle drie 401).

## Bevindingen

1. **Portaaltaak van GZAC niet in NL Portal (bekende fout).** De core-plugin
   Portaaltaak van GZAC 13.48 schrijft taken in het oude formaat (taak v1: `title`,
   `identificatie`, `formulier`, `verwerker_taak_id`). NL Portal 3.0 leest alleen taak v2
   (`titel`, `soort`, `koppeling`, `portaalformulier`). De taak staat daarom wel in Open
   Object (objecttype Portaaltaak, c3) en in GZAC, maar niet in Mijn taken. De taken die
   NL Portal wel toont, maakt de seed rechtstreeks in v2-formaat aan (objecttype Taak, c1).
2. **Token exchange.** NL Portal 3.0.4 wisselt tokens in zonder `subject_token_type`. De
   standaard token exchange (v2) van Keycloak 26 eist die parameter. De stack zet daarom
   de oudere variant aan (`KC_FEATURES=token-exchange`, preview). Bij een upgrade van
   Keycloak of NL Portal opnieuw bekijken.
3. **GZAC: zaakdefinities zijn definitief.** Buiten de profielen dev en test accepteert
   GZAC alleen definitieve zaakdefinities (`"final": true`), en die zijn daarna niet meer
   via de API aan te passen. De URL's van zaaktype, roltype en statustypen moeten dus
   vóór de start bekend zijn. De init-container `gzac-zaaktypen` maakt de zaaktypen aan
   en geeft de URL's als Spring-properties door; de autodeploy-bestanden verwijzen ernaar
   met `${GZAC_...}`.
4. **IKO-inrichting.** Connectoren en profielen staan in de database van IKO, met de
   configuratie versleuteld (AES-GCM, `IKO_CRYPTO_KEY`). Er is geen import. Deze stack
   gebruikt het patroon van IKO's eigen e2e-seed: een Flyway-migratie uit een extra map
   (`SPRING_FLYWAY_LOCATIONS`), met placeholders uit (`SPRING_FLYWAY_PLACEHOLDER_REPLACEMENT=false`)
   omdat Camel-routes `${...}` bevatten.
5. **IKO-beheer laadt opmaak van internet.** De beheer-UI haalt htmx en Carbon van
   cdn.jsdelivr.net, unpkg.com en s81c.com. Zonder die toegang werkt de UI, maar zonder
   opmaak (zie `iko-1-profielen.png`).
6. **Testburger D.** De gedeelde testsuite verwacht dat A, B en C precies hun seedzaken
   hebben. Een extra zaak voor A breekt de vaste verwachtingen van de suite (onder meer de
   datacontroles van `mijn-apis`); de GZAC-aanvraag hoort daarom bij burger D.

## Footprint

Gemeten op 2026-10-08 vanaf lege volumes, images lokaal aanwezig, machine 15 GB RAM en
4 CPU. De stack past in één keer; draaien in twee helften is niet nodig.

| | |
|---|---|
| Start (`up` tot en met seed) | 330 s |
| RAM na start / na de testsuite | 7,7 GB / 8,2 GB (32 containers) |
| Grootste verbruikers | GZAC-backend 1,4 GB, Keycloak 0,6 GB, Open Formulieren 0,55 GB, IKO 0,54 GB, NL Portal backend 0,42 GB |
| Images van deze stack | 13,1 GB (som), waarvan zelfgebouwd: IKO 0,51 GB, NL Portal backend 0,48 GB, frontend 0,10 GB |
| Volumes na seed en test | 0,3 GB |
| Vrije schijf na `down` | 8,7 GB; na `docker builder prune` (Gradle- en pnpm-cache van de build) 13 GB. Images blijven staan. |

Details in `results/g4.json` onder `footprint`.

## Screenshots

In `docs/screenshots/g4/`: NL Portal voor burgers A, B en D (overzicht, Mijn zaken,
zaakdetail, taken, berichten, account met BRP-gegevens, en B die de zaak van A probeert
te openen), GZAC (dashboard, dossiers, dossier met gegevens en taken, alle taken) en de
IKO-beheer-UI. Maken, met de stack draaiend (Chromium uit `/opt/pw-browsers`):

```bash
export DIGID_SIM_WACHTWOORD=$(grep ^DIGID_SIM_WACHTWOORD= .env | cut -d= -f2-)
export MEDEWERKER_WACHTWOORD=$(grep ^MEDEWERKER_WACHTWOORD= .env | cut -d= -f2-)
NODE_PATH=$(npm root -g) node stacks/g4/screenshots.mjs
```
