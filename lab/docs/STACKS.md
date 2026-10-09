# Stacks vergeleken

Een gemeente die zegt "ik wil de Maykin-spullen", "ik wil wat PodiumD draait", "ik wil de
G4-keuze" of "ik wil de VCG-basisset" krijgt hier een stack: een complete, gekoppelde set
componenten met dezelfde testdata en dezelfde testsuite. Dit document zet de vijf stacks
naast elkaar: wat draait er, wat is getest, hoe goed zijn burgers van elkaar gescheiden,
wat kost het, en wat leren we ervan voor gemeenten.

Bronnen: `results/<stack>.json` (testrapport en footprint) en de README per stack
(`stacks/<stack>/README.md`). Gemeten op 7 en 8 oktober 2026, elke stack vanaf lege
volumes, op een machine met 15 GB geheugen en 4 CPU's. Alle cijfers zijn zonder plug-ins;
een eigen component van een leverancier komt erbij als plug-in
([`PLUGINS.md`](PLUGINS.md)) en krijgt dan een eigen rapport.

## Componenten per stack

Legenda:

- **getest**: draait, en de testsuite doet echte aanroepen (rooktest, isolatietest of
  keten) die slagen, of falen als bekende fout;
- **draait**: draait, alleen de gezondheidscheck;
- **niet draaibaar**: hoort bij het landschap, maar draait hier niet (reden onder de tabel);
- **niet opgenomen**: hoort bij het landschap, maar bewust weggelaten;
- **-**: hoort niet bij deze stack.

Versies staan in de cel als ze afwijken van de kern.

### Registers en API's

| Component | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| Open Zaak | getest (1.29.0) | getest | getest (1.29.3) | getest | getest |
| Open Notificaties | getest (1.16.1) | getest | getest (1.16.2) | getest | getest |
| Open Object (Objecten en Objecttypen in een applicatie) | getest (4.1.0) | getest | - | getest | getest |
| Objecten API en Objecttypen API (los) | - | - | getest (3.6.2 en 3.4.2) | - | - |
| Open Klant | getest (2.17.0) | getest | getest (2.15.0) | getest | getest |
| Open Product | getest (1.8.0) | getest | - | - | getest |
| Referentielijsten | getest (0.7.3) | getest | getest (0.7.4) | getest | getest |
| VNG Selectielijst | getest (1.0.5) | getest | getest | getest | getest |
| Open VTB (Verzoeken, Taken, Berichten) | - | getest (0.2.0) | - | getest (0.2.0) | - |
| Open Organisatie | - | - | - | - | getest (0.2.0) |
| GPP-publicatiebank | - | - | - | - | getest (2.1.0) |
| OpenPlan | - | - | - | - | getest (0.1.0, zelf gebouwd) |
| OpenRegister (Nextcloud) | - | - | - | - | getest (1.0.3, zelf gebouwd) |

### Burgerkant

| Component | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| Open Formulieren | - | getest (4.0.1) | getest (3.5.8, met ClamAV) | getest (3.5.8) | - |
| Open Inwoner | - | getest (2.4.5) | getest (2.4.3) | - | - |
| NL Portal | - | - | - | getest (3.0.4/3.0.3, zelf gebouwd) | - |
| OpenPDC en OpenPub (WordPress) | - | - | - | - | getest (3.18.1 en 3.8.7) |

### Medewerkerskant en processen

| Component | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| KISS | - | - | getest (3.1.3, zelf gebouwd) | - | - |
| ITA (web en poller) | - | - | getest (3.3.2, zelf gebouwd) | - | - |
| ZAC (zaakafhandelcomponent) | - | - | niet draaibaar (5.4.5) | - | - |
| Valtimo/GZAC | - | - | - | getest (13.48.0) | - |
| IKO | - | - | - | getest (1.5.1, zelf gebouwd) | - |
| Open Archiefbeheer | - | gepland | getest (2.0.0) | - | - |
| Open Beheer | - | gepland | getest (0.9.1) | - | getest (0.9.0) |
| Operaton (met procesworker) | - | - | - | - | getest (2.1.5) |
| Operaton Modeler | - | - | - | - | niet draaibaar (1.2.0) |
| ZGW Office Add-in | - | - | niet draaibaar (0.11.0) | - | - |

### Integratie en infrastructuur

| Component | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| Keycloak (DigiD-simulatie en medewerkers) | getest (26.4.7) | getest | getest (realm `podiumd`, https) | getest (realm `g4`, token exchange) | getest (realm `vcg`) |
| BRP-mock (iswish) | getest | getest | getest | getest | getest |
| BRP-vertaler (BRP API Personen 2) | - | getest | getest | getest | - |
| Officiele BRP personen-mock | - | niet draaibaar | niet draaibaar | niet draaibaar | - |
| Notificatie-sink, Postgres, Redis | draait | draait | draait | draait | draait |
| Elasticsearch (voor Open Inwoner) | - | draait | draait | - | - |
| ClamAV | - | - | getest (EICAR geweigerd) | - | - |
| Mailpit | - | - | draait | - | - |
| PABC | - | - | getest (1.1.1, zelf gebouwd) | - | - |
| NotifyNL OMC (met Notify-mock) | - | - | getest (1.17.19, keten faalt bekend) | - | - |
| OpenFSC (directory, 2 peers) | - | - | - | - | getest (2.4.0) |
| OpenFTV | - | - | - | - | niet draaibaar (1.26.14) |
| PodiumD-adapter | - | - | niet opgenomen | - | - |
| ZaakBrug | - | - | niet opgenomen | - | - |
| KISS Elastic Sync en crawler | - | - | niet opgenomen | - | - |
| Frank!Gateway | - | - | niet opgenomen | - | - |

### Waarom iets niet draait

| Component | Stack | Reden | Wat nodig is |
|---|---|---|---|
| ZAC 5.4.5 | dimpact | image alleen op ghcr.io (geblokkeerd); bouwen vraagt Gradle, JDK 21 en GB's cache, plus Solr, OPA, Gotenberg, SmartDocuments en KVK/BAG | toegang tot ghcr.io en 2 tot 4 GiB extra geheugen; PABC staat al klaar |
| ZGW Office Add-in | dimpact | alleen op ghcr.io, en vraagt Microsoft 365 | ghcr.io en een Microsoft 365-tenant |
| Officiele BRP personen-mock | maykin, dimpact, g4 | ghcr.io geblokkeerd | ghcr.io; dan kan de BRP-vertaler weg |
| Operaton Modeler | vcg | desktopapplicatie (Electron), geen server | niets: het BPMN-proces is met de hand geschreven |
| OpenFTV 1.26.14 | vcg | geen implementatie gevonden; de link in de basisset wijst naar ZaakBrug | een bron of image van de bedoelde component |
| Open Archiefbeheer, Open Beheer | maykin | zitten in dimpact en vcg | kunnen erbij, nog niet gedaan |
| PodiumD-adapter, ZaakBrug, Frank!Gateway, KISS Elastic Sync | dimpact | niet nodig zonder e-Suite, StUF of externe bronnen; crawler staat op docker.elastic.co (geblokkeerd) | |

## Testresultaten

Alle stacks draaien dezelfde vijf categorieen (zie [`tests/README.md`](../tests/README.md)).
Per stack: geslaagd / gefaald (waarvan bekend) / overgeslagen.

| Categorie | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| gezondheid | 12 / 0 / 0 | 16 / 0 / 2 | 23 / 0 / 7 | 17 / 0 / 1 | 22 / 0 / 2 |
| rook | 19 / 0 / 3 | 30 / 0 / 3 | 46 / 1 (1) / 3 | 39 / 1 (1) / 3 | 38 / 0 / 3 |
| zgw | 3 / 7 (7) / 0 | 3 / 7 (7) / 0 | 3 / 7 (7) / 0 | 3 / 7 (7) / 0 | 3 / 7 (7) / 0 |
| burger-isolatie | 0 / 0 / 1 | 13 / 0 / 0 | 13 / 0 / 0 | 14 / 0 / 0 | 6 / 0 / 0 |
| mijn-apis | 0 / 0 / 1 | 0 / 0 / 1 | 0 / 0 / 1 | 0 / 0 / 1 | 0 / 0 / 1 |
| **totaal** | **34 / 7 (7) / 5** | **62 / 7 (7) / 6** | **85 / 8 (8) / 11** | **73 / 8 (8) / 5** | **69 / 7 (7) / 6** |

De kern is opnieuw gedraaid zonder plug-ins. De cijfers van maykin, dimpact, g4 en vcg zijn
afgeleid van de runs van 7 en 8 oktober 2026, die toen een ingebouwde portaallaag
hadden: de checks van die laag zijn eruit gehaald (zie de kop van `results/<stack>.md`).

Geen enkele stack heeft een onverwachte fout. De bekende fouten:

- **zgw, alle stacks (7).** Het ZGW-aansluitprofiel rechtstreeks op Open Zaak. In de modus
  "gedrag" mag een applicatietoken elke zaak van de geautoriseerde zaaktypen lezen en is
  het BSN een filter dat de client kiest (2). In de modus "strikt" wijkt Open Zaak 1.29 af
  op schema en content-type (5). Zie [`aansluitprofielen/README.md`](../aansluitprofielen/README.md).
- **dimpact, rook (1).** NotifyNL OMC 1.17.19 weigert elke notificatie van Open
  Notificaties 1.16.2 (206, intern 422) om het veld `source`. Beide versies komen uit
  dezelfde PodiumD-chart. OMC zelf werkt.
- **g4, rook (1).** GZAC 13.48 schrijft portaaltaken als taak v1; NL Portal 3.0 leest
  alleen taak v2. De taak staat in Open Object, maar niet in Mijn taken.

Overgeslagen is steeds met reden: infrastructuur zonder rooktest (Postgres, Redis,
notificatie-sink), de categorie `mijn-apis` zonder plug-in, en de componenten uit "Waarom
iets niet draait".

## Isolatie tussen burgers

Testburgers A (999990627) en B (999997609). De vraag per kanaal: kan A iets van B zien?

| Kanaal | Stack | Resultaat |
|---|---|---|
| Open Inwoner | maykin, dimpact | A ziet alleen 101 en 102, B alleen 103 en 104; zaak en document van B geven A 404 (ook in de browser); taken, vragen en profiel schoon; zonder login naar de loginpagina |
| Open Formulieren | maykin, dimpact, g4 | inzending van B geeft A 404, stap van B 403; prefill geeft alleen eigen BRP-gegevens; zonder login 403 |
| NL Portal | g4 | 9 van 9: lijsten schoon, filteren op het zaaknummer van B geeft niets, zaak, taak en bericht van B geven "Access denied", document 401, zonder token geen data, medewerkerstoken 401 |
| Openbare kanalen (OpenPDC, OpenPub, publicatiebank, OpenRegister) | vcg | geen BSN of naam van een testburger in de 6 antwoorden |

Medewerkers zijn ook getest waar een stack ze heeft: in ITA ziet een medewerker alleen
de eigen contactverzoeken (403 op die van het KCC); KISS, IKO, Open Beheer en Open
Organisatie weigeren zonder login of zonder de juiste rol.

**Alle burgerkanalen houden A en B gescheiden. Maar in geen enkele stack zit die
scheiding in de bron.** Elk portaal krijgt een token dat alles leest, en filtert zelf:

| Bron | Token van | Leest |
|---|---|---|
| Open Zaak (ZGW 1.x) | elk portaal (ook de leesclient `burgerportaal`) | elke zaak van de geautoriseerde zaaktypen; het BSN is een queryfilter |
| Open VTB 0.2.0 | elk portaal (token `burgerportaal`) | de taken van alle burgers |
| Open Object / Objecten API | Open Inwoner | alle externe taken; Open Inwoner filtert op BSN |
| Open Klant | KISS en ITA | alle klantcontacten |
| OpenPlan 0.1.0 | elke afnemer | alle personen en plannen; er is geen BSN-filter |

Een fout in het filter van een portaal is dus direct een datalek. Daarom draait de
isolatietest op elk portaal in elke stack, ook op dat van een plug-in, en blijven de twee
zgw-fouten "gedrag" bewust rood.

Schermafdrukken van de isolatie: `docs/screenshots/maykin/oip-isolatie-a-opent-zaak-van-b-*.png`,
`docs/screenshots/dimpact/ita-desai-3-taak-van-kcc-geweigerd.png`,
en `docs/screenshots/g4/nlportal-burger-b-7-probeert-zaak-van-a.png`.

## Footprint

Gemeten vanaf lege volumes, met de images al lokaal, op 15 GB geheugen en 4 CPU's. Elke
stack past in een keer; geen enkele hoefde in twee helften. De metingen bevatten toen een
portaallaag van 2 containers, ongeveer 33 MiB geheugen en 0,3 GB images; die zijn hieronder
van containers en images afgetrokken.

| | kern | maykin | dimpact | g4 | vcg |
|---|---|---|---|---|---|
| Start (`up` tot en met seed) | ruim 3 min | 327 s | 346 s | 330 s | 309 s |
| Geheugen na de tests | 4,2 GiB | 7,5 GiB | 9,0 GiB | 8,0 GiB | 7,1 GiB |
| Containers | 18 | 27 | 36 | 30 | 39 (40 met Open Beheer-frontend) |
| Grootste verbruikers | Keycloak 587 MiB, Open Zaak 435 MiB | Elasticsearch 867, Keycloak 552 MiB | ClamAV 1057, Elasticsearch 855, Keycloak 620 MiB | GZAC-backend 1375, Keycloak 611, IKO 542 MiB | Keycloak 784, Operaton 501, Nextcloud 496 MiB |
| Images op schijf | 8,3 GB | 13,9 GB | 17,9 GB | 12,4 GB | 17,4 GB (som, gedeelde lagen dubbel) |
| Waarvan zelf gebouwd | geen | geen | KISS, ITA, PABC 0,9 GB | IKO, NL Portal 1,1 GB | OpenRegister 3,3, WordPress 1,15, OpenPlan 1,05 GB |
| Volumes | 0,2 GB | 0,33 GB | 0,4 GB | 0,31 GB | 2,2 GB |

Een eerste bouw van de zelfgebouwde images (KISS, ITA, PABC, NL Portal, IKO, OpenPlan,
WordPress, OpenRegister) kost per image een paar minuten extra. Met 18 GB vrije schijf
past steeds een stack plus de kern; daarna `scripts/stack.sh opruimen`.

## Lessen voor gemeenten die een smaak kiezen

1. **Isolatie tussen burgers is een eigenschap van het portaal, niet van de registers.**
   Elk portaal in elke stack scheidt A en B goed, maar met tokens die alles lezen (zie de
   tabel hierboven). Vraag bij elke keuze: welk token heeft dit portaal, wat kan dat token
   lezen, en waar staat de test die bewijst dat het filter klopt? Behandel een
   portaaltoken als een beheertoken.
2. **Een pakket is geen garantie dat de onderdelen op elkaar passen.** Twee keer vonden we
   een breuk tussen componenten die samen geleverd worden: OMC en Open Notificaties uit
   dezelfde PodiumD-chart, en de portaaltaak van GZAC die NL Portal niet leest. Test de
   keten (zaak, notificatie, taak, portaal), niet alleen elk component.
3. **De keuze voor een smaak is ook een keuze voor een takenmodel.** Er zijn er nu drie:
   Open VTB (maykin, g4), "Externe taak" in de Objecten API (Open Inwoner, PodiumD) en
   Portaaltaak v1/v2 in Open Object (GZAC, NL Portal). Wie later van portaal of
   zaaksysteem wisselt, moet de taken meeverhuizen of vertalen.
4. **Configuratie als code is nergens compleet.** Setup-configuration dekt prefill, CMS,
   tokens en de BRP niet in Open Formulieren 4.0, Open Inwoner 2.4.5 en Open VTB 0.2.0;
   IKO heeft geen import; GZAC accepteert alleen definitieve zaakdefinities; en
   setup-configuration geeft applicaties in Open Zaak alleen alle autorisaties. Reken op
   eigen scripts (zoals in `config/` en `stacks/*/seed.py`), anders wordt het handwerk in
   een admin dat niemand kan herhalen.
5. **Rechten in beheertools zelf regelen.** Open Beheer 0.9 laat elke ingelogde gebruiker
   zaaktypen wijzigen; pas een inlogflow in Keycloak die op de rol
   Functioneel-Beheerder controleert, sloot dat af. Ook KISS en ITA eisen https voor de
   login, en NL Portal heeft de oudere token exchange van Keycloak nodig.
6. **Waar je images vandaan komen telt.** KISS, ITA, PABC, ZAC, IKO, de Office Add-in en de
   officiele BRP-mock staan alleen op ghcr.io; NL Portal, OpenPlan, OpenPDC/OpenPub en
   OpenRegister hebben geen bruikbaar gepubliceerd image. Een gemeente of hoster die
   ghcr.io niet bereikt, of geen eigen bouwstraat heeft, kan een deel van PodiumD en G4
   niet draaien. Versies in de VCG-basisset kloppen niet altijd (Operaton 2.1.12 en
   OpenFTV bestaan niet als zodanig).
7. **Alle vier de smaken passen op een machine van 16 GB**, met 7 tot 9 GiB geheugen. De
   zwaarste onderdelen zijn bijkomstig: ClamAV, Elasticsearch, de GZAC-backend en
   Keycloak. Een demo- of testomgeving per gemeente is dus goed haalbaar.

## Zelf draaien

```bash
scripts/stack.sh list                 # stacks met status
scripts/stack.sh up maykin            # of dimpact, g4, vcg, kern
scripts/stack.sh test maykin          # results/maykin.json en results/maykin.md
scripts/stack.sh down maykin          # stoppen en volumes wissen
scripts/stack.sh opruimen             # ongebruikte images en build-cache weg
```

Er draait steeds een stack tegelijk. Details per stack: [`stacks/README.md`](../stacks/README.md)
en `stacks/<stack>/README.md`.
