# OpenEvents op DemoStack

Een eventregister naast de kern-stack: [joepio/openevents](https://github.com/joepio/openevents). Het laat zien wat een generiek register met CloudEvents, een query-engine met autorisatie als query, en een live stroom doet met echte zaken uit Open Zaak.

| Adres | Wat |
|---|---|
| https://events.demostack.nl/ui | Beheer-UI: stand, events (live), query, schrijven; "Bekijk als" met persona's |
| https://events.demostack.nl/mijn/zaken, https://events.demostack.nl/mijn/taken | MijnZaken en MijnTaken (lab `next`) voor de MijnOverheid-demo: zet ze in de API-inspector van mijnoverheid.chat, met een dev-token zoals `dev:https://id.example.nl/jan\|rol=inwoner` |
| https://events.demostack.nl/profiles/nl.vng.zgw.zaken/openapi.json | OpenAPI van de zaakspiegel, gegenereerd uit het profiel |

## Wat er in staat

- **Zaakspiegel uit Open Zaak.** OpenEvents abonneert zich zelf bij Open Notificaties op kanaal `zaken`. Elke notificatie wordt een event (`nl.vng.zgw.zaken.status.create` enz.), de stand van de zaak volgt daaruit. Profiel: `examples/profiles/zgw-zaken.json`.
- **Gesimuleerde stroom** (`oe-sim`): meldingen openbare ruimte, aanvragen omgevingsvergunning en gesprekken in Demodam, met 30 dagen historie.

## Wat er in de andere applicaties nodig was

Bewust zo weinig mogelijk:

| Applicatie | Wijziging |
|---|---|
| Open Zaak | eigen client `openevents` (alle autorisaties, alleen-lezen gebruikt) in `stacks/kern/config/templates/openzaak.yaml` |
| Open Notificaties | client `openevents` in `opennotificaties.yaml`; het abonnement maakt OpenEvents zelf aan en het controleert elke 5 minuten of het er nog is (overleeft een reset) |
| Keycloak | publieke client `mijn-demodam` (in `stacks/kern/scripts/keycloak_portalen.py`) voor inloggen in `/mijnoverheid`, met claims `rol=inwoner` en `bsn`; OpenEvents controleert verder alleen tokens van realm `demogemeente` |
| Kern-stack | `OE_ZGW_SECRET` in de kern-`.env` (`setup.sh` maakt het aan); `demo_reset.sh herstel` past de clients uit de templates opnieuw toe |
| Caddy | één blok (`caddy/Caddyfile.example`) |
| DNS | `events.demostack.nl` |

In de audit-trail van Open Zaak staat OpenEvents onder zijn eigen naam.

## Opzetten

1. In de kern: `OE_ZGW_SECRET` in `.env` (of `scripts/setup.sh`), dan `scripts/render-config.sh` en `setup_configuration` voor `opennotificaties` en `openzaak` (zoals in `setup.sh`).
   Hier: `cp .env.example .env` en vul in (`OE_ZGW_SECRET` uit de kern-`.env`).
2. `git clone https://github.com/joepio/openevents src/openevents`
3. `docker compose up -d --build`
4. Caddy-blok uit `caddy/Caddyfile.example` toevoegen, `systemctl reload caddy`.
5. Controle: `docker compose logs oe-server | grep -i notificaties` toont "subscribed at Open Notificaties"; maak een zaak in ZAC of GZAC en kijk in de UI bij type `nl.vng.zgw.zaak`.

## Privacy

OpenEvents slaat geen echt BSN op: met `OE_PSEUDONYM_KEY` worden het BSN in het Keycloak-token en in de rollen van Open Zaak hetzelfde pseudoniem, zodat Mijn Demodam blijft werken. Gesprekken en taken worden een jaar na afsluiten of afronden vanzelf verwijderd (`retention` in de profielen). Handmatig verwijderen (`DELETE /subjects/...`) kan hier niet, omdat `OPENEVENTS_ADMINS` leeg is. Zie `docs/wissen.md` in OpenEvents.

## Inloggen

Persona's zijn alleen om te bekijken: kies rechtsboven een persona ("Bekijk als") in de beheer-UI of in Mijn Demodam en je ziet wat die persoon mag zien. Iets doen (een taak afronden, een bericht sturen) vraagt een echte login via Keycloak, bijvoorbeeld met de snelkeuze voor suzanne. De simulator tekent zijn eigen tokens met `OE_JWT_SECRET`, dat alleen de server en de simulator kennen. Niemand kan via de API profielen wijzigen (`OPENEVENTS_ADMINS` is leeg).

`/health` en `/metrics` (Prometheus, alleen tellingen en tijden) staan open. Backups staan hier uit, want DemoStack-data mag altijd weg; zie `docs/beheer.md` in OpenEvents om ze aan te zetten.

Wil je dat wat bezoekers schrijven niet blijft staan: `cp cron/demostack-openevents /etc/cron.d/` maakt OpenEvents elke nacht om 04:30 leeg (`reset.sh`).

## Leegmaken en weghalen

- `./reset.sh` maakt OpenEvents leeg en laat de simulator opnieuw beginnen.
- Weghalen: `docker compose down -v`, Caddy-blok verwijderen, `systemctl reload caddy`. Het abonnement in Open Notificaties verdwijnt bij de volgende reset van de kern.
