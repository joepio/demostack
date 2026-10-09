"""Rooktest: log in op KISS als testmedewerker via Keycloak en roep een paar BFF-endpoints aan."""
import os, re, html, sys, requests
D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
K = f"https://kiss.{D}"
s = requests.Session()
r = s.get(f"{K}/api/challenge", allow_redirects=True)
m = re.search(r'<form[^>]+action="([^"]+)"', r.text)
if not m: print("geen loginformulier", r.status_code, r.url); sys.exit(1)
r = s.post(html.unescape(m.group(1)), data={"username": os.environ.get("KISS_USER", "kcc"), "password": PW}, allow_redirects=True)
while "Form_Post" in r.text or "form_post" in r.text.lower() and "signin-oidc" in r.text:
    action = html.unescape(re.search(r'ACTION="([^"]+)"', r.text, re.I).group(1))
    fields = dict(re.findall(r'NAME="([^"]+)" VALUE="([^"]*)"', r.text, re.I))
    r = s.post(action, data={k: html.unescape(v) for k, v in fields.items()}, allow_redirects=True)
if 'id="kc-form-login"' in r.text or "kc-feedback" in r.text:
    print("login mislukt:", re.findall(r'kc-feedback-text">([^<]+)', r.text) or r.text[:500]); sys.exit(1)
print("na login:", r.status_code, r.url)
me = s.get(f"{K}/api/me").json(); print("me:", me)
for path in ["/api/elasticsearch/search-smoelenboek/_search", ]:
    rr = s.post(K + path, json={"query": {"match_all": {}}}, headers={"Content-Type": "application/json"})
    print(path, rr.status_code, rr.text[:200])
import json as _j
body = _j.dumps({"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": ["999993653"], "fields": ["naam"]}, separators=(",", ":"))
rr = s.post(f"{K}/api/haalcentraal/brp/personen", data=body, headers={"Content-Type": "application/json"})
print("brp", rr.status_code, rr.text[:300])
rr = s.get(f"{K}/api/zaken/zaken/api/v1/zaken", params={"identificatie": "OF-JD5JWK"})
print("zaken", rr.status_code, rr.text[:300])
