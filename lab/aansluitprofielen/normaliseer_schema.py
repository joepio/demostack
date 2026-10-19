"""Maakt het door Open Zaak geserveerde OpenAPI-schema bruikbaar voor Redocly Respect (Ajv).

drf-spectacular zet `nullable: true` naast `allOf`/`oneOf` zonder `type`. Ajv weigert dat
("nullable" cannot be used without "type"). Dit script herschrijft die knopen:
- `{allOf: [X], nullable: true}` wordt `{anyOf: [X, null]}` (null als `enum: [null]`), want
  met alleen `type: object` erbij keurt de allOf-verwijzing een null-waarde alsnog af;
- `{oneOf: [...], nullable: true}` (enum-varianten) krijgt `type: string`.
Daarnaast eist Ajv bij een `discriminator` dat elke variant de discriminator-eigenschap
als const/enum heeft. drf-spectacular zet die alleen in de basis (`allOf`). Bij een
discriminator met mapping krijgt elke variant daarom `properties.<naam>: {enum: [sleutel]}`;
de discriminator van GeoJSONGeometry (zonder mapping) vervalt, de `oneOf` blijft.
Tot slot wordt een `$ref` naar een extern schema (alleen `_expand.zaaktype`, naar de
Catalogi API op GitHub) `type: object`: de testsuite draait Respect in een container
zonder internet, en `_expand` speelt in het profiel geen rol.
Verder blijft het schema gelijk.

Gebruik: python3 normaliseer_schema.py <in.yaml> <uit.yaml>
"""
import sys

import yaml

schema = yaml.safe_load(open(sys.argv[1]))
aantal = 0


def loop(knoop):
    global aantal
    if isinstance(knoop, dict):
        ref = knoop.get("$ref")
        if isinstance(ref, str) and ref.startswith("http"):
            knoop.pop("$ref")
            knoop["type"] = "object"
            aantal += 1
        if knoop.get("nullable") and "type" not in knoop:
            if "allOf" in knoop and len(knoop["allOf"]) == 1:
                knoop["anyOf"] = [knoop.pop("allOf")[0], {"type": "string", "nullable": True, "enum": [None]}]
                knoop.pop("nullable")
                aantal += 1
            elif "oneOf" in knoop:
                knoop["type"] = "string"
                aantal += 1
        for v in knoop.values():
            loop(v)
    elif isinstance(knoop, list):
        for v in knoop:
            loop(v)


loop(schema)
schemas = schema.get("components", {}).get("schemas", {})
if schemas.get("GeoJSONGeometry", {}).pop("discriminator", None) is not None:
    aantal += 1
for basis in schemas.values():
    disc = basis.get("discriminator") if isinstance(basis, dict) else None
    if not disc or not disc.get("mapping"):
        continue
    naam = disc["propertyName"]
    for sleutel, ref in disc["mapping"].items():
        variant = schemas[ref.split("/")[-1]]
        variant.setdefault("properties", {})[naam] = {"type": "string", "enum": [sleutel]}
        if naam not in variant.setdefault("required", []):
            variant["required"].append(naam)
        aantal += 1
with open(sys.argv[2], "w") as f:
    f.write("# GEGENEREERD door normaliseer_schema.py uit %s; niet met de hand wijzigen.\n" % sys.argv[1].split("/")[-1])
    yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True, width=120)
print(f"{aantal} knopen aangepast", file=sys.stderr)
