# Stack dimpact: wat PodiumD draait

Een gemeente die zegt "ik wil PodiumD". Bron voor componenten en versies: de Helm-chart
`podiumd` 4.9.3 (`charts/podiumd/Chart.yaml` en `values.yaml` in
github.com/Dimpact-Samenwerking/helm-charts). PodiumD draait op Kubernetes; deze stack
is er een compose-opzet van, met dezelfde versies en dezelfde koppelingen.

```bash
scripts/stack.sh up dimpact      # images bouwen die ontbreken, starten, wachten, testdata laden
scripts/stack.sh test dimpact    # results/dimpact.json en results/dimpact.md
scripts/stack.sh down dimpact
```

Alles wordt automatisch geconfigureerd: setup-configuration (YAML), omgevingsvariabelen,
een realm-import voor Keycloak, een dataset voor PABC en een paar idempotente scripts
voor wat setup-configuration in deze versies nog niet kan. Er is geen handwerk in een
admin nodig.

**Status: werkt.** ZAC, het hart van PodiumD, draait hier niet (zie "Niet draaibaar").

## Componenten

| Component | Image | Host-poort | Intern adres | Status |
|---|---|---|---|---|
| Open Zaak 1.29.3 | `openzaak/open-zaak:1.29.3` | 8001 | `openzaak.local:8000` | draait en getest |
| Open Notificaties 1.16.2 | `openzaak/open-notificaties:1.16.2` | 8002 | `opennotificaties.local:8000` | draait en getest |
| Open Klant 2.15.0 | `maykinmedia/open-klant:2.15.0` | 8004 | `openklant.local:8000` | draait en getest |
| Referentielijsten 0.7.4, Selectielijst | zie `stacks/kern/README.md` | | | draait en getest |
| Objecten API 3.6.2 (los) | `maykinmedia/objects-api:3.6.2` | 8150 | `objecten.local:8000` | draait en getest |
| Objecttypen API 3.4.2 (los) | `maykinmedia/objecttypes-api:3.4.2` | 8151 | `objecttypen.local:8000` | draait en getest |
| Open Formulieren 3.5.8 | `openformulieren/open-forms:3.5.8` | 8102 | `openformulieren.local:8000` | draait en getest |
| ClamAV 1.5.4 (virusscan voor Open Formulieren) | `clamav/clamav:1.5.4` | geen | `clamav:3310` | draait en getest |
| Open Inwoner 2.4.3 | `maykinmedia/open-inwoner:2.4.3` | 8103 | `openinwoner.local:8000` | draait en getest |
| Elasticsearch 9.0.3 (zoeken in Open Inwoner) | `elasticsearch:9.0.3` | geen | `elasticsearch.local:9200` | draait (gezondheid) |
| Open Archiefbeheer 2.0.0 | `maykinmedia/open-archiefbeheer:2.0.0` | 8154 | `openarchiefbeheer.local:8000` | draait en getest |
| Open Beheer 0.9.1 | `maykinmedia/open-beheer:0.9.1` | 8155 | `openbeheer.local:8000` | draait en getest |
| KISS 3.1.3 | `demogemeente/kiss:3.1.3` (gebouwd) | 8156 | `kiss.local:8080` | draait en getest |
| ITA 3.3.2 (web en poller) | `demogemeente/ita-web:3.3.2`, `ita-poller` (gebouwd) | 8157 | `ita.local:8080` | draait en getest |
| PABC 1.1.1 (API en migraties) | `demogemeente/pabc-api:1.1.1` (gebouwd) | 8158 | `pabc.local:8080` | draait en getest |
| NotifyNL OMC 1.17.19 | `worthnl/notifynl-omc:1.17.19` | 8159 | `omc.local:8080` | draait en getest; keten met Open Notificaties faalt (bekend) |
| Notify-mock (in plaats van NotifyNL) | `openzaak/open-zaak:1.29.0` met `tools/notify_mock.py` | geen | `notify-mock.local:8080` | draait en getest |
| Mailpit (SMTP-opvang) | `axllent/mailpit:v1.31.4` | 8160 | `mailpit.local:1025` | draait en getest |
| BRP-vertaler | `openzaak/open-zaak:1.29.0` met `tools/brp_vertaler.py` | geen | `brp-api.local:8080` | draait en getest |
| Keycloak 26.4.7, realms `voorbeeldstad` en `podiumd` | `keycloak/keycloak:26.4.7` | 8080 | `keycloak.local:8080` en `:8443` | draait en getest |
| ZAC 5.4.5 | | | | niet draaibaar, zie hieronder |
| ZGW Office Add-in, officiele BRP-mock | | | | niet draaibaar, zie hieronder |
| PodiumD-adapter, ZaakBrug, KISS Elastic Sync, Frank!Gateway | | | | niet opgenomen, zie hieronder |

Open Product zit niet in PodiumD (`zonder: [openproduct]`). Open Object 4.1 uit de kern
is vervangen door de losse Objecten- en Objecttypen-API's die PodiumD draait; de
component-id blijft `openobject`, zodat de gedeelde seed en rooktests ook hier lopen.

**Zelf gebouwd.** KISS, ITA en PABC staan alleen op ghcr.io, dat in de bouwomgeving
geblokkeerd is. `stacks/dimpact/bouw.sh` bouwt ze uit de broncode op precies de tag uit
de chart (`stacks/dimpact/bouw/dotnet.Dockerfile`, .NET 8 op Alpine, Node voor de
Vue-frontends). `scripts/stack.sh up` roept het aan en bouwt alleen wat ontbreekt; de
broncode komt in `.bron/` (niet in git). Achter een proxy met TLS-inspectie:
`EXTRA_CA_CERT=/pad/naar/ca.crt` (alleen in de bouwfase). Met toegang tot ghcr.io kun je
in `compose.yml` de officiele images gebruiken.

**Keycloak over https.** KISS en ITA eisen een OIDC-authority over https. `bouw.sh`
maakt een eigen demo-CA en een certificaat voor `keycloak.local` (in
`stacks/dimpact/.tls/`, niet in git); Keycloak luistert daarmee ook op poort 8443 en
KISS en ITA vertrouwen die CA. De browser blijft `http://localhost:8080` gebruiken.

Beheerders: `admin` met `ADMIN_PASSWORD` uit `.env` in alle Django-componenten
(`admin@voorbeeldstad.example` in Open Inwoner). Medewerkers loggen in via realm
`podiumd` met `MEDEWERKER_WACHTWOORD`:

| Gebruiker | Wie (fictief) | Rollen |
|---|---|---|
| `kcm.jansen` | Karin Jansen, Klantcontactcentrum | KISS klantcontactmedewerker en kennisbank, ITA-toegang |
| `behandelaar.desai` | Ravi Desai, Vergunningen (Team Omgevingswet) | ITA-toegang |
| `beheer.devries` | Mila de Vries, functioneel beheer | KISS beheerder en redacteur, ITA- en PABC-functioneel beheerder, superuser in Open Archiefbeheer en Open Beheer |

## Koppelingen

```
        DigiD-simulatie (realm voorbeeldstad)        medewerkers (realm podiumd, https :8443)
              |                                          |
 burger --> Open Inwoner ----> Open Zaak, Open Klant (Mijn vragen), Objecten ("Externe taak"),
    |                          BRP-vertaler --> BRP-mock
    v
 Open Formulieren -- prefill --> BRP-vertaler;  registratie --> Open Zaak (zaak plus PDF)
         '-- uploads --> ClamAV

 KISS (kcm) ----> Open Klant (klantcontacten, contactverzoeken), Open Zaak (zaak zoeken),
             \--> BRP-vertaler (persoon zoeken), Objecten (afdelingen, groepen, medewerkers)
 ITA (behandelaar) --> Open Klant (interne taken per actor), Objecten (logboek, medewerkers),
             \--> Open Zaak;  ita-poller --> Mailpit (mail bij nieuwe taak)
 PABC ----------> eigen database: functionele rol x zaaktype x applicatierol (voor ZAC)
 Open Archiefbeheer --> Open Zaak (afgesloten zaken), Selectielijst, Open Klant, Objecten
 Open Beheer ---------> Open Zaak (catalogi, zaaktypen)
 Open Notificaties --> OMC (abonnement kanaal zaken) --> Notify-mock (e-mail/sms aan inwoner)
```

- **ZGW.** `config/openzaak/stack-dimpact.yaml` maakt applicaties voor Open Formulieren,
  Open Inwoner, KISS, ITA, OMC, Open Archiefbeheer en Open Beheer; de autorisaties zet
  `stacks/dimpact/seed.py`.
- **Open Klant.** Tokens voor Open Inwoner, KISS, ITA, OMC en Open Archiefbeheer
  (`config/openklant/stack-dimpact.yaml`).
- **Objecten en Objecttypen.** De PodiumD-objecttypen (Afdeling, Groep, Medewerker,
  Activiteitenlog ITA) krijgen vaste UUID's
  `7c1d4a0e-5a7b-4c1e-8f00-0000000000c1` tot en met `c4`; OMC verwijst naar `b1` (Externe
  taak) en reserveert `c5` tot en met `c7` voor berichten, besluitinformatie en KTO;
  die drie bestaan niet, OMC gebruikt ze alleen in workflows die hier niet getest worden. Zo kent de configuratie van KISS, ITA en OMC ze vooraf.
  De schema's staan in `config/objecttypen/schemas/`.
- **Open Notificaties.** Het abonnement van OMC op kanaal `zaken` maakt de seed aan.
- **Taken voor inwoners.** PodiumD heeft geen Open VTB; taken staan als "Externe taak" in
  de Objecten API. Een plug-in met MijnTaken next heeft daarvoor een eigen bron nodig.

## Configuratie

| Waar | Wat |
|---|---|
| `stacks/dimpact/compose.yml` | services, plus aanvullingen op de init-containers van de kern |
| `stacks/dimpact/stack.env` | PodiumD-versies van de kerncomponenten, extra databases |
| `stacks/dimpact/env.example` | poorten en geheimen (`__GENEREER__`), `up` vult `.env` aan |
| `stacks/dimpact/bouw.sh`, `bouw/dotnet.Dockerfile` | KISS, ITA en PABC uit broncode; demo-CA voor Keycloak |
| `config/keycloak-podiumd/` | realm `podiumd`: clients, rollen, drie medewerkers |
| `config/objecten/`, `config/objecttypen/` | setup-configuration van de losse API's, tokens, objecttypen |
| `config/openformulieren/data-dimpact.yaml`, `configureer.py` | OIDC DigiD, ZGW, Objecten, ClamAV |
| `config/openinwoner/data-dimpact.yaml`, `configureer.py` | OIDC DigiD, ZGW, Open Klant, BRP, Objecten en Objecttypen als twee services |
| `config/openarchiefbeheer/data.yaml`, `config/openbeheer/data.yaml` | setup-configuration: ZGW-services en OIDC op realm `podiumd` |
| `config/pabc/dataset.json` | applicatie ZAC, applicatierollen, functionele rollen, zaaktypen |
| `config/{openzaak,opennotificaties,openklant}/stack-dimpact.yaml` | extra applicaties en tokens in de kern |
| `stacks/dimpact/seed.py`, `na-seed.sh` | testdata (idempotent); `cache_zaken` in Open Archiefbeheer |
| `tools/notify_mock.py`, `tools/beheerder.py` | Notify-mock; hulp voor beheerderslogin in tests |

Databases komen uit `DB_EXTRA` in `stack.env`; Redis gebruikt databases 12 tot en met 21.

## Testdata (Voorbeeldstad)

Bovenop de gedeelde seed (zaken VBS-2026-000101 tot en met -000105 voor burgers A, B, C)
doet `seed.py` wat stack maykin doet voor Open Formulieren en Open Inwoner (formulier
"Melding openbare ruimte", externe taken, vragen in Open Klant), plus:

- afdelingen Vergunningen, Zorg en Welzijn en Klantcontactcentrum, groepen Team
  Omgevingswet en Wmo-loket, en de drie medewerkers als objecten;
- actoren in Open Klant voor medewerkers en organisatorische eenheden, en twee
  contactverzoeken met een interne taak: 8000000001 "Terugbelverzoek over de dakkapel"
  (burger A, zaak 101, voor Ravi Desai en Team Omgevingswet) en 8000000002 "Vraag over
  de planning van de traplift" (burger B, zaak 104, voor Karin Jansen en het
  Klantcontactcentrum). ITA toont een taak alleen aan leden van de afdeling of groep
  waaraan hij is toegewezen;
- PABC: Team Vergunningen, Team Wmo en anderen met applicatierollen per zaaktype;
- het abonnement van OMC in Open Notificaties.

## Testresultaat

Zonder plug-ins: **85 geslaagd, 8 gefaald (alle 8 bekend), 11 overgeslagen**. Afgeleid van
de laatste run vanaf lege volumes (8 oktober 2026); zie `results/dimpact.md` en
`results/dimpact.json`.

| Categorie | Geslaagd | Gefaald | Overgeslagen |
|---|---|---|---|
| gezondheid | 23 | 0 | 7 (ZAC en de andere niet-draaibare of niet-opgenomen componenten) |
| rook | 46 | 1 (bekend: keten Open Notificaties naar OMC) | 3 (infra) |
| zgw | 3 | 7 (bekend, uit de kern) | 0 |
| burger-isolatie | 13 | 0 | 0 |
| mijn-apis | 0 | 0 | 1 (geen plug-in met een Mijn-API) |

Rooktests van deze stack (`tests.py`): objecttypen met vaste UUID's; organisatie in de
Objecten API; KISS (login via Keycloak, afdelingen en groepen, zaak zoeken, contactverzoek
zoeken, persoon zoeken in de BRP, niets zonder login); ITA (werkvoorraad per medewerker,
eigen taak wel en taak van een andere afdeling niet, beheerder ziet alles, 401 zonder
login); PABC (applicatierollen per zaaktype, 401 zonder sleutel); Open Archiefbeheer
(afgesloten zaken uit Open Zaak, login via Keycloak); Open Beheer (zaaktypen, OIDC-config);
OMC (keten en losse notificatie); ClamAV (EICAR direct en via een upload in Open
Formulieren); Mailpit; en de portaaltests uit stack maykin (Open Inwoner, Open
Formulieren).

### Isolatie

Burgers A (999990627) en B (999997609), ingelogd via de DigiD-simulatie:

- **Open Inwoner 2.4.3.** A ziet alleen eigen zaken (101, 102), B alleen 103 en 104.
  Zaakdetail en een document van B geven A een 404. Taken, vragen en profiel van A
  bevatten niets van B. Zonder login: 302 naar de loginpagina.
- **Open Formulieren 3.5.8.** De inzending van B geeft A een 404, de stap van B een 403.
  Prefill geeft alleen de eigen BRP-gegevens. Zonder login: 403.

Medewerkers (geen burgerkanaal, wel getest):

- **ITA.** Ravi Desai ziet alleen zijn eigen contactverzoek (8000000001), Karin Jansen
  alleen dat van het KCC (8000000002); de taak van het KCC geeft Desai een 403. De
  functioneel beheerder ziet beide. Zonder login: 401.
- **KISS.** Zonder login geen zaken en geen klantcontacten (302 naar Keycloak).

Zwakke plekken eronder: het token van ITA en KISS in Open Klant leest alle
klantcontacten, en het token van Open Inwoner in de Objecten API alle externe taken. De
scheiding zit in het filter van de toepassing, niet in de bron. Het ZGW-applicatietoken
mag elke zaak van de geautoriseerde zaaktypen lezen (zie de zgw-checks).

Schermafdrukken (Playwright, Chromium): `docs/screenshots/dimpact/`. Burgerkant met
`stacks/maykin/screenshots.mjs` (`UIT=docs/screenshots/dimpact`), medewerkerskant (KISS,
ITA, Open Archiefbeheer) met `stacks/dimpact/screenshots.mjs`. Daarin ook A die de zaak
van B opent (404) en Desai die de taak van het KCC opent (geweigerd).

## Bevindingen

- **OMC 1.17.19 en Open Notificaties 1.16.2 passen niet op elkaar.** OMC antwoordt op elke
  notificatie van Open Notificaties met 206 en intern 422: de notificatie bevat het veld
  `source`, dat het model van OMC niet kent. Een notificatie zonder dat veld wordt wel
  een e-mail. Dit zijn de versies uit dezelfde PodiumD-chart.
- **KISS en ITA eisen https voor OIDC** (`RequireHttpsMetadata` staat vast aan); lokaal
  vraagt dat een eigen CA.
- **KISS, ITA en PABC staan alleen op ghcr.io.** Wie die registry niet bereikt, moet ze
  zelf bouwen; de bouw van KISS haalt ook npm-pakketten op.
- **Objecttypen met vaste UUID's.** KISS, ITA en OMC krijgen de objecttype-URL's als
  configuratie; door de UUID's vast te kiezen is de hele keten vooraf configureerbaar.
- **Open Archiefbeheer** haalt afgesloten zaken 's nachts op; `na-seed.sh` doet het
  direct.
- **Open Inwoner met losse API's.** Objecten en Objecttypen zijn hier twee services; het
  configuratiescript van Open Inwoner kiest de Objecttypen-service via
  `OIP_OBJECTTYPEN_SERVICE`.
- **PABC** is in 4.9.3 alleen voor ZAC; zonder ZAC is het hier een losse API met data.

## Voetafdruk

Gemeten op de bouwmachine (15 GB RAM, 4 CPU's), stack vanaf lege volumes:

| | |
|---|---|
| Starttijd | 346 s voor `up` tot en met seed en `na-seed.sh`; alle images lokaal aanwezig, ook de zelfgebouwde. De eerste bouw van KISS, ITA en PABC duurt daarnaast enkele minuten per component |
| Geheugen | 8,7 GiB voor 38 containers een minuut na het starten, 9,0 GiB na de testsuite. Grootste: ClamAV 1057 MiB (virusdefinities in het geheugen), Elasticsearch 855 MiB, Keycloak 620 MiB, Open Formulieren 567 MiB, Open Formulieren-celery 484 MiB, Open Inwoner 480 MiB, Open Zaak 446 MiB. De .NET-componenten zijn klein: KISS 103 MiB, PABC 85 MiB, ITA 74 MiB, OMC 56 MiB |
| Images | 19,4 GB opgeteld voor de 27 images van de stack, 18,2 GB op schijf door gedeelde lagen. Grootste: Elasticsearch 2,08 GB, Open Formulieren 2,02 GB, Objecten API 1,73 GB, Open Inwoner 1,56 GB. Zelfgebouwd (KISS, ITA web en poller, PABC API en migraties): samen 0,9 GB |
| Volumes | 0,4 GB na seed en test, vrijwel alles Postgres |

De hele stack past in een keer; opsplitsen was niet nodig. Met ZAC erbij (circa 2 tot 4
GiB voor ZAC, Solr, OPA en Gotenberg) wordt het krap op 15 GB.

## Niet draaibaar of niet opgenomen

- **ZAC 5.4.5 (zaakafhandelcomponent).** Niet draaibaar hier. Het image staat alleen op
  ghcr.io (geblokkeerd); bouwen uit broncode vraagt Gradle, JDK 21 en Node met enkele GB
  cache, en ZAC heeft zelf Solr, OPA, Gotenberg, SmartDocuments en KVK/BAG nodig. Dat past
  niet in de vrije schijfruimte (circa 8 GB) en het geheugen naast de rest. Nodig:
  toegang tot ghcr.io, circa 4 GB extra RAM, Solr, OPA en Gotenberg als services, een
  client in realm `podiumd` en PABC (staat al klaar).
- **ZGW Office Add-in 0.11.0.** Alleen op ghcr.io en vraagt Microsoft 365.
- **Officiele BRP personen-mock 2.7.0.** ghcr.io geblokkeerd; vervangen door de
  iswish-mock met `tools/brp_vertaler.py`.
- **PodiumD-adapter 0.6.7.** Koppelt KISS en ITA aan de e-Suite (licentie), niet nodig
  met Open Zaak en Open Klant.
- **ZaakBrug 2.3.32.** Optioneel in PodiumD (StUF-ZKN naar ZGW); geen StUF-afnemer hier.
- **KISS Elastic Sync en Elastic Open Crawler.** Vullen de zoekindexen van KISS
  (kennisbank, website, smoelenboek) uit externe bronnen; de crawler staat op
  docker.elastic.co (geblokkeerd). Zoeken in KISS geeft daarom geen kennisartikelen.
- **Frank!Gateway (APISIX) met OpenBao.** Uitgaande gateway naar landelijke registers;
  hier praat alles direct met de mocks.
- **Keycloak 26.7.3 van quay.io.** quay.io is hier niet bereikbaar; de basis-Keycloak
  26.4.7 speelt beide realms.
