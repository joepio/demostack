# Testresultaten stack kern

MijnServices-kern (variant 1): registers en API's. Gedraaid op 2026-10-09T08:58:24+0000, commit `4a4db4427ecb`.

Zonder plug-ins.

**34 geslaagd, 7 gefaald (7 bekend, 0 onverwacht), 5 overgeslagen.**

| Categorie | Geslaagd | Gefaald | Waarvan bekend | Overgeslagen |
|---|---|---|---|---|
| gezondheid | 12 | 0 | 0 | 0 |
| rook | 19 | 0 | 0 | 3 |
| zgw | 3 | 7 | 7 | 0 |
| burger-isolatie | 0 | 0 | 0 | 1 |
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
| geslaagd | `rook/openzaak/documenten-metadata-en-inhoud` | Foto trottoirtegels (841 bytes); Melding losliggende trottoirtegels (856 bytes) |
| geslaagd | `rook/openzaak/zaakobject-verwijst-naar-open-object` | http://openobject.local:8000/api/v2/objects/99aea64b-8b33-4be6-b871-84eb544d6160 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-mag-niet-schrijven` | POST /zaken gaf 403 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-heeft-geen-toegang-tot-autorisaties` | GET /applicaties gaf 403 |
| geslaagd | `rook/openzaak/catalogus-met-gepubliceerde-zaaktypen` | Melding openbare ruimte, Omgevingsvergunning aanvragen, Parkeervergunning bewoners aanvragen, Wmo-maatwerkvoorziening aanvragen |
| geslaagd | `rook/opennotificaties/kanalen` | autorisaties, besluiten, besluittypen, documenten, informatieobjecttypen, internetaken, klantcontacten, objecten, partijen, producten, zaaktypen, zaken |
| geslaagd | `rook/opennotificaties/keten-open-zaak-open-notificaties-abonnee` | 'zaken/partial_update' afgeleverd na 4.5s |
| geslaagd | `rook/openklant/partij-en-klantcontacten-van-burger-a-token-burgerportaal` | Stephan Janssen: 1 klantcontact(en), via telefoon |
| geslaagd | `rook/openobject/melding-openbare-ruimte-token-burgerportaal` | 2 meldingen; deze: Bestrating |
| geslaagd | `rook/openproduct/producten-van-burger-b` | 1 product(en): Parkeervergunning Loosduinen (XX-999-X) (actief) |
| geslaagd | `rook/selectielijst/procestypen-2020` | 29 procestypen |
| geslaagd | `rook/referentielijsten/tabel-kanaal` | 6 kanalen: chat, webformulier, post, balie, telefoon, email |
| overgeslagen | `rook/postgres` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/redis` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/notificatie-sink` | infrastructuur: alleen gezondheid |

## zgw

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `zgw/gedrag/overzicht-naar-detail` | 4 stap(pen), 2 waarschuwing(en), o.a. MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/61 |
| geslaagd | `zgw/gedrag/zonder-token` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. |
| geslaagd | `zgw/gedrag/onbekende-zaak` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. |
| gefaald (bekend) | `zgw/gedrag/burger-a-haalt-zaak-van-burger-b` | stap a-haalt-zaak-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $statusCode == 404"} Bekend: ZGW 1.x autoriseert per applicatie, niet per burger: het applicatietoken mag elke zaak van de geautoriseerde zaaktypen lezen (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/gedrag/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: In ZGW is het BSN een queryfilter dat de client kiest; Open Zaak controleert niet wie de burger is (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/strikt/overzicht-naar-detail` | stap zoek-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/614c910d-0128-4355-8b1b-0946cc2275fb", > 71 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 72 \| " Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/zonder-token` | stap zoek-zonder-token: content-type check: Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/onbekende-zaak` | stap haal-onbekende-zaak: content-type check: Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-haalt-zaak-van-burger-b` | stap b-zoekt-eigen-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 60 \| "archiefactiedatum": null, 61 \| "resultaat": null, > 62 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 63 \| "processobjectaard": "", 64 \| "startdatumBewaartermijn": null, 65 \| "processobject": { MINLENG Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |

## burger-isolatie

| Status | Check | Toelichting |
|---|---|---|
| overgeslagen | `burger-isolatie/kanalen` | geen burgerkanalen (portalen of burger-API's) in stack.yaml of in een plug-in |

## mijn-apis

| Status | Check | Toelichting |
|---|---|---|
| overgeslagen | `mijn-apis/geen` | geen plug-in met een Mijn-API in deze stack: start met `scripts/stack.sh up <stack> --plugin <map>` (docs/PLUGINS.md) |

## Images

| Service | Image | Status |
|---|---|---|
| brp-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | Up 6 minutes |
| keycloak | `keycloak/keycloak:26.4.7` | Up 5 minutes (healthy) |
| notificatie-sink | `openzaak/open-zaak:1.29.0` | Up 6 minutes (healthy) |
| openklant | `maykinmedia/open-klant:2.17.0` | Up 2 minutes (healthy) |
| openklant-celery | `maykinmedia/open-klant:2.17.0` | Up 2 minutes |
| openklant-init | `maykinmedia/open-klant:2.17.0` | Exited (0) 2 minutes ago |
| opennotificaties | `openzaak/open-notificaties:1.16.1` | Up 2 minutes (healthy) |
| opennotificaties-celery | `openzaak/open-notificaties:1.16.1` | Up 2 minutes |
| opennotificaties-celery-beat | `openzaak/open-notificaties:1.16.1` | Up 2 minutes |
| opennotificaties-init | `openzaak/open-notificaties:1.16.1` | Exited (0) 2 minutes ago |
| openobject | `maykinmedia/open-object:4.1.0` | Up 2 minutes (healthy) |
| openobject-celery | `maykinmedia/open-object:4.1.0` | Up 2 minutes |
| openobject-init | `maykinmedia/open-object:4.1.0` | Exited (0) 2 minutes ago |
| openproduct | `maykinmedia/open-product:1.8.0` | Up 2 minutes (healthy) |
| openproduct-celery | `maykinmedia/open-product:1.8.0` | Up About a minute |
| openproduct-init | `maykinmedia/open-product:1.8.0` | Exited (0) 2 minutes ago |
| openzaak | `openzaak/open-zaak:1.29.0` | Up About a minute (healthy) |
| openzaak-celery | `openzaak/open-zaak:1.29.0` | Up 53 seconds |
| openzaak-init | `openzaak/open-zaak:1.29.0` | Exited (0) About a minute ago |
| postgres | `postgis/postgis:17-3.5-alpine` | Up 6 minutes (healthy) |
| redis | `redis:8.10.2-alpine` | Up 6 minutes (healthy) |
| referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | Up 5 minutes (healthy) |
| selectielijst | `openzaak/vng-selectielijst:1.0.5` | Up 5 minutes (healthy) |
