# Varianten van de demogemeente

> **Let op:** de varianten zijn vervangen door stacks (`stacks/README.md`). Variant 1 is
> stack `kern`; de inhoud van de varianten 2, 3 en 4 is verdeeld over de stacks
> `maykin`, `dimpact`, `g4` en `vcg`, die elk een landschap zijn zoals een gemeente het
> kiest. Dit document blijft staan voor de inventarisatie, inspanning, blokkades en het
> hostingadvies. Commando's: `scripts/stack.sh up|seed|test|down <naam>`.

De demogemeente groeit in stappen. Elke variant is een compose-bestand bovenop
`stacks/basis/compose.yml` en de vorige variant, met eigen seed-data en een eigen rooktest.
Zo blijft elke stap op zichzelf bruikbaar. Het einddoel is wat de Voorziening Common
Ground (VCG) gaat doen: de complete VCG-basisset, goed geconfigureerd, gekoppeld en
gevuld met fictieve data.

Overzicht (geheugen gemeten of geschat, schijf = images):

| Variant | Status | Containers | Geheugen | Schijf | Inspanning |
|---|---|---|---|---|---|
| 1 MijnServices-kern | klaar | 18 | 4,2 GiB gemeten | 8,3 GB | gedaan |
| 2 Formulieren, portaal, inloggen | gepland | ongeveer 30 | 7 tot 8 GiB | 11 GB | 5 tot 7 dagen |
| 3 Integratie en processen (IKO, Valtimo/GZAC, Operaton) | gepland | ongeveer 37 | 10 tot 12 GiB | 13 GB | 6 tot 9 dagen |
| 4 VCG-basisset compleet (incl. OpenFSC) | klaar (stack `vcg`) | 42 | 7,4 GiB gemeten | 17,7 GB (som) | gedaan |

De inspanning gaat uit van iemand die variant 1 kent. Het meeste werk zit niet in
het starten van images, maar in de koppelingen (autorisaties, notificatie-abonnementen,
OIDC-clients) en in samenhangende testdata.

## Variant 1: MijnServices-kern (klaar)

Bestanden: `stacks/kern/compose.yml` (vroeger `compose/v1-mijnservices.yml`).

| Component | Image | Rol |
|---|---|---|
| Open Zaak | `openzaak/open-zaak:1.29.0` | Zaken, Catalogi, Besluiten, Documenten, Autorisaties |
| Open Notificaties | `openzaak/open-notificaties:1.16.1` | notificaties, met celery-beat |
| Open Object | `maykinmedia/open-object:4.1.0` | Objecten en Objecttypen in een applicatie |
| Open Klant | `maykinmedia/open-klant:2.17.0` | Klantinteracties |
| Open Product | `maykinmedia/open-product:1.8.0` | producten, met de UPL |
| Referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | kanalen |
| VNG Selectielijst | `openzaak/vng-selectielijst:1.0.5` | selectielijst 2020 |
| BRP-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | RvIG-testpersonen |
| Keycloak | `keycloak/keycloak:26.4` | realm `voorbeeldstad`, DigiD-simulatie |

Bewezen:

- **Rooktest:** 18 van 18 (toen `scripts/smoke.sh`, nu categorie `rook` van
  `scripts/stack.sh test kern`), vanaf lege volumes in ruim 3 minuten.
- **ZGW-aansluitprofiel tegen de echte Open Zaak:** 3 van 5 op gedrag. De twee
  autorisatieworkflows falen zoals verwacht, omdat ZGW per applicatie autoriseert. Zie
  `aansluitprofielen/README.md`.
- **Bevindingen over Open Zaak** staan in `docs/openzaak-bevindingen.md`.

Nog niet in variant 1: een takenbron voor MijnTaken en admin-login via Keycloak. Een
portaal of Mijn-API komt erbij als plug-in (`docs/PLUGINS.md`).

## Variant 2: formulieren, portaal en inloggen

**Doel:** de inwonerkant. Een inwoner logt in met (gesimuleerde) DigiD, vult een
formulier in, dat wordt een zaak in Open Zaak, en de inwoner ziet die zaak en een taak
terug in Open Inwoner en in een portaal dat als plug-in meedraait.

| Component | Image | Opmerking |
|---|---|---|
| Open Formulieren | `openformulieren/open-forms:3.5.x` (ongeveer 435 MB) | web, worker, beat; registratie naar Open Zaak (ZGW) en Objecten API |
| Open Inwoner | `maykinmedia/open-inwoner:2.4.5` (ongeveer 360 MB) | web, worker, beat, plus Elasticsearch voor zoeken (zwaarste extra) |
| Keycloak | bestaand | extra realms of identity providers: DigiD (BSN, LoA), eHerkenning (KvK, vestiging, machtiging) |
| Notificatie-consumers | Open Inwoner, Open Formulieren | abonnementen op `zaken` en `objecten` in Open Notificaties |

Werk:

1. **Keycloak.** DigiD en eHerkenning als twee simulaties: eHerkenning-gebruikers met
   fictieve KvK-nummers (uit de KvK-testreeks) en vestigingsnummers. Open Formulieren en
   Open Inwoner koppelen via OIDC (beide hebben `mozilla-django-oidc` met DigiD- en
   eHerkenning-claims), een portaal als plug-in via de DigiD-simulatie (`docs/PLUGINS.md`).
2. **Open Formulieren.** Vier formulieren, een per zaaktype, met registratie naar Open
   Zaak plus documenten. Prefill uit de BRP-mock (Haal Centraal) en Open Klant.
3. **Open Inwoner.** Koppelen aan Open Zaak, Open Klant, Objecten (taken als objecttype
   "Externe taak") en Open Producten. Notificatie-abonnement zodat statuswijzigingen
   doorkomen.
4. **Takenbron.** Taken als objecten (objecttype "Externe taak", zoals Open Inwoner en
   Open Formulieren die gebruiken). Een Mijn-API die die bron leest, kan MijnTaken next
   dan volledig halen.
5. **Rooktest.** Een formulier invullen via de API van Open Formulieren en controleren
   dat de zaak, het document en de notificatie in Open Inwoner aankomen.

Blokkades en risico's:

- **eHerkenning:** het machtigingsmodel (wie handelt namens wie) is in Keycloak alleen
  met eigen claims na te bootsen. Voor een demo genoeg; het is geen echte broker.
- **Open Inwoner:** heeft veel configuratie in de admin (CMS-pagina's, categorieën).
  setup-configuration dekt niet alles, dus een deel wordt een fixture.
- **Elasticsearch:** kost ongeveer 1 GiB geheugen. Uitzetten kan, maar dan werkt
  zoeken niet.

## Variant 3: integratie en processen (IKO, Valtimo/GZAC, Operaton, "Plein")

**Doel:** de medewerkerkant en een integratielaag. Een zaak uit variant 2 wordt in een
zaakafhandelcomponent behandeld met een BPMN-proces, en een integratielaag levert één
klant- en objectbeeld over alle registers.

| Component | Image | Opmerking |
|---|---|---|
| IKO (Integraal Klant- en Objectbeeld, Ritense) | broncode 1.5.0 (`ritense/iko` op Docker Hub is maar 0.3.0) | Kotlin/Spring Boot met Apache Camel; connectoren naar BRP, Open Zaak, Open Klant, Objecten; Keycloak voor beheer |
| Valtimo/GZAC (Ritense) | `ritense/gzac-backend:13.48.0` (ongeveer 360 MB), `ritense/gzac-frontend:13.48.0` | zaakafhandeling op ZGW, met ingebouwde BPMN-engine |
| Operaton | `operaton/operaton:2.1.5` (ongeveer 290 MB) | losse BPMN-engine (fork van Camunda 7) voor processen buiten GZAC |
| Operaton Modeler | nog uitzoeken | geen image `operaton/modeler` op Docker Hub |
| "Plein" | onbekend | zie de open vraag hieronder |

Werk:

1. **IKO bouwen.** Uit de broncode (JDK 21, Gradle) met de `Dockerfile` in de
   repository, of uit ghcr.io als dat bereikbaar is. Connectoren configureren op de
   interne hostnamen. Let op D1 in `docs/openzaak-bevindingen.md`: IKO moet Open Zaak
   onder `openzaak.local:8000` aanroepen.
2. **GZAC.** Koppelen aan Open Zaak, Objecten, Open Klant en Open Notificaties, met
   Keycloak-realm voor medewerkers. Een proces per zaaktype (aanvraag beoordelen,
   besluit nemen) dat statussen in Open Zaak zet.
3. **Operaton.** Los draaien met een voorbeeldproces dat taken als objecten aanmaakt
   (die Open Inwoner en andere portalen tonen).
4. **Rooktest.** Zaak aanmaken, proces starten, taak afronden, status in Open Zaak
   controleren, klantbeeld in IKO opvragen.

Blokkades en risico's:

- **Geen recent image van IKO.** Bouwen kost een paar minuten en een JDK-buildimage.
- **Operaton-versie.** De VCG-basisset noemt Operaton 2.1.12 en Modeler 1.2.0. Op Docker
  Hub is 2.1.5 de nieuwste release (2.2.0-RC1 bestaat). Waarschijnlijk zijn 2.1.12 en
  1.2.0 versies van Helm-charts; dat moet worden nagegaan in de basisset zelf
  (code.overheid.nl was vanuit de bouwomgeving niet bereikbaar).
- **GZAC heeft een eigen BPMN-engine.** Of Operaton daarnaast nodig is, hangt af van wat
  de demo moet laten zien. Twee engines naast elkaar is verwarrend.
- **Java-componenten** (Keycloak, GZAC, IKO, Operaton) zijn de grootste geheugengebruikers.

### Open vraag: wat is "Plein"?

Gevonden: niets dat zeker klopt. "Plein" staat niet in de componentenlijst van de
VCG-basisset en niet in de bronnen van Ritense (IKO, GZAC). Er is ook geen image of
repository met die naam bij Docker Hub, Maykin, Ritense of in de PodiumD-documentatie.
Zoeken op het web gaf geen product van die naam.

Mogelijkheden om na te vragen:

- een nieuw (nog niet open) product of een werknaam bij VNG of de VCG;
- een verwarring met PodiumD (Dimpact), dat ook een geïntegreerde set Common
  Ground-componenten levert;
- een andere naam voor de integratielaag die IKO vult.

Voorstel: vraag het na bij wie "Plein" noemde, en bouw variant 3 eerst met IKO. Als
Plein een integratielaag op dezelfde API's is, kan het daarna naast IKO met dezelfde
testdata.

## Variant 4: VCG-basisset compleet

**Uitkomst (stack `vcg`, zie `stacks/vcg/README.md`):** alle componenten draaien en
zijn getest, behalve Operaton Modeler (een desktopapplicatie) en OpenFTV (geen
implementatie gevonden). OpenPlan, WordPress met OpenPDC en OpenPub, en Nextcloud met
OpenRegister zijn uit de broncode gebouwd; OpenFSC 2.4.0 draait met drie fictieve peers
en een eigen test-PKI. Operaton bleek 2.1.5 te zijn (2.1.12 bestaat niet). De rest van
deze paragraaf is de oorspronkelijke inventarisatie.

**Doel:** alles uit de VCG-basisset naast elkaar, met FSC voor het verkeer tussen
organisaties, zodat de demogemeente laat zien wat de VCG straks levert.

Bovenop variant 3:

| Component (VCG-versie) | Image | Opmerking |
|---|---|---|
| OpenFSC-suite 2.4.0 | nog uitzoeken (opvolger van NLX; images bij GitLab, niet Docker Hub) | manager, inway, outway, directory, controller; met fictieve organisaties en een eigen test-CA |
| Open Organisatie 0.2.0 | `maykinmedia/open-organisatie:0.2.0` (ongeveer 165 MB) | medewerkers en afdelingen van Voorbeeldstad |
| Open Beheer 0.9.0 | `maykinmedia/open-beheer:0.9.0` (ongeveer 130 MB) | beheer van catalogi en zaaktypen |
| OpenPlan 0.1.0 | nog uitzoeken | geen image gevonden |
| GPP-publicatiebank 2.1.0 | `maykinmedia/woo-publications:2.1.0` (ongeveer 155 MB) | Woo-publicaties; voorbeelddocumenten uit Open Zaak |
| OpenPub 3.8.7, OpenPDC 3.18.1 | WordPress-plugins (Yard) | WordPress plus MySQL of MariaDB; OpenPDC naast of in plaats van Open Product |
| OpenRegister 1.0.3 | Nextcloud-app (Conduction) | `nextcloud` met de app; registers en schema's |
| OpenFTV 1.26.14 | nog uitzoeken | |

Werk:

1. **FSC.** Twee of drie fictieve organisaties (Voorbeeldstad, een buurgemeente,
   een "Rijksdienst") met elk een inway/outway, een directory en contracten. Een portaal of
   IKO haalt dan BRP-gegevens via een outway in plaats van rechtstreeks.
2. **Inventarisatie.** Per component nagaan of er een image is en hoe het
   configureert. Waar alleen een Helm-chart bestaat: compose afleiden uit de chart.
3. **Samenhang van de data.** Medewerkers in Open Organisatie zijn dezelfde als de
   behandelaars in de zaken; publicaties verwijzen naar zaken en besluiten.

Blokkades en risico's:

- **Versies en images** van OpenPlan, OpenFTV, Operaton Modeler en de OpenFSC-suite zijn
  nog onbekend. De basisset zelf (code.overheid.nl) moet daarvoor bereikbaar zijn.
- **FSC vraagt PKI.** Een eigen test-CA per demo met certificaten per organisatie.
  Uitvoerbaar, maar het meeste werk van deze variant.
- **Footprint.** Rond de 15 GiB geheugen. Op een laptop krap, op een VM prima.

## Hosting: een demo die altijd aan staat

### Advies: begin met één VM met Docker Compose

| | Eén VM met compose | Kubernetes (Haven) |
|---|---|---|
| Opzet | `scripts/stack.sh up <naam>` op een VM, reverse proxy met TLS (Caddy of Traefik) ervoor | Helm-charts van Maykin en Ritense, Haven-compliant cluster |
| Kosten | 1 VM: 8 vCPU en 32 GB voor variant 4 (variant 1 en 2: 4 vCPU en 16 GB) | cluster plus beheer, al snel enkele keren duurder |
| Gelijkenis met VCG | laag: VCG draait op Haven met Helm | hoog: zelfde charts en manier van uitrollen |
| Beheer | eenvoudig; reset is `scripts/stack.sh down` en `up` | meer bewegende delen, maar standaard tooling |
| Geschikt voor | demo's, workshops, conformancetests, ontwikkelaars | proefdraaien van de VCG-uitrol zelf |

Voorstel:

1. **Nu: één VM met compose.** Bijvoorbeeld in een Nederlandse cloud, met:
   - een subdomein per component (`openzaak.demo.voorbeeldstad.nl`, ...) achter Caddy,
     dat automatisch Let's Encrypt doet;
   - die publieke hostnamen als canonieke URL's in `ALLOWED_HOSTS`, `SITE_DOMAIN` en de
     autorisaties (zie D1 in `docs/openzaak-bevindingen.md`);
   - een nachtelijke `scripts/stack.sh down` en `up` plus `scripts/stack.sh test`, zodat bezoekers altijd
     dezelfde schone data zien, en een melding als de rooktest faalt.
2. **Beveiliging, ook al is de data fictief.** Beheer-admins en Keycloak-beheer alleen
   via een VPN of IP-allowlist. Een testlogin van een plug-in (tokens voor elk BSN) alleen
   als bewuste keuze ("iedereen kan als elke testburger inloggen"); anders de
   DigiD-simulatie in Keycloak gebruiken. Wekelijks nieuwe
   images, met vaste versies uit de basisset.
3. **Later: een Haven-variant** naast de VM, met de Helm-charts. Dat is pas zinvol als
   de demo ook moet laten zien hoe de VCG uitrolt. De seed-scripts en rooktests werken
   dan ongewijzigd (ze praten alleen met de API's), alleen de interne hostnamen
   veranderen.

Inspanning voor de VM-opzet: 2 tot 3 dagen (proxy, DNS, TLS, canonieke hostnamen,
reset en monitoring).
