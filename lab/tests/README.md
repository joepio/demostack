# Gedeelde testsuite

Elke stack draait dezelfde suite:

```bash
scripts/stack.sh test <naam>                        # alles
scripts/stack.sh test <naam> --alleen zgw,mijn-apis     # een deel
```

Uitvoer:

Met plug-ins (`scripts/stack.sh up <naam> --plugin <map>`) heet het rapport
`<naam>+<plug-in>`, zodat een run met een product van een leverancier het rapport zonder
plug-ins niet overschrijft.

- `results/<naam>.json`: machineleesbaar, per check `id`, `categorie`, `component`,
  `naam`, `status` (`pass`, `fail` of `skip`), `detail` of `reden`, en bij een bekende
  fout `bekend` met uitleg. Bovenaan `samenvatting` en `per_categorie` met de tellingen
  (`fail_bekend`, `fail_onverwacht`), onder `plugins` de plug-ins (naam, leverancier,
  versie) en onder `omgeving` het image per service.
- `results/<naam>.md`: dezelfde inhoud als tabellen.
- `results/raw/<naam>/`: ruwe uitvoer (compose ps, Respect-JSON en logs). Niet in git,
  want de Respect-uitvoer bevat tokens.

De exitcode is 1 als er een fout is die niet onder `bekende_fouten` in `stack.yaml`
staat. Een skip heeft altijd een reden.

## Categorieen

| Categorie | Wat | Bron | Check-id's |
|---|---|---|---|
| gezondheid | draaien de services van elk component (healthy als er een healthcheck is), en geeft de health-URL de verwachte status | `checks/gezondheid.py`, `componenten` en `gepland` in `stack.yaml` | `gezondheid/<component>` |
| rook | per component echte API-aanroepen op de geseede data | `checks/rook.py`, `stacks/<naam>/tests.py` | `rook/<component>/<check>` |
| zgw | ZGW-aansluitprofiel (Arazzo, VNG API Lab) rechtstreeks op Open Zaak, met het applicatietoken van `burgerportaal` | `checks/zgw.py`, sectie `zgw` | `zgw/gedrag/<workflow>`, `zgw/strikt/<workflow>` |
| burger-isolatie | kan burger A bij een portaal of burger-API gegevens van burger B zien (lijst, zoeken op BSN van B, detail, document, zonder token) | `checks/isolatie.py`, sectie `burgerkanalen` van de stack en van plug-ins | `burger-isolatie/<kanaal>/<check>` |
| mijn-apis | per Mijn-API van een plug-in: inloggen als testburger, MijnZaken next en MijnTaken next (Arazzo, VNG API Lab, `vendor/vng-api-lab`), controles op de geseede data; zonder plug-in overgeslagen | `checks/mijn_apis.py`, sectie `mijn_apis` in `plugin.yaml` | `mijn-apis/<id>/login`, `mijn-apis/<id>/mijnzaken/<workflow>`, `mijn-apis/<id>/mijntaken/<workflow>`, `mijn-apis/<id>/data/<check>` |

Testburgers (uit `stacks/basis/stack.yaml`): A = 999990627, B = 999997609,
C = 999993409. De seed geeft hen zaken, documenten, klantcontacten en objecten.

## Hoe het draait

1. `scripts/stack.sh` schrijft `docker compose ps` naar `results/raw/<naam>/ps.json`.
2. `tests/run.py` (in de tools-container, binnen het docker-netwerk) voert de
   Python-checks uit en plant de Arazzo-runs (`respect-jobs.json`).
3. `tests/respect/run.mjs` (in de respect-container, `node:22.22.0-alpine`) voert de runs
   uit met Redocly CLI 2.57.0 uit `tests/respect/node_modules`. Die installeert
   `stack.sh` eenmalig met `npm ci` op de host; de container heeft geen internet nodig.
4. `tests/rapport.py` voegt alles samen, past `bekende_fouten` toe en schrijft het rapport.

## Uitbreiden

- **Rooktest voor een component** dat in meer stacks zit: in `checks/rook.py`.
  Stack-specifiek: in `stacks/<naam>/tests.py`:

  ```python
  from checks.rook import rook
  from kader import eis

  @rook("openformulieren", "formulieren opvragen", vereist=("openzaak",))
  def _(ctx):
      ...
      eis(voorwaarde, "melding")
      return "detail"
  ```

  Een component zonder rooktest geeft `rook/<component>: overgeslagen, nog geen rooktest`.
- **Isolatietest voor een nieuw soort portaal:** een functie met
  `@isolatietype("openinwoner")` in `checks/isolatie.py` (of in `stacks/<naam>/tests.py`)
  die met `ctx.voer_uit(...)` per controle een check vastlegt. Laat burger A inloggen
  (DigiD-simulatie in Keycloak, gebruikersnaam is het BSN, wachtwoord
  `DIGID_SIM_WACHTWOORD`) en probeer de zaken, taken, documenten en berichten van burger B
  te zien. Leg eerst vast dat B zelf data heeft, anders bewijst de test niets.
- **Overslaan:** `raise Overslaan("reden")` in een check.
- **Plug-in:** componenten, burgerkanalen en Mijn-API's in `plugin.yaml`, extra rooktests
  en isolatietypes in `tests.py` van de plug-in. Zie [`docs/PLUGINS.md`](../docs/PLUGINS.md).
