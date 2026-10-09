# Testresultaten stack dimpact

Dimpact PodiumD 4.9.3. Gedraaid op 2026-10-08T12:13:13+0000, commit `0ab0bd073347`.

> Afgeleid van de run van 2026-10-08 (commit 0ab0bd073347): die draaide met een ingebouwde portaallaag. De checks van die laag zijn weggelaten, de leesclient heet nu burgerportaal, en de categorie mijn-apis is overgeslagen zonder plug-in. Opnieuw draaien met scripts/stack.sh test dimpact geeft een rapport uit een echte run.

Zonder plug-ins.

**85 geslaagd, 8 gefaald (8 bekend, 0 onverwacht), 11 overgeslagen.**

| Categorie | Geslaagd | Gefaald | Waarvan bekend | Overgeslagen |
|---|---|---|---|---|
| gezondheid | 23 | 0 | 0 | 7 |
| rook | 46 | 1 | 1 | 3 |
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
| geslaagd | `gezondheid/openzaak` | openzaak healthy; openzaak-celery running; HTTP 302 [openzaak/open-zaak:1.29.3] |
| geslaagd | `gezondheid/opennotificaties` | opennotificaties healthy; opennotificaties-celery running; opennotificaties-celery-beat running; HTTP 302 [openzaak/open-notificaties:1.16.2] |
| geslaagd | `gezondheid/openobject` | objecten healthy; objecten-celery running; HTTP 302 [maykinmedia/objects-api:3.6.2] |
| geslaagd | `gezondheid/openklant` | openklant healthy; openklant-celery running; HTTP 302 [maykinmedia/open-klant:2.15.0] |
| geslaagd | `gezondheid/referentielijsten` | referentielijsten healthy; HTTP 302 [maykinmedia/referentielijsten-api:0.7.4] |
| geslaagd | `gezondheid/selectielijst` | selectielijst healthy; HTTP 200 [openzaak/vng-selectielijst:1.0.5] |
| geslaagd | `gezondheid/objecttypen` | objecttypen healthy; HTTP 302 [maykinmedia/objecttypes-api:3.4.2] |
| geslaagd | `gezondheid/brp-api` | brp-api healthy; HTTP 200 [openzaak/open-zaak:1.29.0] |
| geslaagd | `gezondheid/mailpit` | mailpit healthy; HTTP 200 [axllent/mailpit:v1.31.4] |
| geslaagd | `gezondheid/openformulieren` | openformulieren healthy; openformulieren-celery running; openformulieren-celery-beat running; HTTP 302 [openformulieren/open-forms:3.5.8] |
| geslaagd | `gezondheid/clamav` | clamav healthy [clamav/clamav:1.5.4] |
| geslaagd | `gezondheid/openinwoner` | openinwoner healthy; openinwoner-celery running; elasticsearch healthy; HTTP 200 [elasticsearch:9.0.3, maykinmedia/open-inwoner:2.4.3] |
| geslaagd | `gezondheid/openarchiefbeheer` | openarchiefbeheer healthy; openarchiefbeheer-celery running; openarchiefbeheer-celery-beat running; HTTP 302 [maykinmedia/open-archiefbeheer:2.0.0] |
| geslaagd | `gezondheid/openbeheer` | openbeheer healthy; HTTP 302 [maykinmedia/open-beheer:0.9.1] |
| geslaagd | `gezondheid/kiss` | kiss healthy; HTTP 200 [demogemeente/kiss:3.1.3] |
| geslaagd | `gezondheid/ita` | ita healthy; ita-poller running; HTTP 200 [demogemeente/ita-poller:3.3.2, demogemeente/ita-web:3.3.2] |
| geslaagd | `gezondheid/pabc` | pabc healthy; HTTP 200 [demogemeente/pabc-api:1.1.1] |
| geslaagd | `gezondheid/omc` | omc running; notify-mock healthy; HTTP 200 [openzaak/open-zaak:1.29.0, worthnl/notifynl-omc:1.17.19] |
| overgeslagen | `gezondheid/zac` | gepland, nog niet in de stack: niet draaibaar hier: image alleen op ghcr.io (geblokkeerd), bouwen uit broncode vraagt Gradle, JDK 21 en Node met enkele GB cache, plus Solr, OPA, Gotenberg, SmartDocuments en KVK/BAG; past niet in de vrije schijfruimte van deze machine |
| overgeslagen | `gezondheid/podiumd-adapter` | gepland, nog niet in de stack: niet nodig: koppelt KISS en ITA aan de e-Suite (licentie), niet aan Open Zaak en Open Klant |
| overgeslagen | `gezondheid/zaakbrug` | gepland, nog niet in de stack: optioneel in PodiumD (StUF-ZKN naar ZGW voor oude zaaksystemen); geen StUF-afnemer in deze stack |
| overgeslagen | `gezondheid/zgw-office-addin` | gepland, nog niet in de stack: niet draaibaar hier: alleen op ghcr.io en vraagt Microsoft 365 (Word/Outlook-invoegtoepassing) |
| overgeslagen | `gezondheid/kiss-elastic-sync` | gepland, nog niet in de stack: niet opgenomen: vult de zoekindexen van KISS (kennisbank, website, smoelenboek) uit externe bronnen (SDG, website, SharePoint); crawler staat op docker.elastic.co (geblokkeerd) |
| overgeslagen | `gezondheid/frank-gateway` | gepland, nog niet in de stack: niet opgenomen: uitgaande gateway naar landelijke registers (BRP, KVK, BAG); hier praat alles direct met de mocks |
| overgeslagen | `gezondheid/brp-personen-mock` | gepland, nog niet in de stack: niet draaibaar hier: ghcr.io geblokkeerd; vervangen door de iswish-mock met tools/brp_vertaler.py |

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
| geslaagd | `rook/openzaak/zaakobject-verwijst-naar-open-object` | http://objecten.local:8000/api/v2/objects/e6bad707-c33d-443d-a993-10cdda35fb49 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-mag-niet-schrijven` | POST /zaken gaf 403 |
| geslaagd | `rook/openzaak/applicatie-burgerportaal-heeft-geen-toegang-tot-autorisaties` | GET /applicaties gaf 403 |
| geslaagd | `rook/openzaak/catalogus-met-gepubliceerde-zaaktypen` | Melding openbare ruimte, Omgevingsvergunning aanvragen, Parkeervergunning bewoners aanvragen, Wmo-maatwerkvoorziening aanvragen |
| geslaagd | `rook/opennotificaties/kanalen` | autorisaties, besluiten, besluittypen, documenten, informatieobjecttypen, internetaken, klantcontacten, objecten, partijen, producten, zaaktypen, zaken |
| geslaagd | `rook/opennotificaties/keten-open-zaak-open-notificaties-abonnee` | 'zaken/partial_update' afgeleverd na 4.4s |
| geslaagd | `rook/openklant/partij-en-klantcontacten-van-burger-a-token-burgerportaal` | Stephan Janssen: 3 klantcontact(en), via telefoon |
| geslaagd | `rook/openobject/melding-openbare-ruimte-token-burgerportaal` | 2 meldingen; deze: Bestrating |
| geslaagd | `rook/selectielijst/procestypen-2020` | 29 procestypen |
| geslaagd | `rook/referentielijsten/tabel-kanaal` | 6 kanalen: chat, webformulier, post, balie, telefoon, email |
| geslaagd | `rook/openinwoner/digid-login-en-mijn-aanvragen-van-burger-a` | VBS-2026-000101, VBS-2026-000102; 2 links naar een zaak |
| geslaagd | `rook/openinwoner/zaakdetail-met-status-en-documenten` | VBS-2026-000102: statushistorie tot 'afgehandeld', 2 documenten, download is een PDF (850 bytes) |
| geslaagd | `rook/openinwoner/mijn-taken-uit-open-object-externe-taken` | taken van A op de homepage: Aanvullende tekening dakkapel aanleveren, Leges omgevingsvergunning betalen |
| geslaagd | `rook/openinwoner/mijn-profiel-met-brp-gegevens` | Stephan Janssen, Mandelaplein 2, geboren 06 april 1975 |
| geslaagd | `rook/openinwoner/mijn-vragen-uit-open-klant` | Mijn vragen (1): 'Wanneer wordt de grofvuilpas verstuurd?' |
| geslaagd | `rook/openformulieren/formulier-melding-openbare-ruimte-digid-zaak-in-open-zaak` | Melding openbare ruimte: 1 stap(pen), login DigiD |
| geslaagd | `rook/openformulieren/inwoner-logt-in-brp-prefill-verstuurt-melding-zaak-in-open-z` | Paula Prins (uit de BRP) > zaak ZAAK-2026-0000000001 (Melding openbare ruimte), 1 document(en) |
| geslaagd | `rook/brp-api/brp-api-personen-2-in-officieel-formaat` | geboorte.datum als Datum-object, verblijfplaats.verblijfadres genest |
| geslaagd | `rook/objecttypen/podiumd-objecttypen-met-vaste-uuid-s-melding-tot-en-met-acti` | 7 objecttypen aanwezig; zonder token 401 |
| geslaagd | `rook/openobject/afdelingen-groepen-en-medewerkers-van-voorbeeldstad-objecten` | 3 afdeling, 2 groep, 3 medewerker |
| geslaagd | `rook/kiss/klantcontactmedewerker-logt-in-via-keycloak-realm-podiumd` | ingelogd, rol klantcontactmedewerker, rechten: afdelingen, groepen, skillsread, berichtenread, ... |
| geslaagd | `rook/kiss/afdelingen-en-groepen-uit-de-objecten-api` | 3 afdelingen (Klantcontactcentrum, Vergunningen, Zorg en Welzijn), 2 groepen |
| geslaagd | `rook/kiss/zaak-opzoeken-in-open-zaak` | VBS-2026-000101: Plaatsen dakkapel achterzijde woning |
| geslaagd | `rook/kiss/contactverzoek-opzoeken-in-open-klant` | klantcontact 8000000001: Terugbelverzoek over de dakkapel |
| geslaagd | `rook/kiss/persoon-zoeken-in-de-brp` | Stephan Janssen |
| geslaagd | `rook/kiss/zonder-login-geen-zaken-en-geen-klantcontacten` | 302 naar Keycloak, 302 naar Keycloak |
| geslaagd | `rook/ita/werkvoorraad-per-medewerker-contactverzoeken-uit-open-klant` | Desai ziet ['8000000001'], Jansen ziet ['8000000002'] |
| geslaagd | `rook/ita/medewerker-opent-eigen-taak-niet-die-van-een-andere-afdeling` | eigen taak 200 (Terugbelverzoek over de dakkapel), taak van KCC 403 |
| geslaagd | `rook/ita/functioneel-beheerder-ziet-alle-taken-zonder-login-401` | beheerder [200, 200]; zonder login 401 |
| geslaagd | `rook/pabc/applicatierollen-per-zaaktype-voor-een-functionele-rol` | Team Wmo: Wmo-maatwerkvoorziening aanvragen met rollen behandelaar; zonder sleutel 401 |
| geslaagd | `rook/openarchiefbeheer/afgesloten-zaken-uit-open-zaak-klaar-voor-een-vernietigingsl` | 4 afgesloten zaken: VBS-2026-000102, VBS-2026-000103, VBS-2026-000105, VBS-2026-000108 |
| geslaagd | `rook/openarchiefbeheer/medewerker-logt-in-via-keycloak-realm-podiumd` | ingelogd als beheer.devries |
| geslaagd | `rook/openbeheer/zaaktypen-van-voorbeeldstad-uit-open-zaak` | service catalogi-api: 4 zaaktypen (Melding openbare ruimte, Omgevingsvergunning aanvragen, ...) |
| geslaagd | `rook/openbeheer/oidc-configuratie-wijst-naar-keycloak-realm-podiumd` | {"enabled":true,"loginUrl":"http://openbeheer.local:8000/auth/oidc/authenticate/"} |
| gefaald (bekend) | `rook/omc/keten-zaak-in-open-zaak-open-notificaties-omc-e-mail-via-not` | geen bericht over VBS-OMC-1461624064 binnen 45 s: OMC 1.17.19 weigert de notificatie van Open Notificaties 1.16 (veld 'source', 206/422), zie README Bekend: NotifyNL OMC 1.17.19 (de versie in PodiumD 4.9.3) weigert de notificaties van Open Notificaties 1.16.2 met 206 en statuscode 422: die bevatten het veld "source", dat het model van OMC niet kent. OMC zelf werkt (zie de rooktest met een notificatie in het OMC-formaat); de koppeling tussen deze twee versies niet. |
| geslaagd | `rook/omc/notificatie-in-het-omc-formaat-wordt-een-e-mail-aan-de-inwon` | zonder JWT 401; 202, e-mail (template zaak aangemaakt) aan 999995406@inwoner.voorbeeldstad.example voor Paula Prins |
| geslaagd | `rook/clamav/clamd-herkent-het-eicar-testbestand-en-laat-een-gewoon-besta` | stream: Eicar-Test-Signature FOUND; schoon bestand: stream: OK |
| geslaagd | `rook/openformulieren/upload-met-het-eicar-testvirus-wordt-geweigerd-clamav` | EICAR 400 (Er is een virus gedetecteerd in het bestand: 'Eicar-Test-Signature'.), schoon bestand 200 |
| geslaagd | `rook/mailpit/smtp-opvang-ontvangt-en-toont-een-bericht` | bericht 'Rooktest demogemeente 1791461674' zichtbaar in Mailpit |
| overgeslagen | `rook/postgres` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/redis` | infrastructuur: alleen gezondheid |
| overgeslagen | `rook/notificatie-sink` | infrastructuur: alleen gezondheid |

## zgw

| Status | Check | Toelichting |
|---|---|---|
| geslaagd | `zgw/gedrag/overzicht-naar-detail` | 4 stap(pen), 2 waarschuwing(en), o.a. MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/84 |
| geslaagd | `zgw/gedrag/zonder-token` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 403 response is not described in the schema. Expected content types: application/problem+json. |
| geslaagd | `zgw/gedrag/onbekende-zaak` | 1 stap(pen), 1 waarschuwing(en), o.a. Content type application/json for 404 response is not described in the schema. Expected content types: application/problem+json. |
| gefaald (bekend) | `zgw/gedrag/burger-a-haalt-zaak-van-burger-b` | stap a-haalt-zaak-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $statusCode == 404"} Bekend: ZGW 1.x autoriseert per applicatie, niet per burger: het applicatietoken mag elke zaak van de geautoriseerde zaaktypen lezen (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/gedrag/burger-a-zoekt-op-bsn-van-burger-b` | stap a-zoekt-op-bsn-van-b: success criteria check: Checking simple criteria: {"condition":"$statusCode == 403 \|\| $response.body#/count == 0"} Bekend: In ZGW is het BSN een queryfilter dat de client kiest; Open Zaak controleert niet wie de burger is (aansluitprofielen/README.md). |
| gefaald (bekend) | `zgw/strikt/overzicht-naar-detail` | stap zoek-zaken: schema check: MINLENGTH must NOT have fewer than 9 characters 69 \| "archiefactiedatum": "2031-09-09", 70 \| "resultaat": "http://openzaak.local:8000/zaken/api/v1/resultaten/8417759a-811f-4f9b-9e0b-b37ad49e0d6a", > 71 \| "opdrachtgevendeOrganisatie": "", \| ^^ 👈🏽 minLength must NOT have fewer than 9 characters 72 \| " Bekend: Open Zaak 1.29 wijkt op schema en content-type af van het profiel (403/404 als application/json, opdrachtgevendeOrganisatie ""), zie aansluitprofielen/README.md. |
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
| geslaagd | `burger-isolatie/openformulieren/b-heeft-data` | B heeft inzending 6b2b90ea..., prefill Eleonora de Crooy |
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
| brp-api | `openzaak/open-zaak:1.29.0` | Up 6 minutes (healthy) |
| brp-mock | `iswish/haal-centraal-brp-bevragen-gba-mock:2.0.6` | Up 6 minutes |
| clamav | `clamav/clamav:1.5.4` | Up 6 minutes (healthy) |
| elasticsearch | `elasticsearch:9.0.3` | Up 6 minutes (healthy) |
| ita | `demogemeente/ita-web:3.3.2` | Up 4 minutes (healthy) |
| ita-poller | `demogemeente/ita-poller:3.3.2` | Up 4 minutes |
| keycloak | `keycloak/keycloak:26.4.7` | Up 6 minutes (healthy) |
| keycloak-clients | `keycloak/keycloak:26.4.7` | Exited (0) 4 minutes ago |
| keycloak-podiumd | `keycloak/keycloak:26.4.7` | Exited (0) 4 minutes ago |
| kiss | `demogemeente/kiss:3.1.3` | Up 4 minutes (healthy) |
| mailpit | `axllent/mailpit:v1.31.4` | Up 6 minutes (healthy) |
| notificatie-sink | `openzaak/open-zaak:1.29.0` | Up 6 minutes (healthy) |
| notify-mock | `openzaak/open-zaak:1.29.0` | Up 6 minutes (healthy) |
| objecten | `maykinmedia/objects-api:3.6.2` | Up 5 minutes (healthy) |
| objecten-celery | `maykinmedia/objects-api:3.6.2` | Up 5 minutes |
| objecten-init | `maykinmedia/objects-api:3.6.2` | Exited (0) 5 minutes ago |
| objecttypen | `maykinmedia/objecttypes-api:3.4.2` | Up 6 minutes (healthy) |
| objecttypen-init | `maykinmedia/objecttypes-api:3.4.2` | Exited (0) 6 minutes ago |
| omc | `worthnl/notifynl-omc:1.17.19` | Up 5 minutes |
| openarchiefbeheer | `maykinmedia/open-archiefbeheer:2.0.0` | Up 4 minutes (healthy) |
| openarchiefbeheer-celery | `maykinmedia/open-archiefbeheer:2.0.0` | Up 3 minutes |
| openarchiefbeheer-celery-beat | `maykinmedia/open-archiefbeheer:2.0.0` | Up 3 minutes |
| openarchiefbeheer-init | `maykinmedia/open-archiefbeheer:2.0.0` | Exited (0) 5 minutes ago |
| openbeheer | `maykinmedia/open-beheer:0.9.1` | Up 4 minutes (healthy) |
| openbeheer-init | `maykinmedia/open-beheer:0.9.1` | Exited (0) 5 minutes ago |
| openformulieren | `openformulieren/open-forms:3.5.8` | Up 4 minutes (healthy) |
| openformulieren-celery | `openformulieren/open-forms:3.5.8` | Up 3 minutes |
| openformulieren-celery-beat | `openformulieren/open-forms:3.5.8` | Up 3 minutes |
| openformulieren-init | `openformulieren/open-forms:3.5.8` | Exited (0) 4 minutes ago |
| openinwoner | `maykinmedia/open-inwoner:2.4.3` | Up 2 minutes (healthy) |
| openinwoner-celery | `maykinmedia/open-inwoner:2.4.3` | Up 2 minutes |
| openinwoner-init | `maykinmedia/open-inwoner:2.4.3` | Exited (0) 2 minutes ago |
| openklant | `maykinmedia/open-klant:2.15.0` | Up 5 minutes (healthy) |
| openklant-celery | `maykinmedia/open-klant:2.15.0` | Up 5 minutes |
| openklant-init | `maykinmedia/open-klant:2.15.0` | Exited (0) 5 minutes ago |
| opennotificaties | `openzaak/open-notificaties:1.16.2` | Up 5 minutes (healthy) |
| opennotificaties-celery | `openzaak/open-notificaties:1.16.2` | Up 5 minutes |
| opennotificaties-celery-beat | `openzaak/open-notificaties:1.16.2` | Up 5 minutes |
| opennotificaties-init | `openzaak/open-notificaties:1.16.2` | Exited (0) 5 minutes ago |
| openzaak | `openzaak/open-zaak:1.29.3` | Up 4 minutes (healthy) |
| openzaak-celery | `openzaak/open-zaak:1.29.3` | Up 3 minutes |
| openzaak-init | `openzaak/open-zaak:1.29.3` | Exited (0) 4 minutes ago |
| pabc | `demogemeente/pabc-api:1.1.1` | Up 4 minutes (healthy) |
| pabc-migrations | `demogemeente/pabc-migrations:1.1.1` | Exited (0) 6 minutes ago |
| postgres | `postgis/postgis:17-3.5-alpine` | Up 6 minutes (healthy) |
| redis | `redis:8.10.2-alpine` | Up 6 minutes (healthy) |
| referentielijsten | `maykinmedia/referentielijsten-api:0.7.4` | Up 6 minutes (healthy) |
| selectielijst | `openzaak/vng-selectielijst:1.0.5` | Up 6 minutes (healthy) |
