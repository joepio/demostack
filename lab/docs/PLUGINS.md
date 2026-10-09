# Plug-ins: een eigen component aansluiten

DemoStack draait open source Common Ground-componenten met fictieve data en test ze tegen
de VNG-specificaties. Een leverancier (of een gemeente, of een ontwikkelaar) kan daar een
eigen component bij zetten: een portaal, een Mijn-API, een zaaksysteem of iets anders. Dat
heet een plug-in. De plug-in staat in de repository van de leverancier, niet in DemoStack;
DemoStack kent geen enkel product bij naam.

```bash
scripts/stack.sh up kern --plugin ../mijn-portaal/demostack
scripts/stack.sh test kern          # rapport: results/kern+mijn-portaal.md en .json
scripts/stack.sh down kern
```

Meer plug-ins tegelijk kan ook: `--plugin <map>` herhalen, of
`PLUGINS="../a/demostack ../b/demostack" scripts/stack.sh up kern`. `up` onthoudt de
plug-ins in `.demostack/<stack>.plugins`, zodat `seed`, `test`, `ps`, `logs` en `down`
dezelfde set gebruiken. `up` zonder `--plugin` start de stack zonder plug-ins.

De testcriteria komen uit de VNG-specificaties en aansluitprofielen, niet uit de plug-in.
Een plug-in zegt alleen wat hij aanbiedt en hoe je inlogt; DemoStack bepaalt wat er getest
wordt.

## Inhoud van een plug-in-map

| Bestand | Verplicht | Wat |
|---|---|---|
| `plugin.yaml` | ja | manifest: naam, leverancier, componenten, burgerkanalen, Mijn-API's, inloggen |
| `compose.yml` | ja | compose-overlay met de services van de plug-in |
| `stacks/<stack>.yml` | nee | extra overlay voor een bepaalde stack (bijvoorbeeld een takenbron die alleen daar bestaat) |
| `env.example` | nee | extra sleutels voor `.env`; `__GENEREER__` wordt een nieuw geheim |
| `bouw.sh` | nee | bouwt images die niet op een register staan; draait voor `up` met `DEMO_STACK` en `PLUGIN_DIR` |
| `seed.py` | nee | extra testdata na de gedeelde seed; draait in de tools-container |
| `tests.py` | nee | extra rooktests en isolatietypes (zelfde decorators als `stacks/<naam>/tests.py`) |

`scripts/stack.sh` voert compose uit met de basis, de bestanden van de stack, en daarna per
plug-in `compose.yml` en `stacks/<stack>.yml`. Compose leest relatieve paden vanaf de root
van DemoStack, dus verwijs naar je eigen bestanden met `${PLUGIN_<NAAM>_DIR}`: de absolute
map van de plug-in (naam in hoofdletters, `-` wordt `_`). In de tools- en
respect-container staat de map op `/plugins/<naam>` (alleen lezen).

## plugin.yaml

```yaml
naam: mijn-portaal                 # kleine letters, cijfers en -; ook in check-id's en rapportnaam
titel: Mijn Portaal
leverancier: Voorbeeldleverancier B.V.
licentie: EUPL-1.2
bron: https://example.org/mijn-portaal
versie: 1.4.0
omschrijving: Burgerportaal met MijnZaken next en MijnTaken next.
stacks: [kern, maykin]             # optioneel: alleen deze stacks; anders weigert up

inloggen: >-                       # voor mensen: hoe log je in de demo in
  Portaal op http://localhost:5180. Inloggen met de DigiD-simulatie: BSN van een
  testburger, wachtwoord DIGID_SIM_WACHTWOORD uit .env.

componenten:                       # zelfde formaat als stacks/basis/stack.yaml
  - id: mijn-portaal-api
    naam: Mijn Portaal API
    rol: burger-api                # infra | register | proces | portaal | burger-api | medewerker | integratie
    services: [mijn-portaal-api]
    health: {url: "http://mijn-portaal-api.local:8080/health", status: [200]}
  - id: mijn-portaal-web
    naam: Mijn Portaal web
    rol: portaal
    services: [mijn-portaal-web]
    health: {url: "http://mijn-portaal-web/", status: [200]}

burgerkanalen:                     # isolatietest (burger A mag niets van burger B zien)
  - id: mijn-portaal-api
    type: mijnzaken                # isolatie via de MijnZaken-API hieronder
    mijn_api: mijn-portaal-api
  - id: mijn-portaal-web
    type: spa                      # toont alleen wat de API teruggeeft
    api: mijn-portaal-api

mijn_apis:                         # categorie mijn-apis
  - id: mijn-portaal-api
    component: mijn-portaal-api
    naam: Mijn Portaal API
    mijnzaken: http://mijn-portaal-api.local:8080/api      # basis-URL volgens MijnZaken next
    mijntaken_reden: "geen takenbron in deze stack"         # of mijntaken: <basis-URL>
    login:
      type: digid-simulatie        # of dev-token
      client_id: mijnservices

bekende_fouten:                    # optioneel, zelfde betekenis als in stack.yaml
  mijn-apis/mijn-portaal-api/mijntaken/taken-bij-zaak: "uitleg met bron"

per_stack:                         # optioneel: aanvullingen per stack (lijsten op id)
  maykin:
    mijn_apis:
      - id: mijn-portaal-api
        mijntaken: http://mijn-portaal-api.local:8080/api
```

### Velden

- **`naam`, `titel`, `leverancier`, `licentie`, `bron`, `versie`, `omschrijving`.** Komen in
  het rapport (`plugins` in `results/<rapport>.json`), zodat altijd te zien is welk product
  van welke leverancier getest is.
- **`stacks`.** Optioneel. Zonder deze sleutel mag de plug-in op elke stack; de plug-in
  moet dan zelf omgaan met componenten die ontbreken.
- **`componenten`.** Komen bij de componenten van de stack: elk krijgt een
  gezondheidscheck, en een rooktest als `tests.py` er een registreert. Zonder rooktest
  meldt het rapport "nog geen rooktest".
- **`burgerkanalen`.** Elk portaal of elke burger-API krijgt de isolatietest van zijn
  `type`. Ingebouwd: `mijnzaken` (lijst, zoeken op het BSN van B, detail, document en
  zonder token, op de MijnZaken next-API), `spa` (portaal zonder eigen data) en `zgw`.
  Een eigen type registreer je in `tests.py` met `@isolatietype("naam")`.
- **`mijn_apis`.** Elke Mijn-API die de plug-in aanbiedt. `mijnzaken` en `mijntaken` zijn
  de basis-URL's (de `servers` uit de spec, vanuit het docker-netwerk). Ontbreekt er een,
  dan is die check overgeslagen met `<profiel>_reden` als reden.
- **`login`.** Hoe de testsuite een token krijgt voor de testburgers A, B en C:
  - `digid-simulatie`: password grant op Keycloak-realm `voorbeeldstad` met
    gebruikersnaam het BSN en wachtwoord `DIGID_SIM_WACHTWOORD`; `client_id` is
    standaard `mijnservices`. Het token heeft de claims `bsn` en `loa`.
  - `dev-token`: `POST {url}` met JSON `{"bsn": "<bsn>"}` (veldnaam te kiezen met
    `veld`); het antwoord bevat `access_token`. Alleen voor demo's met fictieve data.
- **`bekende_fouten`.** Een fout die bekend en uitgelegd is, blijft zichtbaar in het
  rapport maar laat de exitcode niet falen. Altijd met uitleg en bron.
- **`per_stack`.** Overschrijft of vult aan per stack. Lijsten met een `id` worden per id
  samengevoegd.

## Wat DemoStack test

| Categorie | Wat | Check-id's |
|---|---|---|
| gezondheid | draaien de services van elk component uit `componenten`, en antwoordt de health-URL | `gezondheid/<component>` |
| rook | rooktests uit `tests.py` van de plug-in | `rook/<component>/<check>` |
| burger-isolatie | per kanaal uit `burgerkanalen` | `burger-isolatie/<kanaal>/<check>` |
| mijn-apis | per Mijn-API: inloggen als testburger, de aansluitprofielen MijnZaken next en MijnTaken next (Arazzo, VNG API Lab, ongewijzigd in `vendor/vng-api-lab`), en controles op de geseede data (statushistorie, documenten, filter op status, een vertrouwelijk document dat de burger niet ziet) | `mijn-apis/<id>/login`, `mijn-apis/<id>/mijnzaken/<workflow>`, `mijn-apis/<id>/mijntaken/<workflow>`, `mijn-apis/<id>/data/<check>` |

Zonder plug-in met een Mijn-API is `mijn-apis` overgeslagen met die reden. De
categorieen `zgw` en de rooktests van de stack zelf draaien altijd, met of zonder plug-in.

Een `downloadUrl` in een MijnZaken-antwoord mag de publieke host van de plug-in hebben
(bijvoorbeeld `http://localhost:<poort>`): de test vervangt scheme en host door die van
de `mijnzaken`-URL.

## Wat de stack een plug-in aanbiedt

Een plug-in hoeft zelf geen registers of identiteit mee te brengen. Elke stack heeft:

| Wat | Waar | Geheim in `.env` |
|---|---|---|
| ZGW-applicatie `burgerportaal`: alleen lezen op zaken (per zaaktype), catalogi en documenten (tot en met zeer geheim) | Open Zaak, `http://openzaak.local:8000` | `ZGW_PORTAAL_CLIENT_ID`, `ZGW_PORTAAL_SECRET` (ZGW-JWT, HS256) |
| Token `burgerportaal`, alleen lezen | Open Object, `http://openobject.local:8000` | `OPENOBJECT_PORTAAL_TOKEN` |
| Token `burgerportaal` | Open Klant, `http://openklant.local:8000` | `OPENKLANT_PORTAAL_TOKEN` |
| Token `burgerportaal` (stacks met Open VTB: maykin, g4) | Open VTB, `http://openvtb.local:8000` | `OPENVTB_PORTAAL_TOKEN` |
| Keycloak-client `burgerportaal` (client credentials); tokens van `mijnservices` hebben `burgerportaal` als audience | `http://keycloak.local:8080/realms/voorbeeldstad` | `KEYCLOAK_PORTAAL_CLIENT_SECRET` |
| DigiD-simulatie: publieke client `mijnservices` (PKCE, redirect `http://localhost:*`), claims `bsn` en `loa` | idem; in de browser `http://localhost:8080` | `DIGID_SIM_WACHTWOORD` |
| BRP-mock (Haal Centraal BRP personen) | `http://brp-mock.local:80` | geen |

Open Zaak koppelt autorisaties per zaaktype aan de hostnaam: gebruik binnen het netwerk
altijd `http://openzaak.local:8000` (zie [`openzaak-bevindingen.md`](openzaak-bevindingen.md)).

## Afspraken

- **Netwerk.** Services van een plug-in krijgen een alias `<naam>.local` als andere
  containers ze aanroepen. Voorvoeg service-namen met de naam van de plug-in, zodat twee
  plug-ins niet botsen.
- **Hostpoorten.** Via variabelen uit je `env.example`, gebonden aan `${BIND_ADDRESS:-127.0.0.1}`.
  Vrij voor plug-ins: 5170 tot en met 5199 en 9000 tot en met 9099. Twee plug-ins met
  dezelfde poort zijn een conflict; pas dan een van beide aan in `.env`.
- **Images.** Een vaste tag, nooit `latest`. Een image met `build:` haalt `scripts/stack.sh pull`
  niet op; compose bouwt het bij de eerste `up`, of `bouw.sh` doet dat.
- **Geheimen.** Nooit in git. Gebruik de geheimen van de stack hierboven, of
  `__GENEREER__` in je `env.example`.
- **Data.** Alleen fictieve gegevens en test-BSN's uit de officiele testreeks. De
  testburgers en hun zaken staan in `stacks/basis/stack.yaml` en `seed/data.py`.
- **Testlogin.** Een dev-login die tokens uitgeeft voor elk BSN mag alleen in een demo met
  fictieve data. Noem het in `inloggen`.
- **Afhankelijkheden.** `depends_on` naar services van de stack (zoals `openzaak` met
  `condition: service_healthy`) mag; zet stack-specifieke afhankelijkheden in
  `stacks/<stack>.yml`.

## Een plug-in controleren

```bash
scripts/stack.sh up kern --plugin <map>
scripts/stack.sh compose kern config --services     # services van stack en plug-in
scripts/stack.sh test kern --alleen gezondheid,burger-isolatie,mijn-apis
```

Het rapport `results/kern+<naam>.md` noemt bovenaan de plug-in met leverancier en versie.
Rapporten zonder plug-in heten `results/<stack>.md`.
