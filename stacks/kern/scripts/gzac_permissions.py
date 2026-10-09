"""Geeft ROLE_USER in GZAC dezelfde dossier- en taakrechten als ROLE_ADMIN (zonder beheerschermen).
Draait in de Playwright-container: logt in als beheerder om een token te krijgen."""
import os
from playwright.sync_api import sync_playwright
D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
G = f"https://gzac.{D}"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); tok = {}
    pg.on("request", lambda r: "/api/" in r.url and r.headers.get("authorization") and tok.setdefault("t", r.headers["authorization"]))
    pg.goto(G); pg.wait_for_timeout(3000)
    pg.fill("#username", "beheerder"); pg.fill("#password", PW); pg.click("#kc-login"); pg.wait_for_timeout(8000)
    H = {"Authorization": tok["t"], "Content-Type": "application/json"}
    admin = pg.request.get(f"{G}/api/management/v1/roles/ROLE_ADMIN/permissions", headers=H).json()
    user = pg.request.get(f"{G}/api/management/v1/roles/ROLE_USER/permissions", headers=H).json()
    if user:
        print("ROLE_USER heeft al rechten:", len(user))
    else:
        for perm in admin:
            perm.pop("role", None)
        r = pg.request.put(f"{G}/api/management/v1/roles/ROLE_USER/permissions", headers=H, data=__import__("json").dumps(admin))
        print("PUT", r.status, r.text()[:300])
    b.close()
