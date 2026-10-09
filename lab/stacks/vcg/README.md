# Stack vcg: de VCG-basisset

Een gemeente die zegt: "wij nemen de spullen uit de VCG-basisset" (de componentenlijst
van de Voorziening Common Ground). Bovenop de registers van de kern (Open Zaak, Open
Notificaties, Open Object, Open Klant, Open Product, Selectielijst, Referentielijsten)
draaien Open Organisatie, de GPP-publicatiebank, Open Beheer,
Operaton, OpenPlan, OpenPDC, OpenPub, OpenRegister en OpenFSC, en ze zijn aan elkaar
gekoppeld zoals een gemeente dat zou doen.

```bash
scripts/stack.sh up vcg      # images bouwen die ontbreken, starten, wachten, testdata laden
scripts/stack.sh test vcg    # results/vcg.json en results/vcg.md
scripts/stack.sh down vcg
```

Alles wordt automatisch ingericht: setup-configuration (YAML) en kleine Django-scripts
voor de Maykin-componenten, een realm-script voor Keycloak, `default.yml` en een BPMN-
bestand voor Operaton, wp-cli voor WordPress, de installatievariabelen van Nextcloud,
een test-PKI voor OpenFSC en idempotente seedscripts. Er is geen handwerk in een admin
nodig. Achter een proxy met TLS-inspectie: `EXTRA_CA_CERT=/pad/naar/ca-bundle.crt
scripts/stack.sh up vcg` (alleen nodig als er iets gebouwd moet worden).

**Status: werkt.** Alle componenten die hier kunnen draaien, draaien en zijn getest.
Operaton Modeler en OpenFTV zijn niet draaibaar (zie hieronder).

## Componenten

| Component (VCG-versie) | Image | Host-poort | Intern adres | Status |
|---|---|---|---|---|
| Kern: Open Zaak, Open Notificaties, Open Object, Open Klant, Open Product, Selectielijst, Referentielijsten | zie `stacks/kern/README.md` | | | draait en getest |
| Open Organisatie 0.2.0 | `maykinmedia/open-organisatie:0.2.0` | 8251 | `openorganisatie.local:8000` | draait en getest |
| GPP-publicatiebank 2.1.0 | `maykinmedia/woo-publications:2.1.0` | 8252 | `publicatiebank.local:8000` | draait en getest |
| Open Beheer 0.9.0 | `maykinmedia/open-beheer:0.9.0` plus `nginx:1.29.8-alpine` voor de frontend | 8155 | `openbeheer.local:8000` | draait en getest |
| Operaton 2.1.5 (basisset noemt 2.1.12) | `operaton/operaton:2.1.5` | 8254 | `operaton.local:8080` | draait en getest |
| Procesworker Operaton naar Open Zaak | `openzaak/open-zaak:1.29.0` met `tools/operaton_worker.py` | | | draait en getest |
| OpenPlan 0.1.0 | `demogemeente/openplan:0.1.0` (gebouwd) | 8255 | `openplan.local:8000` | draait en getest |
| OpenPDC 3.18.1 en OpenPub 3.8.7 | `demogemeente/wordpress-owc:6.8.3` (gebouwd) met `mariadb:11.8.3` | 8256 | `wordpress.local` | draait en getest |
| OpenRegister 1.0.3 | `demogemeente/openregister:1.0.3` (gebouwd, Nextcloud 31.0.9) | 8257 | `openregister.local` | draait en getest |
| OpenFSC 2.4.0 (directory, manager, controller, inway, outway, txlog) | `federatedserviceconnectivity/*:v2.4.0` | 8260, 8261, 8262 (controller-UI's) | `*.fsc.local` | draait en getest |
| Keycloak-realm `vcg` (medewerkers) | kern-Keycloak 26.4.7 | 8080 | `keycloak.local:8080` | draait en getest |
| Operaton Modeler 1.2.0 | | | | niet draaibaar |
| OpenFTV 1.26.14 | | | | niet draaibaar |

### Niet draaibaar

| Component | Waarom niet | Wat nodig is |
|---|---|---|
| Operaton Modeler 1.2.0 | Een desktopapplicatie (Electron) om BPMN en DMN te tekenen; geen server of container. | Niets voor de stack: wie processen wil tekenen, installeert de Modeler lokaal. Het proces in `config/operaton/resources/` is met de hand geschreven en staat bij de start in Operaton. |
| OpenFTV 1.26.14 | Geen implementatie gevonden. De link in de basisset wijst naar ZaakBrug, en 1.26.14 is een versienummer van ZaakBrug. FTV (Federatieve Toegangsverlening) is een standaard op basis van AuthZEN, geen product. | Een bron of image van de bedoelde component. OpenFSC kan al een AuthZEN-beslispunt aanroepen (`--authzen-service-address` op in- en outway); zodra er een FTV-implementatie is, past die daar. |

Beide staan in `stack.yaml` onder `gepland`; het rapport toont ze als overgeslagen met
deze reden.

### Zelf gebouwd

`stacks/vcg/bouw.sh` bouwt wat geen bruikbaar image heeft, op een vaste versie, en maakt
eenmalig de test-PKI voor OpenFSC. `scripts/stack.sh up` roept het aan en bouwt alleen
wat ontbreekt; broncode komt in `.bron/` (niet in git).

- **OpenPlan 0.1.0** (`maykinmedia/open-plan`): geen image en geen git-tags. Gebouwd op
  commit `b1f945de` (README-versie 0.1.0), met de frontend (Node) en het image van Open
  Organisatie 0.2.0 als basis (zelfde Django-stack).
- **WordPress 6.8.3 met OpenPDC en OpenPub** (OpenWebconcept): de plugins en wat ze
  vereisen (Meta Box 5.10.10, CMB2 2.11.0, Posts 2 Posts 1.6.5) komen uit GitHub, de
  PHP-afhankelijkheden uit Packagist. wordpress.org is hier niet bereikbaar.
  **Meta Box Group** (vereist door OpenPDC) staat alleen op wordpress.org en metabox.io;
  in plaats daarvan zit er een kleine vervanger in het image
  (`bouw/wordpress/meta-box-group/`). Groepvelden in de beheerschermen van OpenPDC
  vallen daardoor terug op gewone velden; de REST-API werkt.
- **Nextcloud 31.0.9 met OpenRegister 1.0.3** (Conduction): de app store van Nextcloud
  is hier niet bereikbaar, dus de app wordt gebouwd uit tag `v1.0.3` (Composer en
  npm/webpack). Let op: die tag noemt zichzelf in `appinfo/info.xml` versie
  `0.2.13-unstable.78`.

## Gebruikers

| Wie | Waar | Inloggen |
|---|---|---|
| Beheerder | Django-admins, Operaton, WordPress, Nextcloud | `admin` met `ADMIN_PASSWORD` uit `.env` |
| Medewerkers (realm `vcg`) | Open Beheer, Open Organisatie (OIDC); Operaton (eigen gebruikers met dezelfde naam) | gebruikersnaam hieronder, `MEDEWERKER_WACHTWOORD` |
| Burgers | alleen openbare kanalen; een burgerportaal kan als plug-in (`docs/PLUGINS.md`) | DigiD-simulatie (realm `voorbeeldstad`) |

| Gebruiker | Wie (fictief) | Realmrollen | Team in Open Organisatie |
|---|---|---|---|
| `a.vermeulen` | Anouk Vermeulen | Behandelaar | Vergunningen |
| `s.bakker` | Sander Bakker | Behandelaar | Buitendienst |
| `r.vandijk` | Rachid van Dijk | Behandelaar | Wmo |
| `l.smits` | Lotte Smits | Behandelaar | Parkeren (ook Operaton-groep `parkeren`) |
| `beheer.devos` | Mirjam de Vos | Functioneel-Beheerder, Superuser | Functioneel beheer |

Alleen `beheer.devos` komt in Open Beheer en de admin van Open Organisatie: de inlogflow
`beheer-browser` van realm `vcg` weigert iedereen zonder de rol Functioneel-Beheerder
(zie Bevindingen, punt 1).

## Koppelingen

```
 medewerker --OIDC (realm vcg, rolcontrole)--> Open Beheer --Catalogi API--> Open Zaak
                                         \--> Open Organisatie --notificaties--> Open Notificaties (kanaal medewerkers)

 Open Zaak (zaak parkeervergunning) <--ZGW-- procesworker <--fetchAndLock-- Operaton
                                               |                (proces Parkeervergunning behandelen)
                                               +--> Open Organisatie (behandelaar uit team Parkeren)

 GPP-publicatiebank --Documenten API--> Open Zaak       OpenPlan: plannen met URN's naar zaken,
                    (Catalogi van de publicatiebank       medewerkers (Open Organisatie) en BSN's
                     staan als dienst in Open Zaak)

 openbaar: OpenPDC en OpenPub (WordPress REST), GPP-publicatiebank (leestoken), OpenRegister

 OpenFSC-testgroep "fsc-voorbeeldstad":
   app van Voorbeeldstad --> outway (Voorbeeldstad) ==mTLS + token==> inway (BRP-leverancier Testland) --> BRP-mock
                              |                                         |
                              manager, controller, txlog               manager, controller, txlog
                                          \--------- directory ---------/
```

- **Open Organisatie.** Afdelingen, teams en medewerkers van Voorbeeldstad. Dezelfde
  medewerkers (`mdw-0101` tot en met `mdw-0404`) zijn behandelaar op de geseede zaken en
  bestaan als gebruiker in Keycloak-realm `vcg` en in Operaton. Open Organisatie
  publiceert wijzigingen op het kanaal `medewerkers` van Open Notificaties (ZGW-client
  `open-organisatie`); de notificatie-sink van de kern is abonnee.
- **GPP-publicatiebank.** Organisatie Gemeente Voorbeeldstad en twee Woo-publicaties
  (een beschikking en een vergaderstuk) met een PDF. De documenten staan in de
  Documenten API van Open Zaak (ZGW-client `gpp-publicatiebank`); Open Zaak kent de
  catalogus van de publicatiebank als dienst. Twee tokens: beheer (lezen en schrijven) en
  publiek (alleen lezen).
- **Open Beheer.** Beheert de zaaktypen in de Catalogi API van Open Zaak (ZGW-client
  `open-beheer`). Het image bevat de React-frontend, maar het backend serveert op `/`
  alleen een tekstpagina; `openbeheer-ui` (nginx, `config/openbeheer/nginx.conf`) zet de
  frontend op `/` en stuurt API, admin, OIDC en statische bestanden door.
- **Operaton.** Proces `parkeervergunning-behandelen`: externe taak
  `zaak-in-behandeling`, gebruikerstaak "Aanvraag beoordelen" (groep `parkeren`), externe
  taak `zaak-afhandelen`. De procesworker (`tools/operaton_worker.py`, ZGW-client
  `operaton`) zet de status "In behandeling" en de behandelaar uit Open Organisatie op de
  zaak, en na het besluit het resultaat (Geleverd of Niet geleverd) en de eindstatus
  "Afgehandeld". De seed start het proces voor zaak `VBS-2026-000110` van testburger D.
- **OpenPlan.** Plannen in het sociaal domein (werk en inkomen) voor burgers C en B, met
  een doel en een instrument. Verwijzingen zijn URN's: zaak
  (`urn:nl:gemeenten:zaak:VBS-2026-000105`), medewerker
  (`urn:nld:voorbeeldstad:medewerker:mdw-0303`), persoon met BSN.
- **OpenPDC en OpenPub.** Drie producten en diensten (parkeervergunning, paspoort,
  huishoudelijke hulp) onder drie thema's, met de UPL-naam als metadata; twee
  nieuwsberichten. Alleen openbare informatie.
- **OpenRegister.** Register `openbare-ruimte` met schema `speelplek` en drie
  speelplekken; objecten worden tegen het schema gevalideerd.
- **OpenFSC.** Drie fictieve peers in een eigen FSC-groep: de directory
  (`00000099000000000000`), Gemeente Voorbeeldstad (`...01`, afnemer, outway) en
  BRP-leverancier Testland (`...02`, aanbieder van dienst `brp-personen` via een inway
  voor de BRP-mock). Elke peer heeft een manager, een controller, een eigen database en
  (behalve de directory) een transactielog. De seed registreert de dienst, publiceert hem
  in de directory, vraagt namens Voorbeeldstad een verbinding aan voor de eigen outway
  (op basis van de vingerafdruk van de publieke sleutel) en tekent het contract namens
  de aanbieder. Daarna vraagt een applicatie van Voorbeeldstad met
  `Fsc-Grant-Hash: <hash>` een persoon op bij de outway.
- **Test-PKI.** `stacks/vcg/fsc-pki.sh` maakt een groeps-CA (certificaten met
  organisatie en peer-id in het subject) en per organisatie een interne CA, plus een
  beheercertificaat waarmee seed en tests de beheer-API's (mTLS) aanroepen. Alles staat
  in `stacks/vcg/.fsc-pki/` (niet in git).

## Configuratie

| Waar | Wat |
|---|---|
| `stacks/vcg/compose.yml` | services, init-containers, aanvullingen op de kern (Open Zaak, Open Notificaties) |
| `stacks/vcg/stack.env` | extra databases (onder meer acht voor OpenFSC), hostpoorten 8250 tot en met 8299 |
| `stacks/vcg/env.example` | geheimen (`__GENEREER__`), `up` vult `.env` aan |
| `stacks/vcg/bouw.sh`, `bouw/`, `fsc-pki.sh` | OpenPlan, WordPress en OpenRegister uit broncode; test-PKI voor OpenFSC |
| `config/keycloak-vcg/` | realm `vcg`: clients `openbeheer` en `openorganisatie`, rollen, medewerkers, inlogflow `beheer-browser` |
| `config/openorganisatie/` | setup-configuration (Open Notificaties, OIDC) en API-token |
| `config/publicatiebank/configureer.py` | Documenten API, globale instellingen, twee API-tokens |
| `config/openbeheer/` | setup-configuration (Open Zaak, Objecttypen, OIDC) en nginx voor de frontend |
| `config/operaton/` | `default.yml` (database, beheerder, autorisatie) en het BPMN-proces |
| `config/openplan/tokens.py` | API-token |
| `config/wordpress/inrichting.sh` | wp-cli: installatie, plugins, thema's, producten, berichten |
| `config/{openzaak,opennotificaties}/stack-vcg.yaml` | ZGW-clients en applicaties, kanaal `medewerkers`, abonnement |
| `tools/operaton_worker.py` | procesworker Operaton naar Open Zaak |
| `stacks/vcg/seed.py`, `fsc.py` | testdata (idempotent) en de FSC-hulpfuncties |
| `stacks/vcg/tests.py`, `screenshots.mjs` | rooktests en isolatietype `openbaar`; screenshots |

## Testresultaten

Zonder plug-ins: **69 geslaagd, 7 gefaald (alle 7 bekend), 6 overgeslagen**. Afgeleid van
`scripts/stack.sh test vcg` op een schone start (lege volumes, 8 oktober 2026); zie
`results/vcg.md`. Na het toevoegen van `openbeheer-ui` is de suite opnieuw gedraaid op
dezelfde stack, met dezelfde uitkomst.

| Categorie | Geslaagd | Gefaald (bekend) | Overgeslagen |
|---|---|---|---|
| gezondheid | 22 | 0 | 2 (Operaton Modeler, OpenFTV) |
| rook | 38 | 0 | 3 (infra) |
| zgw | 3 | 7 (7) | 0 |
| burger-isolatie | 6 | 0 | 0 |
| mijn-apis | 0 | 0 | 1 (geen plug-in met een Mijn-API) |

De 7 bekende ZGW-fouten zijn die van de kern (Open Zaak 1.29 tegen het aansluitprofiel).
Rooktests van deze stack (19, alle geslaagd):

| Component | Wat de test bewijst |
|---|---|
| Keycloak-realm vcg | `beheer.devos` logt via OIDC in bij de admin van Open Organisatie |
| Open Organisatie | 3 afdelingen, 5 teams, 5 medewerkers; een wijziging van een medewerker komt binnen 2,1 s via Open Notificaties bij de abonnee |
| GPP-publicatiebank | 2 publicaties; beide documenten staan in de Documenten API van Open Zaak en zijn als PDF te downloaden; het leestoken kan niet schrijven (403) |
| Open Beheer | `beheer.devos` ziet de 4 zaaktypen van Open Zaak; behandelaar `a.vermeulen` wordt bij de login geweigerd |
| Operaton | `l.smits` claimt en rondt "Aanvraag beoordelen" af; de worker zet resultaat Geleverd, de behandelaar (`mdw-0404`) en de einddatum op zaak `VBS-2026-000110`; zonder inlog 401 |
| OpenPlan | 2 plannen met doel en instrument, verwijzend naar `VBS-2026-000104` en `-000105`; zonder token 401 |
| OpenPDC, OpenPub | 3 producten, gekoppeld aan een thema (Posts 2 Posts); 2 nieuwsberichten |
| OpenRegister | 3 speelplekken; een ongeldig object wordt geweigerd (400); zonder inlog een lege lijst |
| OpenFSC | 10 componenten gereed; publicatie en verbinding geldig en door beide peers getekend; persoon opgevraagd via outway en inway, met dezelfde transactie in de log van afnemer en aanbieder; zonder grant 400, inway zonder clientcertificaat geweigerd in de TLS-handshake |

### Isolatie

De VCG-basisset heeft zelf geen burgerportaal. De burgerkanalen in deze stack zijn:

- **Openbare kanalen** (isolatietype `openbaar`): de REST-API's van OpenPDC (items,
  thema's) en OpenPub, de publicaties en documenten van de GPP-publicatiebank met het
  leestoken, en de objecten van OpenRegister zonder inlog. Geen van de zes antwoorden
  bevat een BSN of naam van een testburger.
- **Medewerkerskanalen.** OpenPlan bevat BSN's (personen bij een plan) en geeft zonder
  token 401. Open Beheer en Open Organisatie weigeren een behandelaar zonder beheerrol al
  bij de login.

## Bevindingen

1. **Open Beheer: elke ingelogde gebruiker mag zaaktypen beheren.** De API van Open
   Beheer 0.9.0 controleert alleen of iemand is ingelogd (DRF `IsAuthenticated`), niet
   welke rol hij heeft. Met `make_users_staff` uit de OIDC-configuratie kon behandelaar
   `a.vermeulen` daardoor zaaktypen lezen en wijzigen. Oplossing in deze stack: de
   clients `openbeheer` en `openorganisatie` gebruiken in Keycloak de inlogflow
   `beheer-browser`, die na het inloggen iedereen zonder de realmrol
   Functioneel-Beheerder weigert ("Alleen functioneel beheerders hebben toegang tot deze
   beheeromgeving."). Een gemeente moet dit zelf regelen; Open Beheer doet het niet.
2. **Open Beheer: frontend niet bereikbaar.** Het image bevat de frontend, maar serveert
   hem niet op `/`. In productie zet Maykin er een webserver voor; hier doet
   `openbeheer-ui` (nginx) dat.
3. **GPP-publicatiebank: niet te snel publiceren.** Na het uploaden van een PDF haalt
   een achtergrondtaak de metadata weg: het document wordt in Open Zaak verwijderd en
   opnieuw aangemaakt. Wie de publicatie direct na het uploaden op "gepubliceerd" zet,
   botst met die taak (`ConcurrentTransition`); het document staat dan niet meer in Open
   Zaak en de upload is nooit voltooid. De seed wacht daarom tot `uploadVoltooid` waar is.
4. **Setup-configuration geeft alleen volledige autorisaties.** De applicaties in Open
   Zaak (Open Organisatie, publicatiebank, Open Beheer, Operaton) krijgen via
   setup-configuration `heeft_alle_autorisaties`; per component maar enkele scopes
   toekennen kan zo niet. Voor een echte gemeente moet dat met de hand of via de
   Autorisaties API.
5. **OpenPlan kent geen filter op BSN.** De API van personen heeft geen BSN-filter en
   een token ziet alle personen en plannen. Een portaal dat plannen aan burgers toont,
   moet dus zelf per burger filteren.
6. **Versies in de basisset.** Operaton 2.1.12 bestaat niet (nieuwste release: 2.1.5);
   OpenFTV 1.26.14 is een versie van ZaakBrug; tag `v1.0.3` van OpenRegister noemt zich
   `0.2.13-unstable.78`; Meta Box Group is alleen via wordpress.org te krijgen.
7. **OpenFSC eist vaste poorten.** Een inway moet op poort 443 staan (`self-address`
   met een andere poort wordt geweigerd), en de images hebben geen shell, dus geen
   healthcheck in compose; de tests vragen `/health/ready` op de monitoringpoort.
8. **Posts 2 Posts via wp-cli.** De plugin maakt zijn tabellen pas aan bij het openen
   van een beheerpagina. Bij activeren via wp-cli blijven koppelingen tussen producten
   en thema's leeg; `inrichting.sh` roept daarom `P2P_Storage::install()` aan.

## Footprint

Gemeten op 2026-10-08 vanaf lege volumes, images lokaal aanwezig, machine 15 GB RAM en
4 CPU. De stack past in één keer; draaien in twee helften is niet nodig.

| | |
|---|---|
| Start (`up` tot en met seed) | 309 s |
| RAM na de testsuite | 7,2 GB (41 containers); met `openbeheer-ui` 7,4 GB (42 containers) |
| Grootste verbruikers | Keycloak 0,78 GB, Operaton 0,50 GB, Nextcloud 0,50 GB, Open Zaak 0,48 GB |
| VCG-componenten samen | ongeveer 2,8 GB (zonder Keycloak uit de kern), waarvan OpenFSC (10 containers) 94 MB |
| Images van deze stack | 17,7 GB (som, gedeelde lagen dubbel geteld); zelfgebouwd: OpenRegister 3,3 GB (waarvan Nextcloud 2,1 GB), WordPress 1,15 GB, OpenPlan 1,05 GB |
| Volumes na seed en test | 2,2 GB (Nextcloud 1,5 GB) |
| Vrije schijf na `down` | 7,1 GB; na het verwijderen van de images die `up` weer ophaalt (Operaton, MariaDB, publicatiebank, Open Beheer, OpenFSC) 9,6 GB. De zelfgebouwde images blijven staan. |

Details in `results/vcg.json` onder `footprint`.

## Screenshots

In `docs/screenshots/vcg/`: Open Organisatie (medewerkers) en Open Beheer
(zaaktypen, zaaktype parkeervergunning) als `beheer.devos`; de weigering van behandelaar
`a.vermeulen` in Keycloak; Operaton Cockpit; publicatiebank; OpenPDC in WordPress;
OpenRegister in Nextcloud; de FSC-controller van Voorbeeldstad (directory en contracten).
Maken, met de stack draaiend (Chromium uit `/opt/pw-browsers`):

```bash
for v in ADMIN_USERNAME ADMIN_PASSWORD MEDEWERKER_WACHTWOORD; do
  export $v="$(grep "^$v=" .env | cut -d= -f2-)"
done
NODE_PATH=$(npm root -g) node stacks/vcg/screenshots.mjs
```
