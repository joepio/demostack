"""Inrichting van IKO voor Gemeente Voorbeeldstad (stack g4), zonder klikken in de beheer-UI.

IKO bewaart connectoren, instanties en profielen in zijn database; de configuratiewaarden
van een instantie (host, secrets) staan daar versleuteld met AES-GCM onder IKO_CRYPTO_KEY.
Dit script schrijft een herhaalbare Flyway-migratie (R__voorbeeldstad.sql) naar /iko-seed.
IKO draait die bij het starten na zijn eigen migraties (SPRING_FLYWAY_LOCATIONS met
filesystem:/iko-seed), net zoals de e2e-seed van IKO zelf (e2e/seed/).

Wat er komt:
- connector "openzaak" (Camel-route uit doc/connectors/openzaak.md van IKO 1.5.1) met de
  endpoints zaak_list en zaak_read
- instantie "voorbeeldstad" naar http://openzaak.local:8000 met de ZGW-client "iko"
- profiel "zaken-van-burger": GET /aggregated-data-profiles/zaken-van-burger?id=<bsn>
  geeft de zaken waarin die burger een rol heeft; rol ROLE_KLANTBEELD vereist

De versleuteling gebruikt een IV die afhangt van sleutel en waarde: dezelfde invoer geeft
dezelfde SQL, zodat Flyway de migratie alleen opnieuw draait als er echt iets verandert.
"""
import base64
import hashlib
import hmac
import os
import pathlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

UIT = pathlib.Path(os.environ.get("IKO_SEED_DIR", "/iko-seed"))

CONNECTOR_ID = "1c0a0000-0000-4000-8000-000000000001"
INSTANTIE_ID = "1c0a0000-0000-4000-8000-000000000002"
EP_LIST_ID = "1c0a0000-0000-4000-8000-000000000003"
EP_READ_ID = "1c0a0000-0000-4000-8000-000000000004"
ROL_LIST_ID = "1c0a0000-0000-4000-8000-000000000005"
ROL_READ_ID = "1c0a0000-0000-4000-8000-000000000006"
PROFIEL_ID = "1c0a0000-0000-4000-8000-000000000007"
ROL = "ROLE_KLANTBEELD"

ZAAK_LIST_FILTER = (
    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn|zaaktype|identificatie|"
    "bronorganisatie|startdatum|startdatum__gte|startdatum__lte|einddatum__isnull|ordering|page|expand")

CONNECTOR_CODE = f"""- route:
    id: "direct:iko:endpoint:transform:openzaak.zaak_list"
    errorHandler:
        noErrorHandler: {{}}
    from:
        uri: "direct:iko:endpoint:transform:openzaak.zaak_list"
        steps:
            - removeHeaders:
                pattern: "*"
                excludePattern: "{ZAAK_LIST_FILTER}"
            - setHeader:
                name: "Accept-Crs"
                constant: "EPSG:4326"
- route:
    id: "direct:iko:endpoint:transform:openzaak.zaak_read"
    errorHandler:
        noErrorHandler: {{}}
    from:
        uri: "direct:iko:endpoint:transform:openzaak.zaak_read"
        steps:
            - choice:
                when:
                    - simple: "${{header.uuid}} == null"
                      steps:
                          - setHeader:
                              name: "uuid"
                              jq:
                                  expression: ".idParam // header(\\"id\\") // empty"
                                  source: "variable:endpointTransformContext"
            - removeHeaders:
                pattern: "*"
                excludePattern: "expand|uuid"
            - setHeader:
                name: "Accept-Crs"
                constant: "EPSG:4326"
- route:
    id: "direct:iko:connector:openzaak"
    errorHandler:
        noErrorHandler: {{}}
    from:
        uri: "direct:iko:connector:openzaak"
        steps:
            - setHeader:
                name: "Accept"
                constant: "application/json"
            - script:
                groovy: |-
                    def signingKey = io.jsonwebtoken.security.Keys.hmacShaKeyFor(variable.configProperties.clientSecret.getBytes());
                    def jwt = io.jsonwebtoken.Jwts.builder()
                          .issuer(variable.configProperties.clientId)
                          .issuedAt(new Date())
                          .claim("client_id", variable.configProperties.clientId)
                          .signWith(signingKey, io.jsonwebtoken.SignatureAlgorithm.HS256)
                          .compact();
                    exchange.in.setHeader("Authorization", "Bearer ${{jwt}}");
            - toD:
                uri: "language:groovy:\\"rest-openapi:${{variable.configProperties.apiSpecificationUrl}}#${{variable.operation}}?host=${{variable.configProperties.host}}\\""
            - unmarshal:
                json: {{}}
"""

# Endpoint-transform: het id uit de aanroep (?id=<bsn>) wordt het rolfilter van Open Zaak
ENDPOINT_TRANSFORM = '{"rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": .idParam, "ordering": "-startdatum"}'
# Resultaat: alleen wat een medewerker in een klantbeeld nodig heeft
RESULT_TRANSFORM = ('{aantal: .count, zaken: [.results[] | {identificatie, omschrijving, zaaktype, startdatum, '
                    'einddatum, status, vertrouwelijkheidaanduiding}]}')


def versleutel(sleutel: bytes, waarde: str) -> str:
    iv = hmac.new(sleutel, waarde.encode(), hashlib.sha256).digest()[:12]
    return base64.b64encode(iv + AESGCM(sleutel).encrypt(iv, waarde.encode(), None)).decode()


def sql(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main():
    sleutel = base64.b64decode(os.environ["IKO_CRYPTO_KEY"])
    config = {
        "host": "http://openzaak.local:8000",
        "clientId": "iko",
        "clientSecret": os.environ["ZGW_IKO_SECRET"],
        "apiSpecificationUrl": "http://openzaak.local:8000/zaken/api/v1/schema/openapi.yaml",
    }
    regels = [
        "-- Gegenereerd door config/iko/inrichting.py (stack g4). Niet met de hand wijzigen.",
        f"""INSERT INTO connector (id, name, tag, version, is_active, status, connector_code)
VALUES ('{CONNECTOR_ID}', 'Open Zaak', 'openzaak', '1.0.0', TRUE, 'FINAL', {sql(CONNECTOR_CODE)})
ON CONFLICT (id) DO UPDATE SET connector_code = EXCLUDED.connector_code;""",
        f"""INSERT INTO connector_instance (id, name, connector_id, tag, api_specification_url)
VALUES ('{INSTANTIE_ID}', 'Open Zaak Voorbeeldstad', '{CONNECTOR_ID}', 'voorbeeldstad', NULL)
ON CONFLICT (id) DO NOTHING;""",
        f"DELETE FROM connector_instance_config WHERE connector_instance_id = '{INSTANTIE_ID}';",
    ]
    for k, v in config.items():
        regels.append(f"INSERT INTO connector_instance_config (connector_instance_id, key, value) "
                      f"VALUES ('{INSTANTIE_ID}', {sql(k)}, {sql(versleutel(sleutel, v))});")
    regels += [
        f"""INSERT INTO connector_endpoint (id, name, connector_id, operation) VALUES
    ('{EP_LIST_ID}', 'zaak_list', '{CONNECTOR_ID}', 'zaak_list'),
    ('{EP_READ_ID}', 'zaak_read', '{CONNECTOR_ID}', 'zaak_read')
ON CONFLICT (id) DO NOTHING;""",
        f"""INSERT INTO connector_endpoint_role (id, connector_endpoint_id, connector_instance_id, role) VALUES
    ('{ROL_LIST_ID}', '{EP_LIST_ID}', '{INSTANTIE_ID}', '{ROL}'),
    ('{ROL_READ_ID}', '{EP_READ_ID}', '{INSTANTIE_ID}', '{ROL}')
ON CONFLICT (id) DO NOTHING;""",
        f"""INSERT INTO aggregated_data_profile (
    id, name, version, is_active, status, connector_instance_id, connector_endpoint_id,
    endpoint_transform, transform, roles, cache_enabled, cache_ttl)
VALUES ('{PROFIEL_ID}', 'zaken-van-burger', '1.0.0', TRUE, 'FINAL', '{INSTANTIE_ID}', '{EP_LIST_ID}',
    {sql(ENDPOINT_TRANSFORM)}, {sql(RESULT_TRANSFORM)}, '{ROL}', FALSE, 0)
ON CONFLICT (id) DO UPDATE SET endpoint_transform = EXCLUDED.endpoint_transform,
    transform = EXCLUDED.transform, roles = EXCLUDED.roles;""",
    ]
    UIT.mkdir(parents=True, exist_ok=True)
    (UIT / "R__voorbeeldstad.sql").write_text("\n\n".join(regels) + "\n")
    print(f"IKO-inrichting geschreven: {UIT / 'R__voorbeeldstad.sql'}")


if __name__ == "__main__":
    main()
