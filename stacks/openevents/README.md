# OpenEvents op DemoStack

Een eventregister naast de kern-stack: [joepio/openevents](https://github.com/joepio/openevents). Het laat zien wat een generiek register met CloudEvents, een query-engine met autorisatie als query, en een live stroom doet met echte zaken uit Open Zaak.

| Adres | Wat |
|---|---|
| https://events.demostack.nl/ui | Beheer-UI: stand, events (live), query, schrijven; "Bekijk als" met persona's |
| https://events.demostack.nl/profiles/nl.vng.zgw.zaken/openapi.json | OpenAPI van de zaakspiegel, gegenereerd uit het profiel |

## Wat er in staat

- **Zaakspiegel uit Open Zaak.** OpenEvents abonneert zich zelf bij Open Notificaties op kanaal `zaken`. Elke notificatie wordt een event (`nl.vng.zgw.zaken.status.create` enz.), de stand van de zaak volgt daaruit. Profiel: `examples/profiles/zgw-zaken.json`.
- **Gesimuleerde stroom** (`oe-sim`): meldingen openbare ruimte, aanvragen omgevingsvergunning en gesprekken in Demodam, met 30 dagen historie.

## Wat er in de andere applicaties nodig was

Bewust zo weinig mogelijk:

| Applicatie | Wijziging |
|---|---|
| Open Zaak | geen: bestaande client `open-inwoner` (heeft alle autorisaties) |
| Open Notificaties | geen: OpenEvents maakt zijn abonnement zelf aan en controleert elke 5 minuten of het er nog is (overleeft de nachtelijke reset) |
| Keycloak | geen: OpenEvents controleert alleen tokens van realm `demogemeente` |
| Kern-stack | geen |
| Caddy | één blok (`caddy/Caddyfile.example`) |
| DNS | `events.demostack.nl` |

Concessie: in de audit-trail van Open Zaak lijkt OpenEvents op Open Inwoner. Een eigen client kost drie regels in `stacks/kern/config/templates/openzaak.yaml` en `opennotificaties.yaml`.

## Opzetten

1. `cp .env.example .env` en vul in (`OIP_ZGW_SECRET` uit de kern-`.env`).
2. `git clone https://github.com/joepio/openevents src/openevents`
3. `docker compose up -d --build`
4. Caddy-blok uit `caddy/Caddyfile.example` toevoegen, `systemctl reload caddy`.
5. Controle: `docker compose logs oe-server | grep -i notificaties` toont "subscribed at Open Notificaties"; maak een zaak in ZAC of GZAC en kijk in de UI bij type `nl.vng.zgw.zaak`.

## Inloggen

Dev-modus: kies rechtsboven een persona ("Bekijk als"). Alle data is demodata en mag weg; niemand kan via de API profielen wijzigen (`OPENEVENTS_ADMINS` is leeg). Machines kunnen ook een token van Keycloak (realm `demogemeente`) gebruiken.

## Leegmaken en weghalen

- `./reset.sh` maakt OpenEvents leeg en laat de simulator opnieuw beginnen.
- Weghalen: `docker compose down -v`, Caddy-blok verwijderen, `systemctl reload caddy`. Het abonnement in Open Notificaties verdwijnt bij de volgende reset van de kern.
