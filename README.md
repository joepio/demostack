# Common Ground Demostack

Een werkende demogemeente met ongewijzigde open source Common Ground-componenten, in één commando op te zetten.
Bedoeld om de componenten en standaarden te laten zien, te analyseren en (later) te toetsen op naleving van de API-specificaties.

> Status: werkversie. Een hulpmiddel van VNG rond de Common Ground-standaarden.

## Uitgangspunten

- **Leveranciersneutraal.** Geen productcode van een leverancier, geen voorkeur voor een component. Elk component dat een standaard-API implementeert kan als profiel worden toegevoegd en wordt op dezelfde manier getest.
- **Ongewijzigde componenten.** Officiële images, vaste versies. Alle aanpassingen zitten in configuratie en demodata. Uitzondering: de MijnOverheid-demo uit het VNG API Lab heeft geen image en krijgt een adapter (zie `stacks/kern/README.md`).
- **Reproduceerbaar.** `scripts/setup.sh` zet een stack van nul op en is veilig om opnieuw te draaien.
- **Geen echte gegevens.** BRP- en KvK-gegevens komen uit openbare testvoorzieningen.
- **Instantie-gegevens horen niet in deze repo.** Domein, wachtwoorden en tokens staan in een lokale `.env` die het setup-script aanmaakt.

## Stacks

| Stack | Inhoud | Map |
| --- | --- | --- |
| kern | Open Formulieren, Open Zaak, OneGround, Open Klant, Open VTB, Objecten, Objecttypen, Open Notificaties, KISS, ZAC, GZAC, Open Inwoner, NL Portal, MijnOverheid-demo, IKO, ZaakChat (met Keycloak, Elasticsearch, BRP-mock), Mailpit | [`stacks/kern`](stacks/kern) |

Gepland: compliance-tests tegen de API-specificaties (ZGW, Klantinteracties, Objecten) met een rapport per component en versie.

## Snel starten

Vereist: een Linux-server met Docker Compose, Caddy, ongeveer 12 GB vrij geheugen met alle profielen aan (16 GB RAM plus swap), en DNS voor `<domein>` en `*.<domein>`.

    cd stacks/kern
    BASE_DOMAIN=demo.example.nl ./scripts/setup.sh
    ./scripts/caddyfile.sh | sudo tee /etc/caddy/Caddyfile && sudo systemctl reload caddy

Open daarna `https://demo.example.nl/` voor de welkomstpagina met alle ingangen per rol.

## Licentie

EUPL-1.2. De componenten zelf vallen onder hun eigen licenties.
