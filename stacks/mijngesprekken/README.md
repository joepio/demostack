# MijnGesprekken-demo

Tijdelijke proof of concept naast de kern-stack: een inwoner voert in Open Inwoner een gesprek bij haar zaak, een medewerker antwoordt, en bij het afsluiten ontstaat een klantcontact in Open Klant. Alleen Caddy verbindt deze stack met de buitenwereld; zaken en de inwoner komen alleen-lezend uit de Open Zaak van de kern-stack.

Draait op de server in `/srv/demogemeente/mijngesprekken-demo` (deze map plus `.env`, de forks in `src/` en het filmpje). Klikpad en uitleg: [DRAAIBOEK.md](DRAAIBOEK.md).

| Adres | Wat | Bron |
|---|---|---|
| https://gesprekken.demostack.nl/regie/ | Regiepagina: inwoner links, medewerker rechts | `app/` (demo) |
| https://gesprekken-medewerker.demostack.nl/ | Medewerkerconsole: gesprekken, eventstroom, Open Klant | `app/` (demo) |
| https://gesprekken-inwoner.demostack.nl/ | Open Inwoner | fork joepio/open-inwoner, branch mijngesprekken-poc (PR maykinmedia/open-inwoner#3191) |
| https://gesprekken-api.demostack.nl/swagger/index.html | Gesprekken API, eventstroom op /api/v1/events | fork joepio/ZGW-APIs, branch gesprekken-poc (PR OneGround/ZGW-APIs#252) |
| https://gesprekken-klant.demostack.nl/admin/ | Open Klant 2.19.1, eigen instantie | Maykin |
| https://gesprekken.demostack.nl/video/mijngesprekken-demo.mp4 | Filmpje van het klikpad | `video/film.py` |

Specificatie: VNG-Realisatie/VNG-API-Lab#47 (MijnGesprekken next).

## Opbouw

- `docker-compose.yml`: Postgres, Redis, moto (S3), demo-app, Gesprekken API, Open Klant (met nginx ervoor, uWSGI leest geen chunked bodies), Open Inwoner en de eventvolger van Open Inwoner (`volg_gesprekken_events`).
- `app/`: token- en autorisatiestub voor de Gesprekken API (`/idp`, `/ac`, alleen intern), de medewerkerconsole en de regiepagina.
- `seed/`: inrichting. `openklant.py` (beheerder, token, actoren), `oip.yaml.example` (setup_configuration van Open Inwoner, vul de placeholders), `oip_inrichting.py`, `oip_menu.py` (Mijn profiel en Mijn aanvragen onder de homepage, anders niet in het menu), `oip_home.py` (welkomsttekst).
- `caddy/Caddyfile.example`: de Caddy-blokken, met placeholders voor de bcrypt-hash en het Swagger-token.
- `reset.sh`: maakt gesprekken, events en klantcontacten leeg; inrichting en Suzanne blijven.
- `video/film.py`: neemt het klikpad op met Playwright.

## Opzetten

1. `cp .env.example .env` en vul alles in (wachtwoorden en sleutels zelf genereren; `ONTVANGER_ACTOR` en `AUTO_ACTOR` zijn de actor-URL's die `seed/openklant.py` print).
2. Images bouwen uit de forks:
   `git clone -b gesprekken-poc https://github.com/joepio/ZGW-APIs src/zgw` en het Gesprekken-image bouwen als `mgdemo/grc:<commit>`;
   `git clone -b mijngesprekken-poc https://github.com/joepio/open-inwoner src/oip && docker build -t mgdemo/oip:<commit> src/oip`.
   Zet de tags in `docker-compose.yml`.
3. `docker compose up -d`, daarna de seeds:
   `docker compose exec -T mg-openklant python src/manage.py shell < seed/openklant.py`, Open Inwoner `setup_configuration` met de ingevulde `oip.yaml`, dan
   `docker compose exec -T mg-oip python src/manage.py shell < seed/oip_inrichting.py` (en zo ook `oip_menu.py` en `oip_home.py`).
4. Caddy-blokken uit `caddy/Caddyfile.example` toevoegen (hash met `caddy hash-password`), `systemctl reload caddy`.

## Inloggen

- Regie, medewerker, API en filmpje: `demo` / `CONSOLE_PASSWORD`.
- Inwoner: nep-DigiD van Open Inwoner, BSN 999993653 (Suzanne Moulin).
- Open Klant beheer: `admin` / `ADMIN_PASSWORD`. Open Inwoner beheer: `admin@demogemeente.local` / `ADMIN_PASSWORD`.

## Bekende beperkingen

- Autorisaties en tokens zijn een stub: elke client mag alles. De controle of een zaak bestaat staat uit (`Application__IgnoreZaakValidation`).
- Bestanden staan in moto, in het geheugen. Na een herstart van `mg-s3`: `./reset.sh` (maakt de bucket opnieuw).
- De Gesprekken API stuurt het automatische antwoord op elk bericht van de inwoner, niet alleen op het eerste.

## Weghalen

`docker compose down -v`, Caddy-blokken verwijderen, `systemctl reload caddy`.
