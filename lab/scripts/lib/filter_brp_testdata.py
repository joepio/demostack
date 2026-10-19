"""Filtert de RvIG-testpersonen (Haal Centraal BRP personen-mock) zodat alleen
BSN's in de officiele testreeks 999990000-999999999 overblijven die de
elfproef halen. BSN's van gerelateerde personen buiten die reeks worden
verwijderd.

Bron: https://github.com/BRP-API/Haal-Centraal-BRP-bevragen
      test-data/personen-mock/test-data.json (EUPL-1.2, RvIG)

Gebruik: python3 filter_brp_testdata.py <invoer.json> <uitvoer.json>
"""
import json
import sys


def elfproef(bsn: str) -> bool:
    bsn = str(bsn)
    if len(bsn) != 9 or not bsn.isdigit():
        return False
    gewichten = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    return sum(int(c) * w for c, w in zip(bsn, gewichten)) % 11 == 0


def is_test_bsn(bsn) -> bool:
    return str(bsn).startswith("99999") and elfproef(bsn)


def schoon(obj):
    if isinstance(obj, dict):
        uit = {}
        for k, v in obj.items():
            if k == "burgerservicenummer" and not is_test_bsn(v):
                continue
            uit[k] = schoon(v)
        return uit
    if isinstance(obj, list):
        return [schoon(x) for x in obj]
    return obj


def main(invoer, uitvoer):
    personen = json.load(open(invoer, encoding="utf-8"))
    gefilterd = [schoon(p) for p in personen if is_test_bsn(p.get("burgerservicenummer", ""))]
    with open(uitvoer, "w", encoding="utf-8") as f:
        json.dump(gefilterd, f, ensure_ascii=False, indent=1)
    print(f"{len(gefilterd)} van {len(personen)} personen behouden")


if __name__ == "__main__":
    main(*sys.argv[1:3])
