# Testresultaten stack maykin

Maykin-landschap. Gedraaid op 2026-10-08T16:04:13+0000, commit `26c61314e074`.

> Afgeleid van de run van 2026-10-08 (commit 26c61314e074): die draaide met een ingebouwde portaallaag. De checks van die laag zijn weggelaten, de leesclient heet nu burgerportaal, en de categorie mijn-apis is overgeslagen zonder plug-in. Opnieuw draaien met scripts/stack.sh test maykin geeft een rapport uit een echte run.

Zonder plug-ins.

**62 geslaagd, 7 gefaald (7 bekend, 0 onverwacht), 6 overgeslagen.**

| Categorie | Geslaagd | Gefaald | Waarvan bekend | Overgeslagen |
|---|---|---|---|---|
| gezondheid | 16 | 0 | 0 | 2 |
| rook | 30 | 0 | 0 | 3 |
| zgw | 3 | 7 | 7 | 0 |
| burger-isolatie | 13 | 0 | 0 | 0 |
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
| geslaagd | `gezondheid/brp-api` | brp-api healthy; HTTP 200 [openzaak/open-zaak:1.29.0] |
| geslaagd | `gezondheid/openvtb` | openvtb healthy; openvtb-celery running; HTTP 302 [maykinmedia/open-vtb:0.2.0] |
| geslaagd | `gezondheid/openformulieren` | openformulieren healthy; openformulieren-celery running; openformulieren-celery-beat running; HTTP 302 [openformulieren/open-forms:4.0.1] |
| geslaagd | `gezondheid/openinwoner` | openinwoner healthy; openinwoner-celery running; elasticsearch healthy; HTTP 200 [elasticsearch:9.0.3, maykinmedia/open-inwoner:2.4.5] |
| overgeslagen | `gezondheid/openarchiefbeheer` | gepland, nog niet in de stack: zit in stack dimpact (PodiumD); hoort ook bij Maykin, nog niet hier |
| overgeslagen | `gezondheid/openbeheer` | gepland, nog niet in de stack: zit in stack dimpact en vcg; hoort ook bij Maykin, nog niet hier |

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
| geslaagd | `rook/openzaak/documenten-metadata-en-inhoud` | Foto burgerportaaltegels (843 bytes); Melding losliggende burgerportaaltegels (858 bytes) |
| geslaagd | `rook/openzaak/zaakobject-verwijst-naar-open-object` | http://openobject.local:8000/api/v2/objects/1629c980-c873-4b47-aba5-45344a0aa022 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-mag-niet-schrijven` | POST /zaken gaf 403 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-heeft-geen-toegang-tot-autorisaties` | GET /applicaties gaf 403 |
| geslaagd | `rook/openzaak/catalogus-met-gepubliceerde-zaaktypen` | Melding openbare ruimte, Omgevingsvergunning aanvragen, Parkeervergunning bewoners aanvragen, Wmo-maatwerkvoorziening aanvragen |
| geslaagd | `rook/opennotificaties/kanalen` | autorisaties, besluiten, besluittypen, documenten, informatieobjecttypen, internetaken, klantcontacten, objecten, partijen, producten, zaaktypen, zaken |
| geslaagd | `rook/opennotificaties/keten-open-zaak-open-notificaties-abonnee` | 'zaken/partial_update' afgeleverd na 2.4s |
| geslaagd | `rook/openklant/partij-en-klantcontacten-van-burger-a-token-burgerportaal` | Stephan Janssen: 2 klantcontact(en), via webformulier |
| geslaagd | `rook/openobject/melding-openbare-ruimte-token-burgerportaal` | 2 meldingen; deze: Bestrating |
| geslaagd | `rook/openproduct/producten-van-burger-b` | 1 product(en): Parkeervergunning Loosduinen (XX-999-X) (actief) |
| geslaagd | `rook/selectielijst/procestypen-2020` | 29 procestypen |
| geslaagd | `rook/referentielijsten/tabel-kanaal` | 6 kanalen: chat, webformulier, post, balie, telefoon, email |
| geslaagd | `rook/openinwoner/digid-login-en-mijn-aanvragen-van-burger-a` | VBS-2026-000101, VBS-2026-000102; 2 links naar een zaak |
| geslaagd | `rook/openinwoner/zaakdetail-met-status-en-documenten` | VBS-2026-000102: statushistorie tot 'afgehandeld', 2 documenten, download is een PDF (843 bytes) |
| geslaagd | `rook/openinwoner/mijn-taken-uit-open-object-externe-taken` | taken van A op de homepage: Aanvullende tekening dakkapel aanleveren, Leges omgevingsvergunning betalen |
| geslaagd | `rook/openinwoner/mijn-profiel-met-brp-gegevens` | Stephan Janssen, Mandelaplein 2, geboren 06 april 1975 |
| geslaagd | `rook/openinwoner/mijn-vragen-uit-open-klant` | Mijn vragen (1): 'Wanneer wordt de grofvuilpas verstuurd?' |
| geslaagd | `rook/openformulieren/formulier-melding-openbare-ruimte-digid-zaak-in-open-zaak` | Melding openbare ruimte: 1 stap(pen), login DigiD |
| geslaagd | `rook/openformulieren/inwoner-logt-in-brp-prefill-verstuurt-melding-zaak-in-open-z` | Paula Prins (uit de BRP) > zaak OF-KCLDWM (Melding openbare ruimte), 1 document(en) |
| geslaagd | `rook/openvtb/taken-van-burger-a-taken-api-filter-istoegewezenaan` | 3 taken (betaaltaak, urltaak, urltaak) |
| geslaagd | `rook/openvtb/filter-matcht-een-urn-segment-alleen-het-bsn-vindt-ook-de-ta` | isToegewezenAan=999990627 geeft 3 taken (segment-match, gedocumenteerd gedrag) |
| geslaagd | `rook/openvtb/zonder-token-geen-taken-token-burgerportaal-mag-lezen` | zonder token 401; token burgerportaal ziet 4 taken (alle inwoners) |
| geslaagd | `rook/brp-api/brp-api-personen-2-in-officieel-formaat` | geboorte.datum als Datum-object, verblijfplaats.verblijfadres genest |
| overgeslagen | `rook/postgres` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/redis` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/notificatie-sink` | infrastructuur: alleen gezondheid |

## zgw

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `zgw/gedrag/overzicht-naar-detail` | 4 stap(pen), 2 waarschuwing(en), o.a. MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/a4 |
| geslaagd | `zgw/gedrag/zonder-token` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. |
| geslaagd | `zgw/gedrag/onbekende-zaak` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. |
| gefaald (bekend) | `zgw/gedrag/burger-a-haalt-zaak-van-burger-b` | stap a-haalt-zaak-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $statusCode == 404"} Bekend: ZGW 1.x autoriseert per applicatie, niet per burger: het applicatietoken mag elke zaak van de geautoriseerde zaaktypen lezen (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/gedrag/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: In ZGW is het BSN een queryfilter dat de client kiest; Open Zaak controleert niet wie de burger is (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/strikt/overzicht-naar-detail` | stap zoek-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/a4a83741-51ba-4bb8-b666-c775953b77ee", > 71 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 72 \| " Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/zonder-token` | stap zoek-zonder-token: content-type check: Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/onbekende-zaak` | stap haal-onbekende-zaak: content-type check: Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-haalt-zaak-van-burger-b` | stap b-zoekt-eigen-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 60 \| "archiefactiedatum": null, 61 \| "resultaat": null, > 62 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 63 \| "processobjectaard": "", 64 \| "startdatumBewaartermijn": null, 65 \| "processobject": { MINLENG Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
| gefaald (bekend) | `zgw/strikt/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |

## burger-isolatie

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `burger-isolatie/openinwoner/b-heeft-data` | B ziet zaken VBS-2026-000103, VBS-2026-000104, 3 document(en), een eigen taak en een eigen vraag |
| geslaagd | `burger-isolatie/openinwoner/lijst` | A ziet VBS-2026-000101, VBS-2026-000102, geen van B |
| geslaagd | `burger-isolatie/openinwoner/detail` | zaken van B via directe URL: 404, 404 |
| geslaagd | `burger-isolatie/openinwoner/document` | 404 op een document van B |
| geslaagd | `burger-isolatie/openinwoner/taken` | taak van B niet zichtbaar (Open Inwoner filtert zelf op BSN, zie README) |
| geslaagd | `burger-isolatie/openinwoner/vragen` | vraag van B niet zichtbaar |
| geslaagd | `burger-isolatie/openinwoner/profiel` | alleen eigen BRP-gegevens |
| geslaagd | `burger-isolatie/openinwoner/zonder-login` | 302 naar /accounts/login/?next=/cases/ |
| geslaagd | `burger-isolatie/openformulieren/b-heeft-data` | B heeft inzending 5f785d93..., prefill Eleonora de Crooy |
| geslaagd | `burger-isolatie/openformulieren/prefill` | A krijgt alleen eigen BRP-gegevens |
| geslaagd | `burger-isolatie/openformulieren/inzending` | 404 |
| geslaagd | `burger-isolatie/openformulieren/stap` | 403 |
| geslaagd | `burger-isolatie/openformulieren/zonder-login` | 403 |

## mijn-apis

| Status | Check | Toelichting |
|---|---|---|
| overgeslagen | `mijn-apis/geen` | geen plug-in met een Mijn-API in deze stack: start met `scripts/stack.sh up <stack> --plugin <map>` (docs/PLUGINS.md) |

## Images

| Service | Image | Status |
|---|---|---|
| brp-api | `openzaak/open-zaak:1.29.0` | Up 5 minutes (healthy) |
| brp-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | Up 5 minutes |
| elasticsearch | `elasticsearch:9.0.3` | Up 5 minutes (healthy) |
| keycloak | `keycloak/keycloak:26.4.7` | Up 5 minutes (healthy) |
| keycloak-clients | `keycloak/keycloak:26.4.7` | Exited (0) 3 minutes ago |
| notificatie-sink | `openzaak/open-zaak:1.29.0` | Up 5 minutes (healthy) |
| openformulieren | `openformulieren/open-forms:4.0.1` | Up 3 minutes (healthy) |
| openformulieren-celery | `openformulieren/open-forms:4.0.1` | Up 2 minutes |
| openformulieren-celery-beat | `openformulieren/open-forms:4.0.1` | Up 2 minutes |
| openformulieren-init | `openformulieren/open-forms:4.0.1` | Exited (0) 3 minutes ago |
| openinwoner | `maykinmedia/open-inwoner:2.4.5` | Up About a minute (healthy) |
| openinwoner-celery | `maykinmedia/open-inwoner:2.4.5` | Up 49 seconds |
| openinwoner-init | `maykinmedia/open-inwoner:2.4.5` | Exited (0) About a minute ago |
| openklant | `maykinmedia/open-klant:2.17.0` | Up 4 minutes (healthy) |
| openklant-celery | `maykinmedia/open-klant:2.17.0` | Up 4 minutes |
| openklant-init | `maykinmedia/open-klant:2.17.0` | Exited (0) 4 minutes ago |
| opennotificaties | `openzaak/open-notificaties:1.16.1` | Up 4 minutes (healthy) |
| opennotificaties-celery | `openzaak/open-notificaties:1.16.1` | Up 4 minutes |
| opennotificaties-celery-beat | `openzaak/open-notificaties:1.16.1` | Up 4 minutes |
| opennotificaties-init | `openzaak/open-notificaties:1.16.1` | Exited (0) 4 minutes ago |
| openobject | `maykinmedia/open-object:4.1.0` | Up 4 minutes (healthy) |
| openobject-celery | `maykinmedia/open-object:4.1.0` | Up 4 minutes |
| openobject-init | `maykinmedia/open-object:4.1.0` | Exited (0) 4 minutes ago |
| openproduct | `maykinmedia/open-product:1.8.0` | Up 4 minutes (healthy) |
| openproduct-celery | `maykinmedia/open-product:1.8.0` | Up 3 minutes |
| openproduct-init | `maykinmedia/open-product:1.8.0` | Exited (0) 4 minutes ago |
| openvtb | `maykinmedia/open-vtb:0.2.0` | Up 4 minutes (healthy) |
| openvtb-celery | `maykinmedia/open-vtb:0.2.0` | Up 3 minutes |
| openvtb-init | `maykinmedia/open-vtb:0.2.0` | Exited (0) 4 minutes ago |
| openzaak | `openzaak/open-zaak:1.29.0` | Up 3 minutes (healthy) |
| openzaak-celery | `openzaak/open-zaak:1.29.0` | Up 2 minutes |
| openzaak-init | `openzaak/open-zaak:1.29.0` | Exited (0) 3 minutes ago |
| postgres | `postgis/postgis:17-3.5-alpine` | Up 5 minutes (healthy) |
| redis | `redis:8.10.2-alpine` | Up 5 minutes (healthy) |
| referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | Up 5 minutes (healthy) |
| selectielijst | `openzaak/vng-selectielijst:1.0.5` | Up 5 minutes (healthy) |
