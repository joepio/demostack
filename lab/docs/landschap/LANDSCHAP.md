# Softwarelandschap gemeentelijke dienstverlening en Common Ground

*Overzicht van de open source componenten, platforms en standaarden rond gemeentelijke dienstverlening en Common Ground, als achtergrond bij de stacks van DemoStack. Peildatum 7 oktober 2026. Machineleesbare versie: `landschap.json` (zelfde velden).*

**Methode.** Versies uit `git ls-remote` (tags), Docker Hub API en GHCR-tags-API, zelf opgevraagd op 7-10-2026. Repo's gekloond (shallow) voor licentie, README en Helm-chart-inhoud. De VCG-basisset gelezen via code.overheid.nl (README gegenereerd 07-07-2026, basisset v0.1.0). PodiumD-samenstelling uit de Helm-chart `podiumd` 4.9.3 (Dimpact-Samenwerking/helm-charts). G4-architectuur uit de gitbook *Platform Generieke Dienstverlening*. Een paar adoptiecijfers komen uit een niet-openbare marktscan (GEMMA-export 13-07-2026); die staan steeds als zodanig gemarkeerd en zijn niet zelf nagekeken. Productieaantallen alleen opgenomen waar een bron ze noemt; anders "onbekend".

**Niet bereikbaar:** commonground.nl, componentencatalogus.commonground.nl, vng.nl, developer.overheid.nl en dimpact.nl via curl (proxy); een deel wel via WebFetch. GitHub REST-API geblokkeerd voor niet-gekoppelde repo's (git-protocol werkte wel). codeberg.org geblokkeerd. Notion-roadmap van Platform Dienstverlening niet leesbaar.

## 1. Samenvatting: wat valt op

1. **De datalaag is af, de burgerlaag niet.** Laag 1-2 (Open Zaak, OpenKlant, Objecten, Open Product, Open VTB) is vrijwel geheel Maykin, EUPL, actief onderhouden (releases in de afgelopen weken) en staat grotendeels in de VCG-basisset. In de VCG-basisset zit **geen enkel burgerportaal en geen formulierencomponent**: laag 5 bevat alleen OpenBeheer en Operaton (Modeler).
2. **Twee kampen in laag 5.** Dimpact/PodiumD (44 leden volgens niet-openbare marktscan; ZAC-README: "more than 40") kiest **Open Inwoner** (Maykin, Django, server-rendered) + **KISS** + **Open Formulieren**. De G4 (Platform Dienstverlening, opdrachtgever: programmamanagers Common Ground G4) kiest in de SBB-mapping **NL Portal** (Ritense) + **IKO** (Ritense) + **GZAC** + Open Formulieren.
3. **IKO is de integratielaag die de G4 al heeft gekozen.** IKO 1.5.1 (EUPL, Kotlin/Camel, actief) staat als "Integrated customer/object views" in laag 5 van de G4-architectuur. Het genoemde "API framework" van G4 + Dimpact op de IKO-engine is **publiek niet terug te vinden**; wel bevestigd dat IKO de G4-bouwsteen is.
4. **Taken en berichten verhuizen.** Vandaag staan burgertaken en -berichten als generieke objecten in de Objecten API (NL Portal-patroon). Het G4-platform introduceert **Open VTB** (Maykin, 0.2.0, 6-10-2026) met Verzoeken/Taken/Berichten-API's. Dat wordt de kernbron voor "Mijn taken" en "Mijn berichten".
5. **Contracten zijn nog vloeibaar.** ZGW 1.7 is vastgesteld (9-6-2026), maar Klantinteracties is formeel *niet* vastgesteld ("halfproduct", "beproeving"), Producten en Referentielijsten zijn concept, VTB is een concept, en de VNG Interactie-API's (MijnServices) zijn pre-alfa.
6. **Per-burger-autorisatie ontbreekt overal in de standaarden.** ZGW kent alleen applicatie-autorisatie; elke portaalbouwer filtert zelf op `rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn`. De nieuwe Logius-standaard FTV/AuthZEN (definitief 25-6-2026) en het VCG-item "OpenFTV" zijn de plek waar dit landt, maar een implementatie is niet gevonden (de VCG-link wijst naar ZaakBrug, vermoedelijk een fout).
7. **De VCG-lijst loopt achter of bevat fouten.** Gepinde versies liggen 1 tot 4 minors achter (OpenKlant 2.17 vs 2.19.1, OpenFSC 2.4.0 vs 2.8.0, OpenRegister 1.0.3 vs 2.1.0). Operaton "2.1.12" bestaat niet als tag (laatste 2.1.5). OpenFTV verwijst naar de verkeerde repo.

### Het Common Ground 5-lagenmodel (zoals hier gebruikt)

| Laag | Inhoud | Voorbeelden |
|---|---|---|
| 5 Interactie | Burger- en medewerkerapplicaties | Open Inwoner, NL Portal, KISS, ZAC |
| 4 Proces | Procesengines, zaakafhandeling | Operaton, Valtimo/GZAC |
| 3 Integratie | Gateways, notificaties, federatie | OpenFSC, OpenNotificaties, IKO, OMC |
| 2 Services | API's | ZGW, Klantinteracties, Objecten, BRP |
| 1 Data | Registers | Open Zaak, OpenKlant, Open Product, Open VTB |

## 2. Kaart per laag

### Platforms (alle lagen)

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| PodiumD (platform) | Dimpact (coöperatie van gemeenten) | Helm-chart podiumd 4.9.3 | nee | ja |
| Platform (Generieke) Dienstverlening (G4 + Dimpact) | Opdrachtgever: programmamanagers Common Ground van de G4 | gitbook | nee | nee |

### Laag 5 (en 4) interactie

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| OpenBeheer | Maykin | 0.9.1 | ja | ja |
| Open Inwoner | Maykin (opengem.nl) | 2.4.5 | nee | ja |
| Open Formulieren | Maykin | 4.0.1 | nee | ja |
| MijnOverheid (Berichtenbox, Lopende Zaken, MijnGegevens) | Logius (Rijk) | n.v.t. | nee | nee |
| ZAC (Zaakafhandelcomponent) | ICATT (Info.nl) | 5.9.1 | nee | ja |
| KISS (Klantinteractie-Servicesysteem) | KISS-community | 3.2.0 | nee | ja |
| ITA (Interne Taakafhandeling / Contactverzoek) | KISS-community (Oost Gelre e.a.) | 3.3.3 | nee | ja |
| Signalen | Ontstaan bij Amsterdam | backend 2.50.20 | nee | nee |
| NL Portal | Ritense | frontend v3.0.3, backend 3.0.4.RELEASE | nee | nee |
| Mijn Services (NLDS-community templates) | NL Design System-community / VNG Project Omnichannel | geen releases | nee | nee |
| NL Design System | NL Design System-community | per pakket | nee | nee |
| Mijn Amsterdam | Gemeente Amsterdam | geen semver-releases | nee | nee |
| Open Archiefbeheer | Maykin | 2.1.0 | nee | ja |

### Laag 4 proces

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| Operaton | Operaton-community (fork van Camunda 7 CE) | 2.1.5 | ja | nee |
| Operaton Modeler | Operaton-community (port van Fluxnova/Camunda Modeler) | geen git tags | ja | nee |
| Valtimo / GZAC | Ritense (GZAC = Valtimo-distributie voor zaakgericht werken) | 13.48.0 | nee | nee |

### Laag 3 integratie

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| OpenFSC (Inway, Outway, Manager, Directory) | RINIS (rinis-oss) | v2.8.0 | ja | nee |
| OpenNotificaties | Maykin (Open Zaak-community) | 1.17.0 | ja | ja |
| OpenFTV | Onduidelijk: VCG noemt 'IAM-tool' maar linkt naar github.com/wearefrank/zaakbrug | onbekend | ja | nee |
| ESB (generiek) | n.v.t. (keuze per gemeente) | n.v.t. | ja | nee |
| NotifyNL OMC (Output Management Component) | Worth Systems | 2.3.0 | nee | ja |
| IKO (Integraal Klant- en Objectbeeld) | Ritense (GitHub-org Integraal-Klant-en-Objectbeeld) | 1.5.1 | nee | nee |
| 'API framework' (G4 + Dimpact, op IKO-engine) | Onbekend | niet gevonden | nee | nee |
| ZaakBrug | WeAreFrank (opvolger Open-ZaakBrug van Súdwest-Fryslân) | 1.26.19 | nee | ja |
| Frank!Gateway (APISIX) in PodiumD | WeAreFrank (gehardende Apache APISIX-distributie) | 1.1.0 | nee | ja |
| PABC (Platform Autorisatie Beheer Component) | onbekend (GitHub-org platform-autorisatie-beheer-component) | 1.1.1 | nee | ja |
| Keycloak (identity broker) | Red Hat / CNCF-community | 26.7.3 | nee | ja |
| NLX | VNG Realisatie / Common Ground | v0.150.1 | nee | nee |
| Common Gateway / Open Catalogi (Conduction) | Conduction | opencatalogi v2.1.0 | nee | nee |

### Laag 1-2 data en services

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| OpenZaak | Maykin (ontwikkeling) | 1.30.0 | ja | ja |
| OpenKlant | Maykin | 2.19.1 | ja | ja |
| Objecten (Objects API / Open Object) | Maykin | 4.3.0 | ja | ja |
| Objecttypen | Maykin | 3.4.2 | ja | ja |
| OpenProduct | Maykin | 1.9.0 | ja | nee |
| OpenPDC | OpenWebconcept (WordPress-community) | v3.18.1 | ja | nee |
| OpenOrganisatie | Maykin | 0.2.0 | ja | nee |
| OpenPlan | Maykin | 0.1.0 | ja | nee |
| VNG-Selectielijst | Open Zaak-community (Maykin) | 1.0.5 | ja | nee |
| Referentielijsten | Maykin | 0.7.5 | ja | ja |
| GPP-publicatiebank | Maykin | 2.1.0 | ja | nee |
| OpenPub | OpenWebconcept (WordPress-community) | v3.9.4 | ja | nee |
| OpenRegister | Conduction | v2.1.0 | ja | nee |
| Open VTB (Verzoeken, Taken, Berichten) | Maykin | 0.2.0 | nee | nee |

### Standaarden en API-contracten

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| ZGW API's (Zaakgericht Werken) | VNG Realisatie | ZGW 1.7 (09-06-2026) | nee | ja |
| Klantinteracties API | VNG Realisatie (model) | niet vastgesteld (beproeving) | nee | ja |
| Notificaties API | VNG Realisatie | 1.0.1 vastgesteld | nee | ja |
| Haal Centraal BRP API Personen | RvIG (Rijksdienst voor Identiteitsgegevens) | Live | nee | ja |
| Haal Centraal BAG (BAG API Individuele Bevragingen) | Kadaster | onbekend | nee | nee |
| VNG Interactie-API's / VNG API Lab (MijnServices) | VNG Realisatie | pre-alfa | nee | nee |

### Infrastructuur en identiteit

| Component | Maker | Versie (kort) | VCG | PodiumD |
|---|---|---|---|---|
| Haven | VNG / Common Ground | v12.13.0 | nee | nee |
| Haven+ | onbekend (genoemd door VCG en Platform Dienstverlening) | onbekend | nee | nee |
| DigiD / eHerkenning / eIDAS | Logius (DigiD) | n.v.t. | nee | nee |

## 3. Componenten in detail

Per component: wat het doet, laag, licentie, repo, image + versie, standaarden, volwassenheid, VCG/PodiumD en verificatiestatus. 'Gecheckt' betekent: zelf nagekeken in repo, registry of genoemde bron op 7 oktober 2026. 'Aanname' betekent: niet bevestigd.

### Platforms (alle lagen)

#### PodiumD (platform)

- **Wat:** Assemblage van Common Ground-componenten (Open Zaak, OpenKlant, Open Formulieren, Open Inwoner, ZAC, KISS e.a.) als dienstverleningsplatform voor Dimpact-leden.
- **Maker/beheerder:** Dimpact (coöperatie van gemeenten); ontwikkelpartners Icatt/Info.nl, Maykin; hosting SSC Enschede
- **Laag:** 1-5 (platform) · **Licentie:** EUPL-1.2 (componenten); Helm-charts open
- **Repo:** https://github.com/Dimpact-Samenwerking/helm-charts
- **Image / versie:** `Helm-chart 'podiumd' (geen eigen image)` · Helm-chart podiumd 4.9.3 (laatste commit 06-10-2026)
- **Standaarden:** ZGW, Klantinteracties, Objecten, Notificaties, BRP; Keycloak OIDC
- **Volwassenheid:** Productie: ZAC 'funded by Dimpact, a coöperation of more than 40 Dutch municipalities' (ZAC-README); PodiumD Portaal live bij 5 gemeenten (niet-openbare marktscan).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: chart-inhoud en versie; ledenaantal via ZAC-README. Bronnen: <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://github.com/infonl/dimpact-zaakafhandelcomponent>

#### Platform (Generieke) Dienstverlening (G4 + Dimpact)

- **Wat:** Gezamenlijke enterprise-architectuur en referentiecomponenten voor gemeentelijke dienstverlening (verzoeken, taken, berichten, registraties).
- **Maker/beheerder:** Opdrachtgever: programmamanagers Common Ground van de G4; 'ontwikkeld in samenwerking tussen gemeenten, leveranciers en Dimpact'
- **Laag:** 1-5 (architectuur) · **Licentie:** n.v.t. (documentatie)
- **Repo:** https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public
- **Image / versie:** `n.v.t.` · gitbook (levend document); roadmap 2026 in Notion
- **Standaarden:** ZGW, Klantinteracties (beproeving), Producten (concept), Objecten, Referentielijsten (concept), VTB (CloudEvents NL Gov-voorstel), FSC, FTV/PBAC
- **Volwassenheid:** Productieklaar: Open Formulieren, GZAC, KISS; in ontwikkeling: OpenZaak-MijnOverheid-pilot, domeinregisters, Mijnservices, OMC (bouwsteen-overzicht).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: opdrachtgever, SBB-mapping, bouwstenen. Bronnen: <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/01-over-dit-document/03-opdracht-en-opdrachtgever.md>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/introductie/overzicht-bouwstenen>

### Laag 5 (en 4) interactie

#### OpenBeheer

- **Wat:** Beheerinterface voor zaaktypencatalogus, producttypen en objecttypen bovenop de standaard-API's.
- **Maker/beheerder:** Maykin, oorspronkelijk voor Rotterdam; stakeholders Dimpact, Den Haag, Rotterdam, Utrecht
- **Laag:** 4-5 (proces + interactie, medewerker) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-beheer
- **Image / versie:** `maykinmedia/open-beheer` · 0.9.1 (Docker Hub 30-07-2026); VCG pint 0.9.0; PodiumD pint 0.9.1
- **Standaarden:** Catalogi API, Objecttypen API, Producttypen
- **Volwassenheid:** 0.x, maar in PodiumD-chart; productie-aantal onbekend.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/open-beheer>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://github.com/maykinmedia/open-beheer/blob/main/STAKEHOLDERS.md>

#### Open Inwoner

- **Wat:** Server-rendered burgerportaal (Django) met mijn-omgeving, zaken, PDC, plannen, berichten en notificatiefeed.
- **Maker/beheerder:** Maykin (opengem.nl); ontstaan bij Enschede, Zwolle, Leeuwarden, Deventer, Groningen, Zaanstad
- **Laag:** 5 (interactie, burger) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-inwoner
- **Image / versie:** `maykinmedia/open-inwoner` · 2.4.5 (Docker Hub 29-09-2026); PodiumD pint 2.4.3
- **Standaarden:** ZGW, Klantinteracties (OpenKlant 2) en e-Suite-klanten, Objecten, Haal Centraal BRP, KvK, Notificaties (webhook), StUF/SOAP (sociaal domein), DigiD/eHerkenning/eIDAS via OIDC
- **Volwassenheid:** Productie: PodiumD Portaal live bij Assen, Enschede, Groningen, Oost Gelre en Zwolle (stand juli 2026, niet-openbare marktscan 3-0 geverifieerd). GEMMA Softwarecatalogus: 1 registratie.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: versie, licentie, PodiumD; productiegemeenten via niet-openbare marktscan. Bronnen: <https://hub.docker.com/r/maykinmedia/open-inwoner>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://opengem.nl/producten/open-inwoner/>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>

#### Open Formulieren

- **Wat:** Formulierenbouwer en -engine voor e-formulieren met DigiD/eHerkenning, prefill en registratie naar zaaksystemen.
- **Maker/beheerder:** Maykin; stakeholders Dimpact, Den Haag, Rotterdam, Utrecht, SED-organisatie
- **Laag:** 5 (interactie, burger) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/open-formulieren/open-forms
- **Image / versie:** `openformulieren/open-forms` · 4.0.1 (git tag, Docker Hub 14-09-2026; 3.5.x nog onderhouden, 3.5.9); PodiumD pint 3.5.8
- **Standaarden:** ZGW (registratie), Objecten API, StUF-ZDS, Haal Centraal BRP (prefill), KvK, DigiD/eHerkenning/eIDAS, betalingen (Ogone/Worldline)
- **Volwassenheid:** Productie: o.a. Haarlemmermeer via Dimpact (niet-openbare marktscan); GEMMA-catalogus: 6 gemeenten geregistreerd (structurele ondertelling).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: versie, licentie, stakeholders, PodiumD; adoptie via niet-openbare marktscan. Bronnen: <https://hub.docker.com/r/openformulieren/open-forms>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://github.com/open-formulieren/open-forms/blob/master/STAKEHOLDERS.md>

#### MijnOverheid (Berichtenbox, Lopende Zaken, MijnGegevens)

- **Wat:** Rijksbreed burgerportaal met Berichtenbox en Lopende Zaken waarop overheidsorganisaties aansluiten.
- **Maker/beheerder:** Logius (Rijk)
- **Laag:** 5 (interactie, burger) · **Licentie:** gesloten (overheidsvoorziening)
- **Repo:** https://mijn.overheid.nl
- **Image / versie:** `n.v.t.` · n.v.t.
- **Standaarden:** Logius-koppelvlakken Berichtenbox/Lopende Zaken (Digikoppeling); DigiD
- **Volwassenheid:** Grootschalig: meer dan 10 miljoen accounts, 8,5 miljoen unieke inloggers in 2022, ruim 80 miljoen berichten (Binnenlands Bestuur, 25-05-2023). VNG test een OpenZaak-MijnOverheid-pilot (Platform Dienstverlening).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: gebruikscijfers 2023; pilotvermelding via Platform Dienstverlening-gitbook. Bronnen: <https://www.binnenlandsbestuur.nl/digitaal/90-procent-van-de-10-miljoen-accounts-op-mijnoverheid-actief>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/introductie/overzicht-bouwstenen>, <https://vng-api-lab.netlify.app/mijnoverheid/>

#### ZAC (Zaakafhandelcomponent)

- **Wat:** Werkstroomgebaseerde zaakafhandelapplicatie voor medewerkers op ZGW-registers.
- **Maker/beheerder:** ICATT (Info.nl), gefinancierd door Dimpact; oorspronkelijk Atos
- **Laag:** 4-5 (proces + interactie, medewerker) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/infonl/dimpact-zaakafhandelcomponent
- **Image / versie:** `ghcr.io/infonl/zaakafhandelcomponent` · 5.9.1 (GHCR + git tag); PodiumD pint 5.4.5
- **Standaarden:** ZGW, Klantinteracties (OpenKlant), Objecten, BRP, KvK, Open Formulieren, OPA (autorisatie)
- **Volwassenheid:** 'In use by various municipalities' (README); PodiumD Zaak-migratie deadline 1-1-2027 (niet-openbare marktscan).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://github.com/infonl/dimpact-zaakafhandelcomponent>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### KISS (Klantinteractie-Servicesysteem)

- **Wat:** Werkplek voor KCC-medewerkers om klantvragen te registreren en beantwoorden, met kennisbank-zoeken.
- **Maker/beheerder:** KISS-community, trekker gemeente Oost Gelre met Deventer en Zwolle; oorspronkelijk VNG Realisatie
- **Laag:** 5 (interactie, medewerker) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/Klantinteractie-Servicesysteem/KISS-frontend
- **Image / versie:** `ghcr.io/klantinteractie-servicesysteem/kiss-frontend` · 3.2.0 (GHCR + git tag); PodiumD pint 3.1.3
- **Standaarden:** Klantinteracties (OpenKlant 2), ZGW, Objecten, Elasticsearch/kennisbank
- **Volwassenheid:** 'In gebruik bij 5 gemeenten' (VNG, 03-03-2026); eerder genoemd: Deventer, Enschede, Assen, Utrecht in voorbereiding (Binnenlands Bestuur, 04-06-2025).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://vng.nl/artikelen/kiss-ita-contactverzoek-1-overzichtelijke-oplossing-voor-efficient-klantcontact>, <https://www.binnenlandsbestuur.nl/digitaal/kcc-medewerkers-omarmen-kiss>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### ITA (Interne Taakafhandeling / Contactverzoek)

- **Wat:** Afhandeling van contactverzoeken door de organisatie heen, als vervolg op KISS.
- **Maker/beheerder:** KISS-community (Oost Gelre e.a.)
- **Laag:** 5 (interactie, medewerker) · **Licentie:** aanname: EUPL
- **Repo:** https://github.com/interne-taak-afhandeling
- **Image / versie:** `ghcr.io/interne-taak-afhandeling/internetaakafhandeling.web` · 3.3.3 (GHCR); PodiumD pint 3.3.2
- **Standaarden:** Klantinteracties (OpenKlant)
- **Volwassenheid:** Pilot: doel 3 tot 5 gemeenten eind 2026 (VNG, 03-03-2026).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: versie, status; licentie aanname. Bronnen: <https://vng.nl/artikelen/kiss-ita-contactverzoek-1-overzichtelijke-oplossing-voor-efficient-klantcontact>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### Signalen

- **Wat:** Meldingensysteem openbare ruimte (melden, routeren, afhandelen, terugkoppelen).
- **Maker/beheerder:** Ontstaan bij Amsterdam; doorontwikkeld door gemeentecommunity, ondersteund door VNG Realisatie
- **Laag:** 5 (vakapplicatie met eigen registratie) · **Licentie:** MPL-2.0
- **Repo:** https://github.com/Amsterdam/signals
- **Image / versie:** `signalen/backend, signalen/frontend` · backend 2.50.20 (24-09-2026), frontend 2.27.12 (29-09-2026) op Docker Hub
- **Standaarden:** Eigen REST-API (geen ZGW)
- **Volwassenheid:** Productie bij een groep gemeenten met 'ongeveer 3 miljoen inwoners' (vng.nl/projecten/signalen); aantal gemeenten niet vermeld.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://vng.nl/projecten/signalen>, <https://hub.docker.com/r/signalen/backend>

#### NL Portal

- **Wat:** Burgerportaal: React-frontend plus Kotlin BFF die ZGW/BRP/OpenKlant aggregeert achter één GraphQL-endpoint.
- **Maker/beheerder:** Ritense
- **Laag:** 5 (interactie, burger) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/nl-portal/nl-portal-frontend-libraries ; https://github.com/nl-portal/nl-portal-backend-libraries
- **Image / versie:** `niet gevonden op Docker Hub/GHCR (template-repo bouwt eigen image)` · frontend v3.0.3, backend 3.0.4.RELEASE (git tags)
- **Standaarden:** ZGW, Objecten (taken/berichten), Klantinteracties, Haal Centraal BRP en HR, GraphQL naar de frontend, Keycloak token-exchange
- **Volwassenheid:** Is de gekozen SBB voor 'User portal' in het G4 Platform Dienstverlening; productiegemeenten niet geverifieerd (aanname: Den Haag-ecosysteem).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: versies, licentie, G4-SBB; productie aanname. Bronnen: <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>, <https://github.com/nl-portal/nl-portal-backend-libraries>

#### Mijn Services (NLDS-community templates)

- **Wat:** Storybook met Mijn Omgeving-sjablonen (MijnZaken, MijnTaken, MijnBerichten e.d.) op NL Design System-componenten met gevalideerde patronen.
- **Maker/beheerder:** NL Design System-community / VNG Project Omnichannel
- **Laag:** 5 (interactie, burger) · **Licentie:** EUPL-1.2 (code), CC0 (docs)
- **Repo:** https://github.com/nl-design-system/mijn-services
- **Image / versie:** `n.v.t.` · geen releases; laatste commit 17-09-2026
- **Standaarden:** n.v.t. (UI); sluit aan op VNG Interactie-API's
- **Volwassenheid:** Ontwerppatronen, geen product.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://github.com/nl-design-system/mijn-services>, <https://nl-design-system.github.io/mijn-services/>

#### NL Design System

- **Wat:** Gedeelde, toegankelijke UI-componenten en design tokens met per-organisatie huisstijlthema's (Utrecht, Den Haag, Rijk).
- **Maker/beheerder:** NL Design System-community (overheidsbreed; kernteam onder BZK/Logius, aanname)
- **Laag:** 5 (interactie) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/nl-design-system
- **Image / versie:** `n.v.t. (npm-pakketten)` · per pakket (npm)
- **Standaarden:** n.v.t.; WCAG 2.2
- **Volwassenheid:** Breed gebruikt in Open Inwoner, NL Portal, Mijn Services (gecheckt via analyse); totaal aantal organisaties onbekend.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: licentie (utrecht-repo); beheer aanname. Bronnen: <https://github.com/nl-design-system/utrecht>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>

#### Mijn Amsterdam

- **Wat:** Eigen mijn-omgeving van Amsterdam die vele vakapplicaties aggregeert.
- **Maker/beheerder:** Gemeente Amsterdam
- **Laag:** 5 (interactie, burger) · **Licentie:** MPL-2.0
- **Repo:** https://github.com/Amsterdam/mijn-amsterdam-frontend
- **Image / versie:** `onbekend` · geen semver-releases
- **Standaarden:** Eigen BFF (aanname)
- **Volwassenheid:** Productie in Amsterdam (aanname, niet geverifieerd).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: repo en licentie; rest aanname. Bronnen: <https://github.com/Amsterdam/mijn-amsterdam-frontend>

#### Open Archiefbeheer

- **Wat:** Vernietigingslijsten en archiefbeheer op ZGW-zaken.
- **Maker/beheerder:** Maykin
- **Laag:** 4-5 (medewerker) · **Licentie:** EUPL-1.2 (aanname)
- **Repo:** https://github.com/maykinmedia/open-archiefbeheer
- **Image / versie:** `maykinmedia/open-archiefbeheer` · 2.1.0 (Docker Hub 28-09-2026); PodiumD pint 2.0.0
- **Standaarden:** ZGW
- **Volwassenheid:** In PodiumD-chart; aantal onbekend.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: versie, PodiumD. Bronnen: <https://hub.docker.com/r/maykinmedia/open-archiefbeheer>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

### Laag 4 proces

#### Operaton

- **Wat:** BPMN/DMN-procesengine voor procesautomatisering.
- **Maker/beheerder:** Operaton-community (fork van Camunda 7 CE)
- **Laag:** 4 (proces) · **Licentie:** Apache-2.0
- **Repo:** https://github.com/operaton/operaton
- **Image / versie:** `operaton/operaton` · 2.1.5 (git tag + Docker Hub 18-09-2026; 2.2.0-RC1 beschikbaar); VCG noemt 2.1.12 (niet teruggevonden)
- **Standaarden:** BPMN 2.0, DMN 1.3, Camunda 7 REST-API
- **Volwassenheid:** Onbekend bij gemeenten; Camunda 7 zelf was breed in gebruik (o.a. onder Valtimo/GZAC, aanname).
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: versie, licentie; VCG-versie wijkt af. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/operaton/operaton>

#### Operaton Modeler

- **Wat:** Desktop-modelleertool voor BPMN, DMN en formulieren.
- **Maker/beheerder:** Operaton-community (port van Fluxnova/Camunda Modeler)
- **Laag:** 4 (proces) · **Licentie:** MIT
- **Repo:** https://github.com/operaton/operaton-modeler
- **Image / versie:** `geen (desktopapp)` · geen git tags; VCG noemt 1.2.0; laatste commit 24-06-2026
- **Standaarden:** BPMN, DMN
- **Volwassenheid:** Onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/operaton/operaton-modeler>

#### Valtimo / GZAC

- **Wat:** Low-code BPMN-platform voor zaakafhandeling en processen op ZGW-registers.
- **Maker/beheerder:** Ritense (GZAC = Valtimo-distributie voor zaakgericht werken)
- **Laag:** 4 (proces) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/valtimo-platform/valtimo
- **Image / versie:** `ritense/gzac-backend, ritense/gzac-frontend (ook ritense/valtimo-*)` · 13.48.0 (git tag + Docker Hub 30-09-2026); parallel 12.48.0
- **Standaarden:** ZGW, Objecten, Klantinteracties, BRP, Notificaties; BPMN/DMN
- **Volwassenheid:** 'Productieklaar' volgens G4 Platform Dienstverlening (bouwsteen-overzicht); afgestemd tussen Rotterdam, Utrecht, Amsterdam, Den Haag (niet-openbare marktscan, niet adversarieel geverifieerd).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: versies, licentie, G4-status; gemeenten deels aanname. Bronnen: <https://github.com/valtimo-platform/valtimo>, <https://hub.docker.com/r/ritense/gzac-backend>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/introductie/overzicht-bouwstenen>

### Laag 3 integratie

#### OpenFSC (Inway, Outway, Manager, Directory)

- **Wat:** Referentie-implementatie van Federatieve Service Connectiviteit: contracten, mTLS en logging voor API-verkeer tussen organisaties.
- **Maker/beheerder:** RINIS (rinis-oss); standaard FSC door Logius
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2
- **Repo:** https://gitlab.com/rinis-oss/fsc/open-fsc
- **Image / versie:** `federatedserviceconnectivity/{inway,outway,manager,controller,directory-ui,...}` · v2.8.0 (git tag + Docker Hub 06-10-2026); VCG pint 2.4.0
- **Standaarden:** FSC Core 2.0 (Logius), Digikoppeling REST-profiel, OIN-certificaten (PKIoverheid)
- **Volwassenheid:** FSC is opvolger van NLX (niet-openbare marktscan: per 2025 standaard verklaard, niet adversarieel geverifieerd); productie-aantal onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: repo, licentie, versies; adoptie niet. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://gitlab.com/rinis-oss/fsc/open-fsc>, <https://hub.docker.com/r/federatedserviceconnectivity/manager>

#### OpenNotificaties

- **Wat:** Notificatierouteringscomponent: abonneren op en doorsturen van notificaties (webhooks) tussen componenten.
- **Maker/beheerder:** Maykin (Open Zaak-community)
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/open-zaak/open-notificaties
- **Image / versie:** `openzaak/open-notificaties` · 1.17.0 (Docker Hub 02-10-2026); VCG pint 1.16.1; PodiumD pint 1.16.2
- **Standaarden:** Notificaties API (ZGW)
- **Volwassenheid:** Productie: noodzakelijk naast elke Open Zaak-installatie.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/openzaak/open-notificaties>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### OpenFTV

- **Wat:** Bedoeld als implementatie van Federatieve Toegangsverlening (autorisatiebeslissingen via AuthZEN).
- **Maker/beheerder:** Onduidelijk: VCG noemt 'IAM-tool' maar linkt naar github.com/wearefrank/zaakbrug; standaard FTV door Logius
- **Laag:** 3 (integratie) · **Licentie:** onbekend
- **Repo:** onbekend (VCG-link wijst naar ZaakBrug, waarschijnlijk fout)
- **Image / versie:** `onbekend` · VCG noemt 1.26.14 (dat is een ZaakBrug-versie)
- **Standaarden:** FTV / NLGov-profiel OpenID AuthZEN 1.0.0 (Logius, definitief 25-06-2026)
- **Volwassenheid:** Standaard definitief; implementatie onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: VCG-tekst en AuthZEN-publicatie; implementatie niet gevonden. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://gitdocumentatie.logius.nl/publicatie/ftv/authzen/1.0.0/ftv-authzen-1.0.0.pdf>, <https://gitdocumentatie.logius.nl/publicatie/api/authzen/1.0.0/>

#### ESB (generiek)

- **Wat:** Enterprise Service Bus voor berichtenverkeer tussen componenten; 'afhankelijk van de behoefte vanuit gemeente'.
- **Maker/beheerder:** n.v.t. (keuze per gemeente)
- **Laag:** 3 (integratie) · **Licentie:** n.v.t.
- **Repo:** n.v.t.
- **Image / versie:** `n.v.t.` · n.v.t.
- **Standaarden:** StUF, SOAP, REST (afhankelijk van product)
- **Volwassenheid:** Bij veel gemeenten aanwezig (aanname); geen VCG-product gekozen.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: VCG-omschrijving; rest aanname. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>

#### NotifyNL OMC (Output Management Component)

- **Wat:** Zet ZGW-notificaties om in e-mail/SMS naar burgers via NotifyNL (port van GOV.UK Notify).
- **Maker/beheerder:** Worth Systems
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/Worth-NL/NotifyNL-OMC
- **Image / versie:** `worthnl/notifynl-omc` · 2.3.0 (Docker Hub 05-10-2026); PodiumD pint 1.17.19
- **Standaarden:** Notificaties API, OpenKlant, Objecten, NotifyNL-API
- **Volwassenheid:** In PodiumD-chart en G4 Platform Dienstverlening (SBB 'Omnichannel communication'); productie-aantal onbekend.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://hub.docker.com/r/worthnl/notifynl-omc>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>

#### IKO (Integraal Klant- en Objectbeeld)

- **Wat:** Aggregatieplatform (Kotlin/Spring + Apache Camel) dat via connectoren en declaratieve 'Aggregated Data Profiles' (JQ) één klant- en objectbeeld uit meerdere bronnen levert.
- **Maker/beheerder:** Ritense (GitHub-org Integraal-Klant-en-Objectbeeld)
- **Laag:** 3 (integratie), door G4 ingedeeld in laag 5 · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/Integraal-Klant-en-Objectbeeld/iko
- **Image / versie:** `ghcr.io/integraal-klant-en-objectbeeld/iko (oud: ritense/iko op Docker Hub, laatst 0.3.0 in 2025)` · 1.5.1 (GHCR + git tag); laatste commit 24-09-2026; Helm-chart in aparte repo
- **Standaarden:** Consumeert OpenZaak, OpenKlant, Objecten, Open Documenten, Haal Centraal BRP (ook WS-gateway), BAG; levert eigen JWT-beveiligde ADP-REST-API (geen VNG-standaard)
- **Volwassenheid:** Gekozen SBB 'Integrated customer/object views' in G4 Platform Dienstverlening; productiegemeenten niet gevonden.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: broncode, licentie, versies, G4-SBB; adoptie onbekend. Bronnen: <https://github.com/Integraal-Klant-en-Objectbeeld/iko>, <https://github.com/Integraal-Klant-en-Objectbeeld/helm-chart>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>

#### 'API framework' (G4 + Dimpact, op IKO-engine)

- **Wat:** Aangekondigd gezamenlijk API-raamwerk voor portalen/kanalen, gebouwd op de IKO-engine (volgens Joep).
- **Maker/beheerder:** Onbekend; vermoedelijk Platform Dienstverlening-kerngroep met Ritense
- **Laag:** 3 (integratie) · **Licentie:** onbekend
- **Repo:** niet gevonden
- **Image / versie:** `niet gevonden` · niet gevonden
- **Standaarden:** onbekend (aanname: IKO-ADP-API's als façade voor ZGW/Klantinteracties/VTB)
- **Volwassenheid:** Niet publiek verifieerbaar. Wel gecheckt: G4 Platform Dienstverlening kiest IKO als bouwsteen in laag 5.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** aanname (geen publieke bron voor de naam 'API framework'). Bronnen: <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>

#### ZaakBrug

- **Wat:** Vertaalt legacy StUF-ZDS-berichten naar ZGW-API's.
- **Maker/beheerder:** WeAreFrank (opvolger Open-ZaakBrug van Súdwest-Fryslân)
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/wearefrank/zaakbrug
- **Image / versie:** `wearefrank/zaakbrug` · 1.26.19 (Docker Hub 25-09-2026); PodiumD pint 1.26.19
- **Standaarden:** StUF-ZDS 1.1, ZGW
- **Volwassenheid:** In PodiumD-chart; aantal onbekend.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://hub.docker.com/r/wearefrank/zaakbrug>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### Frank!Gateway (APISIX) in PodiumD

- **Wat:** API-gateway met oauth2-proxy-dashboard in de PodiumD-chart.
- **Maker/beheerder:** WeAreFrank (gehardende Apache APISIX-distributie)
- **Laag:** 3 (integratie) · **Licentie:** Apache-2.0 (APISIX; aanname voor de distributie)
- **Repo:** ghcr.io/wearefrank/frank-gateway
- **Image / versie:** `ghcr.io/wearefrank/frank-gateway` · 1.1.0 (PodiumD values.yaml)
- **Standaarden:** HTTP/OAuth2
- **Volwassenheid:** In PodiumD-chart.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: chart; licentie aanname. Bronnen: <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### PABC (Platform Autorisatie Beheer Component)

- **Wat:** Centraal beheer van autorisaties binnen PodiumD.
- **Maker/beheerder:** onbekend (GitHub-org platform-autorisatie-beheer-component)
- **Laag:** 3 (integratie) · **Licentie:** onbekend
- **Repo:** https://github.com/platform-autorisatie-beheer-component
- **Image / versie:** `ghcr.io/platform-autorisatie-beheer-component/pabc-api` · 1.1.1 (PodiumD values.yaml)
- **Standaarden:** onbekend
- **Volwassenheid:** In PodiumD-chart.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: chart; rest onbekend. Bronnen: <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### Keycloak (identity broker)

- **Wat:** OIDC-provider/broker voor DigiD, eHerkenning en medewerkerslogin; token-exchange.
- **Maker/beheerder:** Red Hat / CNCF-community
- **Laag:** 3 (integratie, dwarsdoorsnijdend) · **Licentie:** Apache-2.0
- **Repo:** https://github.com/keycloak/keycloak
- **Image / versie:** `quay.io/keycloak/keycloak` · 26.7.3 (PodiumD values.yaml)
- **Standaarden:** OIDC, OAuth2 token-exchange, SAML (DigiD)
- **Volwassenheid:** Standaard in PodiumD, IKO, NL Portal en G4 Platform Dienstverlening.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: PodiumD, G4-SBB. Bronnen: <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>

#### NLX

- **Wat:** Voorloper van FSC voor federatief API-verkeer tussen organisaties.
- **Maker/beheerder:** VNG Realisatie / Common Ground
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2
- **Repo:** https://gitlab.com/commonground/nlx/nlx
- **Image / versie:** `nlxio/* (aanname)` · v0.150.1 (git tag)
- **Standaarden:** NLX (pre-FSC)
- **Volwassenheid:** Uitfaserend, vervangen door FSC (niet-openbare marktscan, niet adversarieel geverifieerd).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: versie; status via niet-openbare marktscan. Bronnen: <https://gitlab.com/commonground/nlx/nlx>

#### Common Gateway / Open Catalogi (Conduction)

- **Wat:** Integratie- en catalogusplatform (tegenwoordig grotendeels als Nextcloud-apps naast OpenRegister).
- **Maker/beheerder:** Conduction
- **Laag:** 3 (integratie) · **Licentie:** EUPL-1.2 (aanname)
- **Repo:** https://github.com/ConductionNL/commonground-gateway ; https://github.com/ConductionNL/opencatalogi
- **Image / versie:** `onbekend` · opencatalogi v2.1.0 (git tag); gateway geen tags
- **Standaarden:** ZGW, eigen
- **Volwassenheid:** Onbekend.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: repo's; rest aanname. Bronnen: <https://github.com/ConductionNL/opencatalogi>

### Laag 1-2 data en services

#### OpenZaak

- **Wat:** Registratiecomponent die de ZGW-API's (Zaken, Catalogi, Documenten, Besluiten, Autorisaties) aanbiedt.
- **Maker/beheerder:** Maykin (ontwikkeling); community/stakeholders gemeenten
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/open-zaak/open-zaak
- **Image / versie:** `openzaak/open-zaak` · 1.30.0 (Docker Hub 20-08-2026); VCG pint 1.29.0; PodiumD pint 1.29.3
- **Standaarden:** ZGW API's (Zaken, Catalogi, Documenten, Besluiten, Autorisaties), Notificaties (client)
- **Volwassenheid:** Productie. 'Gerealiseerd door o.a. Amsterdam, Arnhem, Delft, Haarlem, 's-Hertogenbosch, Rotterdam, Tilburg en Utrecht' (opengem.nl); Dimpact draait het centraal voor leden (niet-openbare marktscan). Geen totaalaantal gevonden.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt: versie (git tags + Docker Hub), licentie, VCG, PodiumD-chart; gebruikers alleen via vendorpagina. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/openzaak/open-zaak>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://opengem.nl/producten/open-zaak/>

#### OpenKlant

- **Wat:** Register voor klanten (partijen), digitale adressen en klantcontacten volgens het Klantinteracties-model.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-klant
- **Image / versie:** `maykinmedia/open-klant` · 2.19.1 (Docker Hub 06-10-2026); VCG pint 2.17.0; PodiumD pint 2.15.0
- **Standaarden:** Klantinteracties API, Contactgegevens API
- **Volwassenheid:** Productie bij Den Haag ('ingezet bij gemeente Den Haag', opengem.nl); ontwikkeld met Den Haag, Utrecht, Rotterdam, Amsterdam en Dimpact; onderdeel PodiumD (KISS draait erop).
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt: versie, licentie, VCG, PodiumD; productie alleen Den Haag bevestigd via vendorpagina. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/open-klant>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://opengem.nl/producten/open-klant/>

#### Objecten (Objects API / Open Object)

- **Wat:** Generiek register waarin objecten van een configureerbaar objecttype (JSON-schema) worden opgeslagen.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-object (voorheen objects-api)
- **Image / versie:** `maykinmedia/open-object (nieuw); maykinmedia/objects-api (oud)` · 4.3.0 (Docker Hub open-object 05-10-2026); VCG pint 4.1.0; PodiumD draait nog objects-api 3.6.2
- **Standaarden:** Objecten API
- **Volwassenheid:** Productie binnen PodiumD-gemeenten (onderdeel chart); NL Portal en Open Inwoner gebruiken het voor taken/berichten/producten. Aantal onbekend.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt: versies, imagehernoeming, PodiumD-pin. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/open-object>, <https://hub.docker.com/r/maykinmedia/objects-api>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>

#### Objecttypen

- **Wat:** Register van objecttypen (JSON-schema's) die bepalen hoe objecten in de Objecten API eruitzien.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/objecttypes-api
- **Image / versie:** `maykinmedia/objecttypes-api` · 3.4.2 (Docker Hub 10-04-2026); VCG en PodiumD pinnen 3.4.2
- **Standaarden:** Objecttypen API
- **Volwassenheid:** Productie als onderdeel PodiumD; aantal onbekend.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/objecttypes-api>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### OpenProduct

- **Wat:** Register voor producttypen (PDC) en aan burgers geleverde producten, zoals een parkeervergunning.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-product
- **Image / versie:** `maykinmedia/open-product` · 1.9.0 (Docker Hub 31-08-2026); VCG pint 1.8.0
- **Standaarden:** Producten API, Producttypen API (beide concept-standaard volgens Platform Dienstverlening)
- **Volwassenheid:** Onbekend; in G4 Platform Dienstverlening als SBB 'Product data APIs'. Niet in PodiumD-chart.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: versie, licentie; productiegebruik niet gevonden. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/open-product>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>

#### OpenPDC

- **Wat:** WordPress-plugin voor een producten- en dienstencatalogus (PDC) met eigen REST-API.
- **Maker/beheerder:** OpenWebconcept (WordPress-community); bouwer aanname: Yard
- **Laag:** 1-2 (data + services) · **Licentie:** aanname: EUPL (niet gecontroleerd)
- **Repo:** https://github.com/OpenWebconcept/plugin-pdc-base
- **Image / versie:** `geen (WordPress-plugin)` · v3.18.1 (git tag); VCG pint 3.18.1
- **Standaarden:** Eigen WordPress REST-API (geen VNG-standaard)
- **Volwassenheid:** Onbekend (gebruikt binnen OpenWebconcept-gemeenten, aantal niet gevonden).
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: versie, VCG; licentie en maker aanname. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/OpenWebconcept/plugin-pdc-base>

#### OpenOrganisatie

- **Wat:** Register voor medewerkers en teams, gesynchroniseerd via SCIM uit Entra ID e.d.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-organisatie
- **Image / versie:** `maykinmedia/open-organisatie` · 0.2.0 (Docker Hub 23-01-2026); VCG pint 0.2.0
- **Standaarden:** Eigen REST-API, SCIM
- **Volwassenheid:** Vroeg (0.x); productie onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/open-organisatie>

#### OpenPlan

- **Wat:** Register voor plannen van inwoners (sociaal domein) met doelen, producten en taken.
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-plan
- **Image / versie:** `maykinmedia/openplan (genoemd in docker-compose; niet gevonden op Docker Hub)` · 0.1.0 (README; geen git tags); VCG pint 0.1.0
- **Standaarden:** Eigen Plannen API (ook opgenomen in VNG Interactie-API's als openplan-plannen)
- **Volwassenheid:** Zeer vroeg; productie onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: README-versie; Docker-image niet gevonden. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/maykinmedia/open-plan>

#### VNG-Selectielijst

- **Wat:** API die de VNG Selectielijst (archiveringstermijnen) ontsluit voor zaaktypen.
- **Maker/beheerder:** Open Zaak-community (Maykin)
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2 (aanname)
- **Repo:** https://github.com/open-zaak/vng-selectielijst
- **Image / versie:** `openzaak/vng-selectielijst` · 1.0.5 (Docker Hub 17-08-2020); VCG pint 1.0.5
- **Standaarden:** Selectielijst API
- **Volwassenheid:** Stabiel en al jaren ongewijzigd; gebruikt door Open Zaak.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: versie; licentie aanname. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/openzaak/vng-selectielijst>

#### Referentielijsten

- **Wat:** Register voor gedeelde waardelijsten (codes, kanalen e.d.).
- **Maker/beheerder:** Maykin
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/referentielijsten
- **Image / versie:** `maykinmedia/referentielijsten-api` · 0.7.5 (Docker Hub 05-10-2026); VCG pint 0.7.3; PodiumD pint 0.7.4
- **Standaarden:** Referentielijsten API (concept)
- **Volwassenheid:** In PodiumD-chart; productie-aantal onbekend.
- **VCG-basisset:** ja · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://hub.docker.com/r/maykinmedia/referentielijsten-api>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### GPP-publicatiebank

- **Wat:** Registratie van Woo-publicaties en documenten, onderdeel van het Generieke Publicatieplatform.
- **Maker/beheerder:** Maykin, in opdracht van ICATT en Dimpact (GPP-Woo)
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/GPP-Woo/GPP-publicatiebank
- **Image / versie:** `ghcr.io/gpp-woo/gpp-publicatiebank` · 2.1.0 (GHCR + git tag); VCG pint 2.1.0
- **Standaarden:** Eigen REST-API; koppelt met Documenten API (Open Zaak) en GPP-zoeken
- **Volwassenheid:** Onbekend aantal; aangeboden via Dimpact.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/GPP-Woo/GPP-publicatiebank>

#### OpenPub

- **Wat:** WordPress-plugin voor nieuwsberichten, Woo-verzoeken en convenanten.
- **Maker/beheerder:** OpenWebconcept (WordPress-community)
- **Laag:** 1-2 (data + services) · **Licentie:** aanname: EUPL (niet gecontroleerd)
- **Repo:** https://github.com/OpenWebconcept/plugin-openpub-base
- **Image / versie:** `geen (WordPress-plugin)` · v3.9.4 (git tag); VCG pint 3.8.7
- **Standaarden:** Eigen WordPress REST-API
- **Volwassenheid:** Onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: versie; licentie aanname. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/OpenWebconcept/plugin-openpub-base>

#### OpenRegister

- **Wat:** Nextcloud-app/framework om schema-gedreven registers met REST-API's te maken.
- **Maker/beheerder:** Conduction
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/ConductionNL/openregister (VCG verwijst naar codeberg.org/Conduction/openregister, niet bereikbaar)
- **Image / versie:** `geen eigen image (Nextcloud-app)` · v2.1.0 (GitHub tag); VCG pint 1.0.3
- **Standaarden:** Eigen REST-API, schema-gedreven
- **Volwassenheid:** Onbekend.
- **VCG-basisset:** ja · **PodiumD:** nee
- **Verificatie:** gecheckt: GitHub-versie en licentie; codeberg geblokkeerd. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://github.com/ConductionNL/openregister>

#### Open VTB (Verzoeken, Taken, Berichten)

- **Wat:** Register en API's voor verzoeken (aanvragen los van zaken), taken voor de burger en berichten tussen burger en gemeente.
- **Maker/beheerder:** Maykin, voor de werkgroep Platform Dienstverlening
- **Laag:** 1-2 (data + services) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/maykinmedia/open-vtb
- **Image / versie:** `maykinmedia/open-vtb` · 0.2.0 (Docker Hub 06-10-2026)
- **Standaarden:** Verzoeken, Taken, Berichten API (concept); voorstel CloudEvents NL Gov-profiel
- **Volwassenheid:** Zeer vroeg (0.x); bedoeld om het Objecten-API-patroon voor taken/berichten te vervangen.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://github.com/maykinmedia/open-vtb>, <https://hub.docker.com/r/maykinmedia/open-vtb>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/08-applicatiearchitectuur/08-solution-building-blocks-sbb-s-en-mapping-op-abb-s>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/onderzoeken/vtb-component-concept.md>

### Standaarden en API-contracten

#### ZGW API's (Zaakgericht Werken)

- **Wat:** API-standaard voor zaken, catalogi, documenten, besluiten, autorisaties en notificaties.
- **Maker/beheerder:** VNG Realisatie
- **Laag:** 2 (services, standaard) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/VNG-Realisatie/gemma-zaken
- **Image / versie:** `n.v.t.` · ZGW 1.7 vastgesteld 09-06-2026 (Zaken 1.7.0, Catalogi 1.3.3, Documenten 1.7.0, Besluiten 1.1.0, Autorisaties 1.1.0, Notificaties 1.0.1); september-2026-release in consultatie (Zaken 1.8.0)
- **Standaarden:** OpenAPI 3, verplichte /openapi.json; applicatie-autorisatie (geen per-burger)
- **Volwassenheid:** Breed geïmplementeerd; Roxit claimt ZGW 'in productie bij 150+ organisaties' (niet-openbare marktscan).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://vng-realisatie.github.io/gemma-zaken/standaard/>, <https://github.com/VNG-Realisatie/Interactie-APIs/blob/main/architecture/analyze-portalen.md>

#### Klantinteracties API

- **Wat:** Model en API voor partijen, betrokkenen, klantcontacten, interne taken en digitale adressen.
- **Maker/beheerder:** VNG Realisatie (model); OpenKlant 2 is de implementatie
- **Laag:** 2 (services, standaard) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/VNG-Realisatie/klantinteracties
- **Image / versie:** `n.v.t.` · Niet vastgesteld: VNG-site noemt het een 'halfproduct', doorontwikkeling gepauzeerd (stand juli 2024); Platform Dienstverlening labelt het 'BEPROEVING'
- **Standaarden:** OpenAPI 3
- **Volwassenheid:** De-facto standaard via OpenKlant 2 + KISS, formeel niet vastgesteld.
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://vng-realisatie.github.io/klantinteracties/>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/standaarden/klantinteracties-beproeving.md>

#### Notificaties API

- **Wat:** Publish/subscribe-standaard voor events tussen componenten (kanalen, abonnementen, webhooks).
- **Maker/beheerder:** VNG Realisatie
- **Laag:** 3 (integratie, standaard) · **Licentie:** EUPL-1.2
- **Repo:** https://github.com/VNG-Realisatie/notificaties-api
- **Image / versie:** `n.v.t.` · 1.0.1 vastgesteld; 1.1.0 in consultatie (sept 2026)
- **Standaarden:** REST-webhooks; CloudEvents NL Gov in discussie
- **Volwassenheid:** Breed (elke Open Zaak-installatie).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt. Bronnen: <https://vng-realisatie.github.io/gemma-zaken/standaard/>

#### Haal Centraal BRP API Personen

- **Wat:** Bevragen van persoonsgegevens uit de BRP via REST.
- **Maker/beheerder:** RvIG (Rijksdienst voor Identiteitsgegevens)
- **Laag:** 2 (services, basisregistratie) · **Licentie:** EUPL (aanname)
- **Repo:** https://github.com/BRP-API/Haal-Centraal-BRP-bevragen
- **Image / versie:** `ghcr.io/brp-api/personen-mock (mock)` · Live; mock 2.7.0 in PodiumD; vierde functie 'BRP API Gebeurtenissen' in ontwikkeling
- **Standaarden:** OpenAPI 3; aansluiten vereist BRP-autorisatiebesluit, Diginetwerk en API-gateway
- **Volwassenheid:** Productie (landelijk).
- **VCG-basisset:** nee · **PodiumD:** ja
- **Verificatie:** gecheckt: status en aansluitvoorwaarden (developer.rvig.nl); versie niet. Bronnen: <https://developer.rvig.nl/brp-api/overview/>, <https://github.com/Dimpact-Samenwerking/helm-charts/blob/main/charts/podiumd/Chart.yaml>

#### Haal Centraal BAG (BAG API Individuele Bevragingen)

- **Wat:** Bevragen van adressen en gebouwen uit de BAG.
- **Maker/beheerder:** Kadaster
- **Laag:** 2 (services, basisregistratie) · **Licentie:** onbekend
- **Repo:** https://github.com/lvbag/BAG-API
- **Image / versie:** `n.v.t.` · onbekend (geen git tags; aanname v2)
- **Standaarden:** OpenAPI 3
- **Volwassenheid:** Productie (landelijk, aanname).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** aanname: versie en status. Bronnen: <https://github.com/lvbag/BAG-API>

#### VNG Interactie-API's / VNG API Lab (MijnServices)

- **Wat:** Pre-alfa API-specificaties, JSON-schema's en patronen voor burgergerichte 'Mijn'-API's, plus klikbare MijnOverheid-demo op mocks.
- **Maker/beheerder:** VNG Realisatie, Project Omnichannel / MijnServices (opgesteld door Joep Meindertsma)
- **Laag:** 2 (services, standaard in wording) · **Licentie:** EUPL-1.2 (aanname, VNG-default)
- **Repo:** https://github.com/VNG-Realisatie/Interactie-APIs (ook VNG-Realisatie/VNG-API-Lab)
- **Image / versie:** `n.v.t. (mocks via Prism)` · pre-alfa; specs o.a. zaken, taken, producten, agenda 0.2.0, gesprekken 0.2.1, discovery, openvtb-*, openklant-klantinteracties 0.7.0, openplan, openproduct
- **Standaarden:** OpenAPI 3.1, AsyncAPI, JSON Schema, OIDC-NLGOV, federated-auth-patroon
- **Volwassenheid:** Pre-alfa, geen officiële standaard.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt (repo gekloond). Bronnen: <https://github.com/VNG-Realisatie/Interactie-APIs>, <https://vng-api-lab.netlify.app>

### Infrastructuur en identiteit

#### Haven

- **Wat:** Standaard voor platformonafhankelijke cloudhosting (Kubernetes-eisen) plus compliancy-checker.
- **Maker/beheerder:** VNG / Common Ground
- **Laag:** infra (onder laag 1) · **Licentie:** EUPL-1.2 (aanname)
- **Repo:** https://gitlab.com/commonground/haven/haven
- **Image / versie:** `n.v.t. (CLI/checker)` · v12.13.0 (git tag)
- **Standaarden:** Kubernetes
- **Volwassenheid:** VNG-standaard sinds 12-04-2022; 'een groot aantal gemeenten' werkt ermee (Binnenlands Bestuur), geen aantal.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt. Bronnen: <https://gitlab.com/commonground/haven/haven>, <https://www.binnenlandsbestuur.nl/digitaal/vng-verklaart-haven-tot-standaard-cloudhosting>

#### Haven+

- **Wat:** Voorgeconfigureerde platformlaag bovenop Haven met monitoring, logging, identity, databases en secrets.
- **Maker/beheerder:** onbekend (genoemd door VCG en Platform Dienstverlening)
- **Laag:** infra (onder laag 1) · **Licentie:** onbekend
- **Repo:** niet gevonden
- **Image / versie:** `n.v.t.` · onbekend
- **Standaarden:** n.v.t.
- **Volwassenheid:** Onbekend; VCG noemt het 'platformdienst voor het veilig hosten en beheren van Common Ground-voorzieningen'.
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** gecheckt: omschrijving; beheerder onbekend. Bronnen: <https://code.overheid.nl/CommonGround/vcg-basisset>, <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur/12-technische-architectuur/02-haven.md>

#### DigiD / eHerkenning / eIDAS

- **Wat:** Authenticatie van burgers en bedrijven.
- **Maker/beheerder:** Logius (DigiD), stelsel eHerkenning
- **Laag:** dwarsdoorsnijdend · **Licentie:** n.v.t.
- **Repo:** https://www.logius.nl/domeinen/toegang/digid
- **Image / versie:** `n.v.t.` · n.v.t.
- **Standaarden:** SAML, OIDC (via broker), OIDC-NLGOV
- **Volwassenheid:** Verplicht; jaarlijks ICT-beveiligingsassessment voor aansluithouder, RSO-rapport leverancier (niet-openbare marktscan 3-0).
- **VCG-basisset:** nee · **PodiumD:** nee
- **Verificatie:** overgenomen uit een niet-openbare marktscan, niet zelf nagekeken.

## 4. Open vragen

1. **"API framework" van G4 + Dimpact op de IKO-engine.** Geen publieke bron gevonden (geen repo, geen artikel, geen gitbook-pagina met die naam). Wel gecheckt: G4 Platform Dienstverlening kiest IKO als laag-5-bouwsteen en het platform is "ontwikkeld in samenwerking tussen gemeenten, leveranciers en Dimpact". Te vragen aan Ritense of de Platform Dienstverlening-kerngroep: is dit een IKO-distributie met vaste ADP-profielen, een nieuwe API-specificatie, of de VNG Interactie-API's op IKO?
2. **Productie-adoptie van IKO en NL Portal.** Niet gevonden. Welke G4-stad draait IKO/NL Portal in productie, en voor welke kanalen (KCC of burger)?
3. **OpenFTV.** De VCG noemt het een "IAM-tool" maar linkt naar ZaakBrug. Welke implementatie bedoelt VNG, en komt er een PDP die AuthZEN spreekt (NLGov-profiel 1.0.0)?
4. **Operaton-versie in VCG (2.1.12).** Niet terug te vinden; laatste release 2.1.5. Typo of interne build?
5. **Open VTB-tijdpad.** Wanneer vervangt Open VTB het Objecten-patroon in NL Portal, Open Inwoner en ZAC? Komt het in de VCG-basisset en in PodiumD?
6. **Klantinteracties-status.** VNG-site: niet vastgesteld, ontwikkeling gepauzeerd (juli 2024); Platform Dienstverlening: "beproeving". Wie is eigenaar van de doorontwikkeling?
7. **Haven+ beheerder en propositie.** Alleen omschrijving gevonden; wie levert het en kan een externe leverancier erop draaien?
8. **Werkelijke productieaantallen Common Ground-componenten.** GEMMA-registraties (1 tot 6) liggen ver onder de werkelijkheid (Dimpact centraal). Componentencatalogus niet bereikbaar in deze sessie.
9. **Laag 5 in de VCG.** Is er een route om een laag-5-component (zoals een burgerportaal) aan de basisset toe te voegen (beheerder: Hugo ter Doest, VNG Realisatie, volgens README)?
10. **MijnOverheid-pilot.** Bouwstenenoverzicht noemt "OpenZaak (pilot met MijnOverheid-integratie)". Welke gemeenten, welk koppelvlak, en hoe verhoudt dat zich tot een gemeentelijk burgerportaal?

## 5. Bronnen

**Primair (zelf geraadpleegd 7-10-2026)**
- VCG-basisset README: <https://code.overheid.nl/CommonGround/vcg-basisset> (via WebFetch; `data/components.json` geblokkeerd door robots.txt)
- PodiumD Helm-chart 4.9.3: <https://github.com/Dimpact-Samenwerking/helm-charts> (`charts/podiumd/Chart.yaml`, `values.yaml`)
- Platform Generieke Dienstverlening (G4): <https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public> (opdrachtgever, bouwstenen, SBB-mapping, VTB-concept, Haven+)
- IKO: <https://github.com/Integraal-Klant-en-Objectbeeld/iko> (README, `doc/architecture.md`, LICENSE)
- VNG Interactie-API's en analyse bestaande portalen: <https://github.com/VNG-Realisatie/Interactie-APIs> (`architecture/analyze-portalen.md`, `referentie-architectuur.md`, `generieke-api-strategie.md`)
- ZGW-standaard: <https://vng-realisatie.github.io/gemma-zaken/standaard/>
- Klantinteracties: <https://vng-realisatie.github.io/klantinteracties/>
- BRP API: <https://developer.rvig.nl/brp-api/overview/>
- FTV/AuthZEN: <https://gitdocumentatie.logius.nl/publicatie/ftv/authzen/1.0.0/ftv-authzen-1.0.0.pdf>
- OpenFSC: <https://gitlab.com/rinis-oss/fsc/open-fsc>
- Docker Hub API (`hub.docker.com/v2/repositories/<image>/tags`) en GHCR-tags-API voor alle versies
- GitHub-repo's via `git ls-remote` / `git clone --depth 1`: open-zaak, open-klant, open-object, objecttypes-api, open-product, open-organisatie, open-plan, referentielijsten, vng-selectielijst, GPP-publicatiebank, plugin-pdc-base, plugin-openpub-base, openregister, open-notificaties, zaakbrug, open-beheer, operaton, operaton-modeler, open-inwoner, open-forms, open-vtb, open-archiefbeheer, nl-portal, KISS-frontend, dimpact-zaakafhandelcomponent, valtimo, signals, mijn-services, NotifyNL-OMC

**Secundair (web)**
- opengem.nl productpagina's Open Zaak, Open Klant, Open Inwoner, Open Formulieren
- VNG: <https://vng.nl/projecten/signalen>, <https://vng.nl/artikelen/kiss-ita-contactverzoek-1-overzichtelijke-oplossing-voor-efficient-klantcontact> (3-3-2026)
- Binnenlands Bestuur: KISS (4-6-2025), Haven tot standaard (12-4-2022), MijnOverheid 10 miljoen accounts (25-5-2023)
- iBestuur, "Hoe de G4 een gezamenlijke digitale koers uitzet" (8-12-2025)
- Digitale Overheid, innovatieproject "Integraal klantbeeld" (2021, Den Haag e.a.)
