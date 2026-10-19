# Testresultaten stack vcg

VCG-basisset. Gedraaid op 2026-10-08T15:45:47+0000, commit `ec6514bbfbbf`.

> Afgeleid van de run van 2026-10-08 (commit ec6514bbfbbf): die draaide met een ingebouwde portaallaag. De checks van die laag zijn weggelaten, de leesclient heet nu burgerportaal, en de categorie mijn-apis is overgeslagen zonder plug-in. Opnieuw draaien met scripts/stack.sh test vcg geeft een rapport uit een echte run.

Zonder plug-ins.

**69 geslaagd, 7 gefaald (7 bekend, 0 onverwacht), 6 overgeslagen.**

| Categorie | Geslaagd | Gefaald | Waarvan bekend | Overgeslagen |
|---|---|---|---|---|
| gezondheid | 22 | 0 | 0 | 2 |
| rook | 38 | 0 | 0 | 3 |
| zgw | 3 | 7 | 7 | 0 |
| burger-isolatie | 6 | 0 | 0 | 0 |
| mijn-apis | 0 | 0 | 0 | 1 |

## gezondheid

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `gezondheid/postgres` | postgres healthy [postgis/postgis:17-3.5-alpine] |
| geslaagd | `gezondheid/redis` | redis healthy [redis:8.10.2-alpine] |
| geslaagd | `gezondheid/keycloak` | keycloak healthy; HTTP 200 [keycloak/keycloak:26.4.7] |
| geslaagd | `gezondheid/brp-mock` | brp-mock running; HTTP 405 [iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6] |
| geslaagd | `gezondheid/notificatie-sink` | notificatie-sink healthy; HTTP 200 [openzaak/open-zaak:1.29.0] |
| geslaagd | `gezondheid/openzaak` | openzaak healthy; openzaak-celery running; HTTP 302 [openzaak/open-zaak:1.29.0] |
| geslaagd | `gezondheid/opennotificaties` | opennotificaties healthy; opennotificaties-celery running; opennotificaties-celery-beat running; HTTP 302 [openzaak/open-notificaties:1.16.1] |
| geslaagd | `gezondheid/openobject` | openobject healthy; openobject-celery running; HTTP 302 [maykinmedia/open-object:4.1.0] |
| geslaagd | `gezondheid/openklant` | openklant healthy; openklant-celery running; HTTP 302 [maykinmedia/open-klant:2.17.0] |
| geslaagd | `gezondheid/openproduct` | openproduct healthy; openproduct-celery running; HTTP 302 [maykinmedia/open-product:1.8.0] |
| geslaagd | `gezondheid/referentielijsten` | referentielijsten healthy; HTTP 302 [maykinmedia/referentielijsten-api:0.7.3] |
| geslaagd | `gezondheid/selectielijst` | selectielijst healthy; HTTP 200 [openzaak/vng-selectielijst:1.0.5] |
| geslaagd | `gezondheid/keycloak-vcg` | keycloak healthy; HTTP 200 [keycloak/keycloak:26.4.7] |
| geslaagd | `gezondheid/openorganisatie` | openorganisatie healthy; openorganisatie-celery running; HTTP 302 [maykinmedia/open-organisatie:0.2.0] |
| geslaagd | `gezondheid/publicatiebank` | publicatiebank healthy; publicatiebank-celery running; HTTP 302 [maykinmedia/woo-publications:2.1.0] |
| geslaagd | `gezondheid/openbeheer` | openbeheer healthy; openbeheer-ui healthy; HTTP 302 [maykinmedia/open-beheer:0.9.0, nginx:1.29.8-alpine] |
| geslaagd | `gezondheid/operaton` | operaton healthy; operaton-worker running; HTTP 200 [openzaak/open-zaak:1.29.0, operaton/operaton:2.1.5] |
| geslaagd | `gezondheid/openplan` | openplan healthy; HTTP 302 [demogemeente/openplan:0.1.0] |
| geslaagd | `gezondheid/openpdc` | mariadb healthy; wordpress healthy; HTTP 200 [demogemeente/wordpress-owc:6.8.3, mariadb:11.8.3] |
| geslaagd | `gezondheid/openpub` | mariadb healthy; wordpress healthy; HTTP 200 [demogemeente/wordpress-owc:6.8.3, mariadb:11.8.3] |
| geslaagd | `gezondheid/openregister` | nextcloud healthy; HTTP 200 [demogemeente/openregister:1.0.3] |
| geslaagd | `gezondheid/openfsc` | fsc-directory running; fsc-directory-controller running; fsc-vbs-manager running; fsc-vbs-controller running; fsc-vbs-outway running; fsc-vbs-txlog running; fsc-brp-manager running; fsc-brp-controller running; fsc-brp-inway running; fsc-brp-txlog running; HTTP 200 [federatedserviceconnectivity/controller:v2.4.0, federatedserviceconnectivity/inway:v2.4.0, federatedserviceconnectivity/manager:v2.4.0, federatedserviceconnectivity/outway:v2.4.0, federatedserviceconnectivity/txlog-api:v2.4.0] |
| overgeslagen | `gezondheid/operaton-modeler` | gepland, nog niet in de stack: niet draaibaar: een desktopapplicatie (Electron) voor het tekenen van BPMN/DMN, geen server of container. Het proces in config/operaton/resources/ is met de hand geschreven en wordt bij de start in Operaton gezet. |
| overgeslagen | `gezondheid/openftv` | gepland, nog niet in de stack: niet draaibaar: geen implementatie gevonden. De link in de basisset wijst naar ZaakBrug en 1.26.14 is een versienummer van ZaakBrug; FTV (Federatieve Toegangsverlening) is een standaard (AuthZEN), geen product. Nodig: een bron of image van de bedoelde component. |

## rook

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `rook/brp-mock/testpersoon-raadplegen` | Stephan Janssen |
| geslaagd | `rook/keycloak/digid-simulatie-inloggen-als-inwoner-claim-bsn` | bsn=999990627, loa=urn:etoegang:core:assurance-class:loa2plus |
| geslaagd | `rook/keycloak/client-credentials-voor-burgerportaal` | token ontvangen |
| geslaagd | `rook/openzaak/zaken-van-burger-a-opvragen-applicatie-burgerportaal` | 2 zaken: VBS-2026-000101, VBS-2026-000102 |
| geslaagd | `rook/openzaak/zaak-ophalen-met-zaaktype-en-resultaat` | VBS-2026-000102 (Melding openbare ruimte), einddatum 2026-09-09, resultaat 'Uitgevoerd' |
| geslaagd | `rook/openzaak/statussen` | Ontvangen > Ingepland > Afgehandeld |
| geslaagd | `rook/openzaak/rollen-natuurlijk-persoon-met-bsn` | Aanvrager: Janssen |
| geslaagd | `rook/openzaak/documenten-metadata-en-inhoud` | Foto burgerportaaltegels (835 bytes); Melding losliggende burgerportaaltegels (850 bytes) |
| geslaagd | `rook/openzaak/zaakobject-verwijst-naar-open-object` | http://openobject.local:8000/api/v2/objects/a7926893-0a6f-4fce-a616-cf2cc978e8d6 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-mag-niet-schrijven` | POST /zaken gaf 403 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-heeft-geen-toegang-tot-autorisaties` | GET /applicaties gaf 403 |
| geslaagd | `rook/openzaak/catalogus-met-gepubliceerde-zaaktypen` | Melding openbare ruimte, Omgevingsvergunning aanvragen, Parkeervergunning bewoners aanvragen, Wmo-maatwerkvoorziening aanvragen |
| geslaagd | `rook/opennotificaties/kanalen` | autorisaties, besluiten, besluittypen, documenten, informatieobjecttypen, internetaken, klantcontacten, medewerkers, objecten, partijen, producten, zaaktypen, zaken |
| geslaagd | `rook/opennotificaties/keten-open-zaak-open-notificaties-abonnee` | 'zaken/partial_update' afgeleverd na 0.4s |
| geslaagd | `rook/openklant/partij-en-klantcontacten-van-burger-a-token-burgerportaal` | Stephan Janssen: 1 klantcontact(en), via telefoon |
| geslaagd | `rook/openobject/melding-openbare-ruimte-token-burgerportaal` | 2 meldingen; deze: Bestrating |
| geslaagd | `rook/openproduct/producten-van-burger-b` | 1 product(en): Parkeervergunning Loosduinen (XX-999-X) (actief) |
| geslaagd | `rook/selectielijst/procestypen-2020` | 29 procestypen |
| geslaagd | `rook/referentielijsten/tabel-kanaal` | 6 kanalen: chat, webformulier, post, balie, telefoon, email |
| geslaagd | `rook/keycloak-vcg/medewerker-logt-via-oidc-in-bij-open-organisatie` | beheer.devos (Superuser) in de admin van Open Organisatie |
| geslaagd | `rook/openbeheer/behandelaar-zonder-beheerrol-komt-niet-binnen` | geweigerd bij de login (Keycloak weigert a.vermeulen (401)) |
| geslaagd | `rook/openorganisatie/afdelingen-teams-en-medewerkers-van-voorbeeldstad` | 3 afdelingen, 5 teams, 5 medewerkers; Parkeren: Lotte Smits |
| geslaagd | `rook/openorganisatie/wijziging-medewerker-open-notificaties-abonnee` | 'medewerkers/partial_update' afgeleverd na 4.1s |
| geslaagd | `rook/publicatiebank/gepubliceerde-woo-documenten-staan-in-open-zaak` | 2 publicaties, 2 documenten in Open Zaak, download 1782 bytes PDF |
| geslaagd | `rook/publicatiebank/leestoken-kan-niet-schrijven` | 403 |
| geslaagd | `rook/openbeheer/zaaktypen-uit-open-zaak-na-oidc-login` | Mirjam de Vos ziet 4 zaaktypen |
| geslaagd | `rook/operaton/behandelaar-rondt-taak-af-worker-sluit-de-zaak-in-open-zaak` | taak was al afgerond; zaak VBS-2026-000110: resultaat Geleverd, einddatum 2026-10-08, behandelaar mdw-0404 |
| geslaagd | `rook/operaton/rest-api-weigert-zonder-inlog` | 401 |
| geslaagd | `rook/openplan/plannen-met-doel-en-instrument` | 2 plannen (VBS-2026-000104, VBS-2026-000105), 2 doelen, 2 instrumenten |
| geslaagd | `rook/openplan/zonder-token-geen-persoonsgegevens` | 401 |
| geslaagd | `rook/openpdc/producten-en-diensten-met-thema` | 3 items; 'Parkeervergunning bewoners aanvragen' onder thema Parkeren |
| geslaagd | `rook/openpub/nieuwsberichten` | Stadskantoor gesloten tijdens de feestdagen; Nieuwe parkeertarieven binnenstad per 1 januari |
| geslaagd | `rook/openregister/register-schema-en-objecten-validatie-tegen-het-schema` | 3 speelplekken; ongeldig object geweigerd (400) |
| geslaagd | `rook/openregister/zonder-inlog-geen-objecten` | 200 met een lege lijst (objecten zijn niet gepubliceerd) |
| geslaagd | `rook/openfsc/alle-fsc-componenten-gereed` | 10 componenten /health/ready 200 |
| geslaagd | `rook/openfsc/contract-voorbeeldstad-en-brp-leverancier-geldig` | dienst brp-personen gepubliceerd; verbinding getekend door beide peers |
| geslaagd | `rook/openfsc/brp-bevragen-via-outway-en-inway-met-transactielog` | Thea Kouwenhoven via FSC; transactie 01a11c27-a0e5... gelogd bij afnemer en aanbieder |
| geslaagd | `rook/openfsc/geen-toegang-zonder-grant-of-certificaat` | outway zonder grant 400 (UNKNOWN_GRANT_HASH_IN_HEADER); inway zonder clientcertificaat: TLS-handshake geweigerd |
| overgeslagen | `rook/postgres` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/redis` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/notificatie-sink` | infrastructuur: alleen gezondheid |

## zgw

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `zgw/gedrag/overzicht-naar-detail` | 4 stap(pen), 2 waarschuwing(en), o.a. MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/9b |
| geslaagd | `zgw/gedrag/zonder-token` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. |
| geslaagd | `zgw/gedrag/onbekende-zaak` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. |
| gefaald (bekend) | `zgw/gedrag/burger-a-haalt-zaak-van-burger-b` | stap a-haalt-zaak-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $statusCode == 404"} Bekend: ZGW 1.x autoriseert per applicatie, niet per burger: het applicatietoken mag elke zaak van de geautoriseerde zaaktypen lezen (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/gedrag/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: In ZGW is het BSN een queryfilter dat de client kiest; Open Zaak controleert niet wie de burger is (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/strikt/overzicht-naar-detail` | stap zoek-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/9b29f6df-1bb8-45ac-8a53-6224dd52f63c", > 71 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 72 \| " Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/zonder-token` | stap zoek-zonder-token: content-type check: Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/onbekende-zaak` | stap haal-onbekende-zaak: content-type check: Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-haalt-zaak-van-burger-b` | stap b-zoekt-eigen-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 60 \| "archiefactiedatum": null, 61 \| "resultaat": null, > 62 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 63 \| "processobjectaard": "", 64 \| "startdatumBewaartermijn": null, 65 \| "processobject": { MINLENG Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |

## burger-isolatie

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `burger-isolatie/openpdc/items` | 200, 2112 bytes zonder BSN of naam van een testburger |
| geslaagd | `burger-isolatie/openpdc/themas` | 200, 1007 bytes zonder BSN of naam van een testburger |
| geslaagd | `burger-isolatie/openpub/items` | 200, 1773 bytes zonder BSN of naam van een testburger |
| geslaagd | `burger-isolatie/publicatiebank/publicaties` | 200, 2431 bytes zonder BSN of naam van een testburger |
| geslaagd | `burger-isolatie/publicatiebank/documenten` | 200, 1501 bytes zonder BSN of naam van een testburger |
| geslaagd | `burger-isolatie/openregister/speelplek` | 200, 312 bytes zonder BSN of naam van een testburger |

## mijn-apis

| Status | Check | Toelichting |
|---|---|---|
| overgeslagen | `mijn-apis/geen` | geen plug-in met een Mijn-API in deze stack: start met `scripts/stack.sh up <stack> --plugin <map>` (docs/PLUGINS.md) |

## Images

| Service | Image | Status |
|---|---|---|
| brp-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | Up 16 minutes |
| fsc-brp-controller | `federatedserviceconnectivity/controller:v2.4.0` | Up 15 minutes |
| fsc-brp-controller-init | `federatedserviceconnectivity/controller:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-brp-inway | `federatedserviceconnectivity/inway:v2.4.0` | Up 15 minutes |
| fsc-brp-manager | `federatedserviceconnectivity/manager:v2.4.0` | Up 15 minutes |
| fsc-brp-manager-init | `federatedserviceconnectivity/manager:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-brp-txlog | `federatedserviceconnectivity/txlog-api:v2.4.0` | Up 15 minutes |
| fsc-brp-txlog-init | `federatedserviceconnectivity/txlog-api:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-directory | `federatedserviceconnectivity/manager:v2.4.0` | Up 15 minutes |
| fsc-directory-controller | `federatedserviceconnectivity/controller:v2.4.0` | Up 15 minutes |
| fsc-directory-controller-init | `federatedserviceconnectivity/controller:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-directory-init | `federatedserviceconnectivity/manager:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-vbs-controller | `federatedserviceconnectivity/controller:v2.4.0` | Up 15 minutes |
| fsc-vbs-controller-init | `federatedserviceconnectivity/controller:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-vbs-manager | `federatedserviceconnectivity/manager:v2.4.0` | Up 15 minutes |
| fsc-vbs-manager-init | `federatedserviceconnectivity/manager:v2.4.0` | Exited (0) 15 minutes ago |
| fsc-vbs-outway | `federatedserviceconnectivity/outway:v2.4.0` | Up 15 minutes |
| fsc-vbs-txlog | `federatedserviceconnectivity/txlog-api:v2.4.0` | Up 15 minutes |
| fsc-vbs-txlog-init | `federatedserviceconnectivity/txlog-api:v2.4.0` | Exited (0) 15 minutes ago |
| keycloak | `keycloak/keycloak:26.4.7` | Up 15 minutes (healthy) |
| keycloak-vcg-init | `keycloak/keycloak:26.4.7` | Exited (0) 2 minutes ago |
| mariadb | `mariadb:11.8.3` | Up 16 minutes (healthy) |
| nextcloud | `demogemeente/openregister:1.0.3` | Up 15 minutes (healthy) |
| notificatie-sink | `openzaak/open-zaak:1.29.0` | Up 16 minutes (healthy) |
| openbeheer | `maykinmedia/open-beheer:0.9.0` | Up 2 minutes (healthy) |
| openbeheer-init | `maykinmedia/open-beheer:0.9.0` | Exited (0) 2 minutes ago |
| openbeheer-ui | `nginx:1.29.8-alpine` | Up 2 minutes (healthy) |
| openklant | `maykinmedia/open-klant:2.17.0` | Up 14 minutes (healthy) |
| openklant-celery | `maykinmedia/open-klant:2.17.0` | Up 14 minutes |
| openklant-init | `maykinmedia/open-klant:2.17.0` | Exited (0) 14 minutes ago |
| opennotificaties | `openzaak/open-notificaties:1.16.1` | Up 14 minutes (healthy) |
| opennotificaties-celery | `openzaak/open-notificaties:1.16.1` | Up 14 minutes |
| opennotificaties-celery-beat | `openzaak/open-notificaties:1.16.1` | Up 14 minutes |
| opennotificaties-init | `openzaak/open-notificaties:1.16.1` | Exited (0) 14 minutes ago |
| openobject | `maykinmedia/open-object:4.1.0` | Up 14 minutes (healthy) |
| openobject-celery | `maykinmedia/open-object:4.1.0` | Up 14 minutes |
| openobject-init | `maykinmedia/open-object:4.1.0` | Exited (0) 14 minutes ago |
| openorganisatie | `maykinmedia/open-organisatie:0.2.0` | Up 12 minutes (healthy) |
| openorganisatie-celery | `maykinmedia/open-organisatie:0.2.0` | Up 12 minutes |
| openorganisatie-init | `maykinmedia/open-organisatie:0.2.0` | Exited (0) 14 minutes ago |
| openplan | `demogemeente/openplan:0.1.0` | Up 14 minutes (healthy) |
| openplan-init | `demogemeente/openplan:0.1.0` | Exited (0) 14 minutes ago |
| openproduct | `maykinmedia/open-product:1.8.0` | Up 14 minutes (healthy) |
| openproduct-celery | `maykinmedia/open-product:1.8.0` | Up 13 minutes |
| openproduct-init | `maykinmedia/open-product:1.8.0` | Exited (0) 14 minutes ago |
| openzaak | `openzaak/open-zaak:1.29.0` | Up 13 minutes (healthy) |
| openzaak-celery | `openzaak/open-zaak:1.29.0` | Up 12 minutes |
| openzaak-init | `openzaak/open-zaak:1.29.0` | Exited (0) 13 minutes ago |
| operaton | `operaton/operaton:2.1.5` | Up 15 minutes (healthy) |
| operaton-worker | `openzaak/open-zaak:1.29.0` | Up 13 minutes |
| postgres | `postgis/postgis:17-3.5-alpine` | Up 16 minutes (healthy) |
| publicatiebank | `maykinmedia/woo-publications:2.1.0` | Up 12 minutes (healthy) |
| publicatiebank-celery | `maykinmedia/woo-publications:2.1.0` | Up 12 minutes |
| publicatiebank-init | `maykinmedia/woo-publications:2.1.0` | Exited (0) 14 minutes ago |
| redis | `redis:8.10.2-alpine` | Up 16 minutes (healthy) |
| referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | Up 15 minutes (healthy) |
| selectielijst | `openzaak/vng-selectielijst:1.0.5` | Up 15 minutes (healthy) |
| wordpress | `demogemeente/wordpress-owc:6.8.3` | Up 15 minutes (healthy) |
| wordpress-init | `demogemeente/wordpress-owc:6.8.3` | Exited (0) 14 minutes ago |
