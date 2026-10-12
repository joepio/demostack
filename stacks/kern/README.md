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
| Open Inwoner (inwonerportaal PodiumD) | 2.4.6 | `inwoner.<domein>` |
| NL Portal (inwonerportaal Ritense) | 3.1.1 | `portaal.<domein>` |
| MijnOverheid-demo (VNG API Lab) met adapter | lab 482be6e | `mijnoverheid.<domein>` |
| IKO (Integraal Klant- en Objectbeeld) | 1.5.1 | `iko.<domein>` |
| Keycloak | 26.7.5 | `keycloak.<domein>` |
| Mailpit | 1.31.4 | `mail.<domein>` |

Intern: één Postgres (PostGIS 17) met een database per component, één Redis, Elasticsearch 8.19 en de BRP personen-mock. KvK-gegevens komen uit de openbare testomgeving van de KvK.

## Opzetten en bijwerken

    BASE_DOMAIN=demo.example.nl ./scripts/setup.sh    # eerste keer; maakt .env aan
    ./scripts/setup.sh                                 # daarna: brengt alles bij, maakt niets dubbel
    ./scripts/caddyfile.sh                             # print de Caddy-config voor deze stack
    ./scripts/domeinwissel.sh nieuw.domein.nl          # alles omzetten naar een ander domein; oude adressen verwijzen door

Werkplekken aan en uit (de registers draaien altijd):

    ./scripts/stack.sh status
    ./scripts/stack.sh uit gzac        # of: aan kcc, alleen gzac

Profielen: `kcc` (KISS, Elasticsearch, BRP-mock), `gzac` (GZAC), `zac` (ZAC met Solr, OPA, PABC, documentconversie), `oip` (Open Inwoner), `nlportal` (NL Portal), `mijnoverheid` (MijnOverheid-demo) en `iko` (IKO). De welkomstpagina toont wat uit staat.

Inloggen gaat overal via Keycloak (single sign-on), ook in de beheerschermen van de Django-apps. Account `demo` mag alles; daarnaast rol-accounts `kcc`, `redacteur`, `behandelaar`, `coordinator` en `beheerder`. Lokale `admin`-accounts in de beheerschermen bestaan nog als noodingang. Alle accounts gebruiken `ADMIN_PASSWORD` uit `.env`. Sessies duren een werkdag, met "onthoud mij" een week.

## Demodata

- Catalogus "Demogemeente" met zaaktype MOR "Melding openbare ruimte" (`scripts/seed_openzaak.py`). Het zaaktype voldoet aan de inrichtingseisen van ZAC (statustypen Intake t/m Afgerond, roltypen Initiator en Behandelaar, informatieobjecttype e-mail).
- ZAC: functionele rollen en groepen in Keycloak (`scripts/keycloak_zac.py`), autorisaties in PABC (`config/pabc-dataset.json`), zaakafhandelparameters voor MOR (`scripts/zac_inrichten.py`).
- Formulier "Melding openbare ruimte" (`scripts/seed_openforms.py`): kaart, inloggen met DigiD (demo), en registratie als zaak met leesbare omschrijving ("soort: plek"), toelichting, locatie (zaakgeometrie) en de inwoner als initiator (BSN).
- DigiD (demo): Keycloak-client `digid` geeft het BSN als claim; testinwoners `suzanne`, `lukas`, `merel` (`scripts/keycloak_digid.py`, `scripts/openforms_inrichting.py`).
- Demomeldingen met verschillende soorten, inwoners, locaties en statussen (`scripts/seed_meldingen.py`; `OPRUIMEN=1` verwijdert eerst de zaken van rooktests).
- KISS-objecttypen en -inhoud: afdelingen, teams, medewerkers, veelgestelde vragen (`scripts/seed_kiss_objecttypes.py`, `scripts/seed_kiss_objecten.py`), nieuws, werkinstructies, links en afhandelopties (`scripts/seed_kiss.sql.tmpl`).
- Testinwoner Suzanne Moulin, BSN 999993653, met een lopende melding (`scripts/seed_testpersoon.py`) en een open portaaltaak (TaakV2 in Objecten, `scripts/seed_portaaltaak.py`), zichtbaar in alle drie de portalen.

## Inwonerportalen

- **Open Inwoner**: koppelingen via `config/templates/openinwoner.yaml`; BRP, Objecten, de CMS-pagina's (Mijn profiel, Mijn aanvragen, Mijn berichten, takenblok), het importeren van zaaktypen en het abonnement op zaaknotificaties via `scripts/openinwoner_inrichting.py`. Inloggen met DigiD (demo) via de Keycloak-client `digid`; de eerste keer vraagt het portaal om een e-mailadres.
- **NL Portal**: frontend en backend achter één adres (Caddy stuurt `/graphql` en `/api` naar de backend). Keycloak-clients `nl-portal` (browser) en `nl-portal-m2m` (token exchange v2, voegt `aanvrager.bsn` toe; `scripts/keycloak_portalen.py`). Het ZGW-geheim moet precies 32 tekens zijn: NL Portal kiest het JWT-algoritme op sleutellengte en Open Zaak accepteert alleen HS256.
- **Portaaltaken**: objecttype `Taak` volgens het TaakV2-schema van NL Portal (`config/objecttypes-schemas/taak.json`). GZAC schrijft portaaltaken nog in het oude formaat, die verschijnen dus niet in NL Portal.
- **MijnOverheid-demo**: de app uit het [VNG API Lab](https://github.com/VNG-Realisatie/VNG-API-Lab) op een vaste commit, met een adapter (`services/mijnoverheid/`). Dit is een uitzondering op "ongewijzigde componenten": de app krijgt bij het bouwen een paar regels aangepast (API-basis, naam van de ingelogde inwoner, uitloggen). De adapter logt in met DigiD (demo) en vertaalt de Lab-API's MijnZaken, MijnTaken en de gegevenspagina naar Open Zaak, Objecten en de BRP-mock; de overige API's gaan door naar de mockserver van het Lab. De chatassistent werkt als `OPENROUTER_API_KEY` in `.env` staat.
- **IKO**: draait met inloggen via Keycloak (client `iko`, rol `ROLE_ADMIN`; `scripts/keycloak_iko.py`). Connectoren en profielen zijn nog niet ingericht.

## Rooktests

    docker compose run --rm -T -e BASE_DOMAIN -v $PWD/scripts:/scripts:ro openforms python /scripts/test_submission.py
    docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -v $PWD/scripts:/scripts:ro openforms python /scripts/test_kiss_login.py

## Opbouw

- `config/templates/`: setup_configuration per component, met `${VAR}` uit `.env`. `scripts/render-config.sh` schrijft ze naar `config/generated/`.
- Open Notificaties: Open Zaak en Objecten sturen hun wijzigingen naar de kanalen zaken, documenten, besluiten, objecten enz. Rooktest: `scripts/test_notificatie.py`.
- `config/nginx/`: nginx tussen Caddy en de Django-apps (zoekt containernamen dynamisch op, zodat een herstarte app direct bereikbaar is). KISS stuurt request-bodies chunked en uWSGI leest die als leeg; nginx buffert ze en zet een Content-Length.
- `config/objecttypes-schemas/`: JSON-schema's voor de KISS-objecttypen, uit [Dimpact-Samenwerking/objecttypes2](https://github.com/Dimpact-Samenwerking/objecttypes2).
- `welkom/`: template en build-script voor de welkomstpagina. `welkom/evaluatie.py` maakt de stackvergelijking (API's en versies live uit de OpenAPI-specificaties, geheugen en images live uit Docker, licenties); zet elk kwartier in cron.
- De KISS-zoekindex wordt bijgewerkt met `docker compose run --rm kiss-sync-vac` en `kiss-sync-smoelenboek`; zet dit in cron.

## Nog niet gekoppeld

- Open Klant aan Open Formulieren.
- Kennisartikelen (producten en diensten) in KISS: het objecttype bestaat, inhoud nog niet.
- eHerkenning: alleen DigiD (demo) is ingericht.
- GZAC is nog niet gekoppeld aan Open Zaak: het draait met de eigen demo-casus.
- IKO heeft nog geen connectoren (Open Zaak, BRP, Open Klant) en geen profiel voor een inwonerbeeld.
- NL Portal: geen bewoningsgegevens (de BRP-mock heeft geen Bewoning-API) en geen eHerkenning.
- ZAC: zaken die Open Formulieren direct in Open Zaak aanmaakt verschijnen in de werkvoorraad, maar zonder ZAC-takenmodel (CMMN). Dat start alleen als ZAC de zaak zelf aanmaakt, bijvoorbeeld via een productaanvraag in Objecten.
- GZAC zet bij elke start de rechten terug; `gzac-permissions` herstelt ze automatisch.
