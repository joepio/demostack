"""Zaaktypen voor GZAC klaarzetten, voordat GZAC start (init-container gzac-zaaktypen).

GZAC koppelt een case-definitie aan een zaaktype in Open Zaak, en de proceskoppelingen
naar de Zaken API verwijzen naar roltypen en statustypen. Die verwijzingen zijn URL's.
Een definitieve case-definitie kan na het deployen niet meer veranderen (in een
productieprofiel kent Valtimo geen drafts), dus de URL's moeten bij de eerste start
kloppen. Daarom:

1. maakt dit script de catalogus, de informatieobjecttypen en de zaaktypen aan met de
   functies van de gedeelde seed (seed/seed.py, idempotent; de seed slaat ze later over);
2. schrijft het de URL's als eigenschappen naar /gzac-runtime/zaaktypen.properties.
   GZAC leest dat bestand (SPRING_CONFIG_IMPORT) en vult ${GZAC_...} in de
   case-bestanden in (config/gzac/config/case/parkeervergunning/).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "seed"))

import seed  # noqa: E402

UIT = Path("/gzac-runtime/zaaktypen.properties")


def main():
    catalogus = seed.zorg_voor_catalogus()
    iots = seed.zorg_voor_informatieobjecttypen(catalogus)
    zaaktypen = seed.zorg_voor_zaaktypen(catalogus, iots)
    zt = zaaktypen["parkeervergunning"]
    statustypen = {s["omschrijving"]: s["url"] for s in seed.oz.lijst(f"{seed.CAT}/statustypen", zaaktype=zt["url"])}
    roltypen = {r["omschrijvingGeneriek"]: r["url"] for r in seed.oz.lijst(f"{seed.CAT}/roltypen", zaaktype=zt["url"])}
    eigenschappen = {
        "GZAC_PARKEERVERGUNNING_ZAAKTYPE": zt["url"],
        "GZAC_PARKEERVERGUNNING_ROLTYPE_INITIATOR": roltypen["initiator"],
        "GZAC_PARKEERVERGUNNING_STATUSTYPE_ONTVANGEN": statustypen["Ontvangen"],
        "GZAC_PARKEERVERGUNNING_STATUSTYPE_IN_BEHANDELING": statustypen["In behandeling"],
        "GZAC_PARKEERVERGUNNING_STATUSTYPE_AFGEHANDELD": statustypen["Afgehandeld"],
    }
    UIT.write_text("".join(f"{k}={v}\n" for k, v in eigenschappen.items()))
    for k, v in eigenschappen.items():
        print(f"{k}={v}", flush=True)


if __name__ == "__main__":
    main()
