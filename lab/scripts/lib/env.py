"""Leest .env (KEY=waarde, zonder shell-quoting) en print een variabele, of een ZGW-JWT.

Gebruik:
  python3 scripts/lib/env.py get NAAM
  python3 scripts/lib/env.py zgw-jwt CLIENT_ID_VAR SECRET_VAR
"""
import base64, hashlib, hmac, json, sys, time
from pathlib import Path

ENV = Path(__file__).resolve().parents[2] / ".env"


def lees():
    waarden = {}
    for regel in ENV.read_text().splitlines():
        regel = regel.strip()
        if not regel or regel.startswith("#") or "=" not in regel:
            continue
        k, v = regel.split("=", 1)
        waarden[k.strip()] = v.strip().strip('"').strip("'")
    return waarden


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def zgw_jwt(client_id, secret):
    kop = {"alg": "HS256", "typ": "JWT"}
    nu = int(time.time())
    claims = {"iss": client_id, "iat": nu, "client_id": client_id,
              "user_id": client_id, "user_representation": client_id}
    deel = b64(json.dumps(kop).encode()) + "." + b64(json.dumps(claims).encode())
    sig = hmac.new(secret.encode(), deel.encode(), hashlib.sha256).digest()
    return deel + "." + b64(sig)


if __name__ == "__main__":
    w = lees()
    if sys.argv[1] == "get":
        print(w[sys.argv[2]])
    elif sys.argv[1] == "zgw-jwt":
        print(zgw_jwt(w[sys.argv[2]], w[sys.argv[3]]))
