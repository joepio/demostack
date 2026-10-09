# Stack "kern"

Een melding van een inwoner, van formulier tot klantcontact.

| Component | Versie | Hostname |
| --- | --- | --- |
| Welkomstpagina | | `<domein>` |
| Open Formulieren | 4.0.2 | `formulieren.<domein>` |
| Open Zaak | 1.30.0 | `zaken.<domein>` |
| Open Klant | 2.19.1 | `klant.<domein>` |
| Objecten / Objecttypen | 3.6.2 / 3.4.2 | `objecten.<domein>`, `objecttypen.<domein>` |
| KISS | 3.2.0 | `kiss.<domein>` |
| ZAC (Dimpact), met Solr, OPA, PABC en Gotenberg | 5.8.0 | `zac.<domein>`, `pabc.<domein>` |
| GZAC (Valtimo), demo-casus evenementenvergunning | 13.49.1 | `gzac.<domein>` |
| Open Notificaties | 1.17.0 | `notificaties.<domein>` |
| Keycloak | 26.7.5 | `keycloak.<domein>` |
| Mailpit (basic auth) | 1.31.4 | `mail.<domein>` |

Intern: één Postgres (PostGIS 17) met een database per component, één Redis, Elasticsearch 8.19 en de BRP personen-mock. KvK-gegevens komen uit de openbare testomgeving van de KvK.

## Opzetten en bijwerken

    BASE_DOMAIN=demo.example.nl ./scripts/setup.sh    # eerste keer; maakt .env aan
    ./scripts/setup.sh                                 # daarna: brengt alles bij, maakt niets dubbel
    ./scripts/caddyfile.sh                             # print de Caddy-config voor deze stack

Werkplekken aan en uit (de registers draaien altijd):

    ./scripts/stack.sh status
    ./scripts/stack.sh uit gzac        # of: aan kcc, alleen gzac

Profielen: `kcc` (KISS, Elasticsearch, BRP-mock), `gzac` (GZAC) en `zac` (ZAC met Solr, OPA, PABC, documentconversie). De welkomstpagina toont wat uit staat.

Inloggen: gebruiker `admin` op alle beheerschermen en Mailpit; `kcc`, `redacteur` en `beheerder` in KISS; `behandelaar`, `coordinator` en `beheerder` in ZAC; `behandelaar` en `beheerder` in GZAC. Alle accounts gebruiken `ADMIN_PASSWORD` uit `.env`.

## Demodata

- Catalogus "Demogemeente" met zaaktype MOR "Melding openbare ruimte" (`scripts/seed_openzaak.py`). Het zaaktype voldoet aan de inrichtingseisen van ZAC (statustypen Intake t/m Afgerond, roltypen Initiator en Behandelaar, informatieobjecttype e-mail).
- ZAC: functionele rollen en groepen in Keycloak (`scripts/keycloak_zac.py`), autorisaties in PABC (`config/pabc-dataset.json`), zaakafhandelparameters voor MOR (`scripts/zac_inrichten.py`).
- Formulier "Melding openbare ruimte", registreert als zaak (`scripts/seed_openforms.py`).
- KISS-objecttypen en -inhoud: afdelingen, teams, medewerkers, veelgestelde vragen (`scripts/seed_kiss_objecttypes.py`, `scripts/seed_kiss_objecten.py`), nieuws, werkinstructies, links en afhandelopties (`scripts/seed_kiss.sql.tmpl`).
- Testinwoner Suzanne Moulin, BSN 999993653, met een lopende melding (`scripts/seed_testpersoon.py`).

## Rooktests

    docker compose run --rm -T -e BASE_DOMAIN -v $PWD/scripts:/scripts:ro openforms python /scripts/test_submission.py
    docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -v $PWD/scripts:/scripts:ro openforms python /scripts/test_kiss_login.py

## Opbouw

- `config/templates/`: setup_configuration per component, met `${VAR}` uit `.env`. `scripts/render-config.sh` schrijft ze naar `config/generated/`.
- Open Notificaties: Open Zaak en Objecten sturen hun wijzigingen naar de kanalen zaken, documenten, besluiten, objecten enz. Rooktest: `scripts/test_notificatie.py`.
- `config/nginx/`: nginx tussen Caddy en de Django-apps (zoekt containernamen dynamisch op, zodat een herstarte app direct bereikbaar is). KISS stuurt request-bodies chunked en uWSGI leest die als leeg; nginx buffert ze en zet een Content-Length.
- `config/objecttypes-schemas/`: JSON-schema's voor de KISS-objecttypen, uit [Dimpact-Samenwerking/objecttypes2](https://github.com/Dimpact-Samenwerking/objecttypes2).
- `welkom/`: template en build-script voor de welkomstpagina.
- De KISS-zoekindex wordt bijgewerkt met `docker compose run --rm kiss-sync-vac` en `kiss-sync-smoelenboek`; zet dit in cron.

## Nog niet gekoppeld

- Open Klant aan Open Formulieren.
- Kennisartikelen (producten en diensten) in KISS: het objecttype bestaat, inhoud nog niet.
- DigiD/eHerkenning: het formulier is anoniem.
- GZAC is nog niet gekoppeld aan Open Zaak: het draait met de eigen demo-casus.
- ZAC: zaken die Open Formulieren direct in Open Zaak aanmaakt verschijnen in de werkvoorraad, maar zonder ZAC-takenmodel (CMMN). Dat start alleen als ZAC de zaak zelf aanmaakt, bijvoorbeeld via een productaanvraag in Objecten.
- GZAC zet bij elke start de rechten terug; `gzac-permissions` herstelt ze automatisch.
