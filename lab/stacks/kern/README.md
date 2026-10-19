# Stack kern: MijnServices-kern (variant 1)

De registers die elke andere stack ook gebruikt. Dit was "variant 1"
(`compose/v1-mijnservices.yml`). De kern heeft zelf geen portaal: een portaal of Mijn-API
komt erbij als plug-in (`scripts/stack.sh up kern --plugin <map>`, zie
[`docs/PLUGINS.md`](../../docs/PLUGINS.md)).

```bash
scripts/stack.sh up kern
scripts/stack.sh test kern
scripts/stack.sh down kern
```

| Component | Image (standaard) | Variabele | Host-poort | Intern adres |
|---|---|---|---|---|
| Open Zaak | `openzaak/open-zaak:1.29.0` | `IMAGE_OPENZAAK` | 8001 | `http://openzaak.local:8000` |
| Open Notificaties | `openzaak/open-notificaties:1.16.1` | `IMAGE_OPENNOTIFICATIES` | 8002 | `http://opennotificaties.local:8000` |
| Open Object | `maykinmedia/open-object:4.1.0` | `IMAGE_OPENOBJECT` | 8003 | `http://openobject.local:8000` |
| Open Klant | `maykinmedia/open-klant:2.17.0` | `IMAGE_OPENKLANT` | 8004 | `http://openklant.local:8000` |
| Open Product | `maykinmedia/open-product:1.8.0` | `IMAGE_OPENPRODUCT` | 8005 | `http://openproduct.local:8000` |
| Referentielijsten | `maykinmedia/referentielijsten-api:0.7.3` | `IMAGE_REFERENTIELIJSTEN` | 8006 | `http://referentielijsten.local:8000` |
| VNG Selectielijst | `openzaak/vng-selectielijst:1.0.5` | `IMAGE_SELECTIELIJST` | 8007 | `http://selectielijst.local:8000` |

De infra (Postgres, Redis, Keycloak, BRP-mock, notificatie-sink) komt uit
`stacks/basis/compose.yml`. Koppelingen, clients en testdata: zie de README in de root.

## Testresultaat

Zie `results/kern.md` (laatste run) en `results/kern.json`. Bekende fouten staan in
`stack.yaml` onder `bekende_fouten`:

- `zgw/gedrag/burger-a-*`: ZGW autoriseert per applicatie, niet per burger. Een portaal
  of Mijn-API op ZGW moet de burger dus zelf controleren (zie
  [`docs/openzaak-bevindingen.md`](../../docs/openzaak-bevindingen.md), D4).
- `zgw/strikt/*`: Open Zaak 1.29 wijkt op schema en content-type af van het profiel.

Zonder plug-in zijn `burger-isolatie` (geen burgerkanalen) en `mijn-apis` (geen Mijn-API)
overgeslagen, met die reden in het rapport.
