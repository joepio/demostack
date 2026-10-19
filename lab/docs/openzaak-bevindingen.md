# Open Zaak: bevindingen uit de demo

Gevonden op 7 oktober 2026 met `openzaak/open-zaak:1.29.0` (Zaken API 1.5.1) in stack
`kern`, met de seed van DemoStack, het ZGW-aansluitprofiel (categorie `zgw`) en losse
aanroepen. Ze gelden voor elke afnemer van Open Zaak, niet voor een bepaald product.

## D1. Autorisaties per zaaktype hangen aan de hostnaam

De autorisaties van een applicatie met rechten per zaaktype (zoals `burgerportaal`) staan
per zaaktype-URL (`http://openzaak.local:8000/catalogi/api/v1/zaaktypen/...`). Open Zaak
bouwt de zaaktype-URL van een zaak uit de Host-header van het request. Via een andere host
(bijvoorbeeld de hostpoort `127.0.0.1:8001`) komt die URL niet overeen:

- `GET /zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=...` geeft 200 met
  resultaten;
- `GET /zaken/{uuid}`, `GET /statussen/{uuid}` en de documenten geven 403.

Bewijs: dezelfde zaak (`VBS-2026-000102`) met hetzelfde token geeft 403 via
`http://127.0.0.1:8001`, 200 via `http://openzaak.local:8000`, en ook 200 via
`127.0.0.1:8001` met de header `Host: openzaak.local:8000`. Voor een applicatie met
`heeftAlleAutorisaties` (zoals `demogemeente-beheer`) maakt de hostnaam niet uit.

Gevolg: alles wat met zaaktype-autorisaties werkt, moet Open Zaak onder zijn canonieke URL
aanroepen. Binnen het docker-netwerk gaat dat vanzelf. Vanaf de host: `127.0.0.1
openzaak.local` in `/etc/hosts` en `python3 tools/poort_doorsturen.py 8000 8001`, of
`PORT_OPENZAAK=8000` in `.env`. Bij een online demo met een publieke hostnaam: maak die
hostnaam de canonieke (`ALLOWED_HOSTS`, en de autorisaties met die URL zetten).

## D2. `expand=status.statustype` vouwt niets uit

Met `expand=status.statustype` geeft Open Zaak 1.29.0 een lege `_expand`. Het pad wordt
pas uitgevouwen als de ouder er ook bij staat:

| `expand=` | `_expand` in het eerste resultaat |
|---|---|
| `status.statustype` | `{}` |
| `status` | `{"status": {...}}` |
| `status,status.statustype` | `{"status": {..., "_expand": {"statustype": {...}}}}` |

Getest met een alleen-lezen-applicatie en met `demogemeente-beheer` (alle rechten); het
resultaat is hetzelfde, dus het komt niet door autorisaties. Een afnemer die alleen
`status.statustype` vraagt, valt terug op losse calls per zaak. De stap `zoek-zaken` in
het ZGW-aansluitprofiel van het VNG API Lab zegt "Eén call met expand"; tegen Open Zaak
klopt dat alleen met `status,status.statustype`.

## D3. Afwijkingen van het eigen OpenAPI-schema

Gevonden met het ZGW-aansluitprofiel in de modus "strikt" (zie
[`aansluitprofielen/README.md`](../aansluitprofielen/README.md)):

1. Foutantwoorden (401/403/404) hebben `Content-Type: application/json`; het schema en de
   ZGW-standaard zeggen `application/problem+json`.
2. `opdrachtgevendeOrganisatie` is `""` bij een zaak zonder opdrachtgever, terwijl het
   schema `minLength: 9` eist.
3. `Status.gezetdoor` is `null`; in het schema van Open Zaak mag dat, in de
   gemma-zaken-spec 1.5.1 niet.
4. Het geserveerde schema is niet direct bruikbaar in Ajv: `nullable` zonder `type`
   (79 keer) en discriminators zonder const/enum in de varianten.
   `aansluitprofielen/normaliseer_schema.py` repareert dat zonder de inhoud te veranderen.

## D4. ZGW 1.x autoriseert per applicatie, niet per burger

Het token van een applicatie mag elke zaak van de geautoriseerde zaaktypen lezen, en het
BSN is een queryfilter dat de afnemer zelf kiest. Een portaal of Mijn-API op ZGW moet de
burger dus zelf uit een geverifieerd token halen en per zaak en document controleren. De
twee workflows `zgw/gedrag/burger-a-*` laten dat zien en staan daarom bewust als bekende
fout in het rapport. De categorie `burger-isolatie` test die controle op elk portaal en
elke Mijn-API in de stack, ook die van een plug-in.
