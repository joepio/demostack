# Stacks

Een stack is een complete, gekoppelde set componenten zoals een gemeente die zou kiezen:
"ik wil het Maykin-landschap", "ik wil wat PodiumD draait", "ik wil de G4-keuze" of "ik
wil de VCG-basisset". Elke stack start met hetzelfde commando, krijgt dezelfde testdata en
draait dezelfde testsuite. Zo vergelijk je landschappen, en test je een eigen component
(als plug-in, zie [`docs/PLUGINS.md`](../docs/PLUGINS.md)) op elk ervan.

```bash
scripts/stack.sh list               # welke stacks er zijn, met status
scripts/stack.sh up kern            # starten, wachten tot gezond, testdata laden
scripts/stack.sh test kern          # testsuite: results/kern.json en results/kern.md
scripts/stack.sh down kern          # stoppen en volumes wissen (--behoud-data om te bewaren)
scripts/stack.sh up kern --plugin <map>   # met een component van een leverancier
```

Er draait steeds één stack tegelijk: alle stacks gebruiken dezelfde hostpoorten voor
dezelfde componenten, en `up` weigert te starten zolang er containers van een andere
stack staan.

| Stack | Status | Inhoud |
|---|---|---|
| `kern` | werkt | variant 1: Open Zaak, Open Notificaties, Open Object, Open Klant, Open Product, Referentielijsten, Selectielijst |
| `maykin` | werkt | kern plus Open VTB, Open Formulieren en Open Inwoner (met Elasticsearch en een BRP-vertaler) |
| `dimpact` | werkt | wat PodiumD 4.9.3 draait: KISS, ITA, PABC, Open Formulieren, Open Inwoner, losse Objecten en Objecttypen, Open Archiefbeheer, Open Beheer, OMC, ClamAV; ZAC niet draaibaar (ghcr.io, schijf) |
| `g4` | werkt | Platform Dienstverlening: NL Portal en IKO (uit broncode gebouwd), Valtimo/GZAC met een zaakproces, Open Formulieren en Open VTB op de kern; GZAC-portaaltaak niet zichtbaar in NL Portal (bekend) |
| `vcg` | werkt | de VCG-basisset op de kern: Open Organisatie, GPP-publicatiebank, Open Beheer, Operaton met procesworker, OpenPlan, OpenPDC en OpenPub (WordPress), OpenRegister (Nextcloud) en OpenFSC met drie peers; Operaton Modeler en OpenFTV niet draaibaar |

Een stack met status "skelet" start nu de kern; de geplande componenten staan in zijn
`stack.yaml` onder `gepland` en verschijnen in het testrapport als "overgeslagen: gepland".

## Opbouw

```
stacks/
  basis/compose.yml     Postgres, Redis, Keycloak (DigiD-simulatie), BRP-mock,
                        notificatie-sink, en de hulpcontainers tools en respect
  basis/stack.yaml      manifest van die infra, plus de testburgers A, B en C
  <naam>/stack.env      voor scripts/stack.sh: compose-bestanden, versies, databases
  <naam>/stack.yaml     voor de testsuite: componenten, burgerkanalen, zgw, bekende fouten
  <naam>/compose.yml    de services van de stack
  <naam>/README.md      wat erin zit, wat werkt, wat nog niet
  <naam>/env.example    optioneel: extra geheimen; up vult .env daarmee aan
  <naam>/seed.py        optioneel: extra testdata na de gedeelde seed
  <naam>/tests.py       optioneel: extra rooktests en isolatietypes
```

`scripts/stack.sh` voert compose uit met `stacks/basis/compose.yml`, dan de bestanden uit
`STACK_COMPOSE` en dan die van de plug-ins (`--plugin`, zie
[`docs/PLUGINS.md`](../docs/PLUGINS.md)). De projectnaam is `demogemeente-<naam>`, dus elke
stack heeft eigen volumes.

### stack.env

```bash
STACK_TITEL="..."
STACK_STATUS=werkt            # werkt | in-opbouw | skelet
STACK_COMPOSE="stacks/kern/compose.yml stacks/maykin/compose.yml"
DB_EXTRA="openformulieren openinwoner:postgis"   # extra databases, naam:extensies
IMAGE_OPENZAAK=openzaak/open-zaak:1.29.3          # andere versie dan de kern
```

De kern leest zijn images uit `IMAGE_<COMPONENT>` met een vaste standaardtag, zodat een
stack de kern kan hergebruiken met andere versies.

### stack.yaml

Formaat en voorbeeld: `stacks/basis/stack.yaml` en `stacks/kern/stack.yaml`. In het kort:

- `erft: kern` neemt componenten, burgerkanalen, `zgw` en bekende fouten over;
  `zonder: [openproduct]` haalt componenten weg.
- `componenten`: per component de compose-services en een health-URL (vanuit het
  docker-netwerk). Met `seed: false` slaat de gedeelde seed het component over.
- `gepland`: componenten die er nog niet zijn, met een opmerking.
- `burgerkanalen`: elk portaal of elke burger-API, met een `type` voor de isolatietest.
- `zgw`: de zaken-URL van Open Zaak en het Arazzo-profiel.
- `bekende_fouten`: check-id (of patroon met `*`) met uitleg. Zo'n fout blijft zichtbaar
  in het rapport, maar laat de exitcode niet falen.

## Afspraken voor nieuwe componenten

- **Hostnaam.** Netwerkalias `<component>.local` (Django accepteert geen hostnamen zonder
  punt). Dezelfde component heeft in elke stack dezelfde alias, zodat seed en tests overal
  werken. Open Zaak blijft `openzaak.local:8000`: de autorisaties zijn aan die hostnaam
  gebonden (bevinding D1 in `docs/openzaak-bevindingen.md`).
- **Versies.** Altijd een vaste tag, nooit `latest`. Waar een stack een bron heeft
  (PodiumD-chart, VCG-basisset), volg die en noem de bron in de README van de stack.
- **Geheimen.** Nooit in compose of git; `__GENEREER__` in `stacks/<naam>/env.example`.
- **Configuratie.** Liefst met setup-configuration (Maykin) of de eigen importmechanismen
  van het component, in `config/<component>/`. Handwerk in een admin telt niet.
- **Databases en Redis.** Een database per component via `DB_EXTRA`. De kern gebruikt
  Redis-databases 0 tot en met 11; nieuwe componenten nemen 12 tot en met 31.
- **Hostpoorten.** kern: 8001 tot 8010, 8080, 8090, 55432. maykin 8100-8149,
  dimpact 8150-8199, g4 8200-8249, vcg 8250-8299. Plug-ins: 5170-5199 en 9000-9099.
- **Data.** Alleen fictieve gegevens en test-BSN's uit de officiele testreeks
  (999990000 tot en met 999999999).
- **Testen.** Elk nieuw component krijgt in `stack.yaml` een health-URL en minstens één
  rooktest (`tests/checks/rook.py` als hij in meer stacks zit, anders
  `stacks/<naam>/tests.py`). Elk nieuw portaal of burger-API komt in `burgerkanalen` met
  een isolatietest.

## Images ophalen en bouwen

- **Docker Hub geeft 429.** `scripts/stack.sh pull <naam>` probeert bij een fout hetzelfde
  image via `mirror.gcr.io` en tagt het lokaal onder de originele naam. `up` doet dit
  automatisch voor ontbrekende images.
- **Proxy met TLS-inspectie.** Een image bouwen dat tijdens de build pakketten haalt
  (pnpm, pip, Gradle) faalt achter zo'n proxy. Dat is op te lossen met een lokaal
  basisimage met het extra CA-certificaat erin, onder dezelfde naam als het origineel,
  zodat de Dockerfile van het project ongewijzigd blijft. Voorbeeld voor Node:

  ```dockerfile
  FROM node:22-alpine
  COPY extra-ca.crt /usr/local/share/ca-certificates/extra-ca.crt
  RUN cat /usr/local/share/ca-certificates/extra-ca.crt >> /etc/ssl/certs/ca-certificates.crt
  ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/extra-ca.crt
  ```

  `docker build -t node:22-alpine .` in een map met het CA-bestand. Voor Python zet je
  daarnaast `PIP_CERT` en `REQUESTS_CA_BUNDLE`, voor Java importeer je het certificaat met
  `keytool` in de truststore. Op een normale machine is dit niet nodig.
- **Schijf.** Na `down` van een stack: `scripts/stack.sh opruimen` (ongebruikte images
  en build-cache).
