# Draaiboek MijnGesprekken-demo

## Inloggen
- Regie, medewerkerconsole, Gesprekken API en filmpje (inlogvenster van de browser): `demo` / CONSOLE_PASSWORD (.env)
- Suzanne (inwoner): Log in met DigiD, "Met burgerservicenummer.", BSN `999993653`, geen wachtwoord
- Open Klant beheer: `admin` / ADMIN_PASSWORD (.env)
- Open Inwoner beheer (/admin/): `admin@demogemeente.local` / ADMIN_PASSWORD (.env)

## Klikpad

| # | Doen | Link | Software die je ziet |
|---|---|---|---|
| 1 | Open de regiepagina, log in met demo / CONSOLE_PASSWORD | https://gesprekken.demostack.nl/regie/ | Regiepagina (demo). Links Open Inwoner, rechts medewerkerconsole |
| 2 | Links: "Log in met DigiD", "Met burgerservicenummer.", 999993653, Inloggen | (los: https://gesprekken-inwoner.demostack.nl/digid/login/?next=/cases/1/a444cd2c-dbf1-4635-8566-12c202daebc8/status/) | Open Inwoner (Maykin, fork) met DigiD-mock |
| 3 | Zaak "Losliggende stoeptegel: Dorpsstraat 12" (ZAAK-2026-0000000001, in Mijn aanvragen de derde): scrol naar "Mijn gesprekken", klik "Nieuw gesprek" | https://gesprekken-inwoner.demostack.nl/cases/1/a444cd2c-dbf1-4635-8566-12c202daebc8/status/ | Open Inwoner; zaak en status uit Open Zaak (Maykin) |
| 4 | Onderwerp: *Wanneer wordt de stoeptegel gerepareerd?* | zelfde pagina | Open Inwoner |
| 5 | Bericht: *Ik meldde op 6 oktober een losse stoeptegel voor Dorpsstraat 12. De tegel ligt nu helemaal los en mijn buurvrouw met rollator struikelde er gisteren bijna over. Wanneer wordt dit gemaakt? Ik heb een foto bijgevoegd.* | zelfde pagina | Open Inwoner |
| 6 | Kies een pdf, klik "Start gesprek" | zelfde pagina | Open Inwoner zet pdf en gesprek in de Gesprekken API (OneGround, fork) |
| 7 | Wacht: automatisch antwoord verschijnt | zelfde pagina | Antwoord komt uit de Gesprekken API (OneGround) |
| 8 | Rechts: klik het gesprek aan | https://gesprekken-medewerker.demostack.nl/ | Medewerkerconsole (demo, stand-in voor zaaksysteem/KCC), leest de Gesprekken API |
| 9 | Klik op de pdf | zelfde | Download via de Gesprekken API (bestand in S3, in de demo nagebootst) |
| 10 | Tabblad "Eventstroom", dan terug naar "Gesprekken" en het gesprek weer aanklikken | ook: https://gesprekken-api.demostack.nl/api/v1/events | Live events van de Gesprekken API (GET /events) |
| 11 | Antwoord typen: *Beste mevrouw Moulin, dank voor uw foto. We hebben vandaag een afzetting bij de tegel geplaatst. De aannemer legt de tegel donderdag 13 november opnieuw. Excuses dat het zo lang duurde. Met vriendelijke groet, Team Openbare Ruimte* | zelfde | Medewerkerconsole |
| 12 | Klik "Antwoord versturen" | zelfde | Console schrijft de bijdrage in de Gesprekken API |
| 13 | Links: antwoord verschijnt vanzelf | zaakpagina | Open Inwoner volgt de events van de Gesprekken API |
| 14 | Links typen: *Fijn, dank u wel! Ik laat het mijn buurvrouw weten.*, verzend-pijltje | zaakpagina | Open Inwoner stuurt de bijdrage naar de Gesprekken API |
| 15 | Links "Vraag beantwoord", bevestig met OK | zaakpagina | Open Inwoner beëindigt het gesprek; de Gesprekken API maakt het klantcontact in Open Klant |
| 16 | Rechts: tabblad "Open Klant" (zo nodig na een paar seconden opnieuw) | https://gesprekken-medewerker.demostack.nl/ | Console leest het klantcontact uit Open Klant (Maykin) |
| 17 | Optioneel: Open Klant beheer, admin / ADMIN_PASSWORD, klantcontact openklikken | https://gesprekken-klant.demostack.nl/admin/klantinteracties/klantcontact/ | Open Klant beheer (Maykin): kanaal MijnGesprekken, Suzanne, gesprek en zaak |
| 18 | Voor techneuten | https://gesprekken-api.demostack.nl/swagger/index.html | Swagger van de Gesprekken API (OneGround) |

Na afloop: `./reset.sh` in deze map (gesprekken, events en klantcontacten leeg).

Filmpje van het hele klikpad: https://gesprekken.demostack.nl/video/mijngesprekken-demo.mp4
