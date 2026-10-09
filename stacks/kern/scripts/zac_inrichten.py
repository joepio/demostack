"""Richt in ZAC de zaakafhandelparameters in voor zaaktype MOR (idempotent). Draait in de Playwright-container."""
import os, json
from playwright.sync_api import sync_playwright
D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
Z = f"https://zac.{D}"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(Z); pg.wait_for_timeout(3000)
    pg.fill("#username", "beheerder"); pg.fill("#password", PW); pg.click("#kc-login"); pg.wait_for_timeout(6000)
    r = pg.request
    configs = r.get(f"{Z}/rest/zaakafhandelparameters").json()
    for conf in configs:
        if conf["zaaktype"]["identificatie"] != "MOR" or not conf["zaaktype"].get("nuGeldig"):
            continue
        if conf.get("valide"):
            print("MOR is al ingericht in ZAC"); continue
        zt = conf["zaaktype"]["uuid"]
        conf = r.get(f"{Z}/rest/zaakafhandelparameters/{zt}").json()
        cd = r.get(f"{Z}/rest/zaakafhandelparameters/case-definitions/generiek-zaakafhandelmodel").json()
        resultaten = r.get(f"{Z}/rest/zaakafhandelparameters/resultaattypes/{zt}").json()
        conf["caseDefinition"] = cd
        conf["defaultGroepId"] = "team-meldingen"
        conf["zaakNietOntvankelijkResultaattype"] = next(x for x in resultaten if x["naam"] == "Niet ontvankelijk")
        conf["einddatumGeplandWaarschuwing"] = 3
        conf["uiterlijkeEinddatumAfdoeningWaarschuwing"] = 3
        conf["humanTaskParameters"] = [{"actief": True, "planItemDefinition": h, "doorlooptijd": 5,
                                        "defaultGroepId": "team-meldingen", "formulierDefinitieId": h["defaultFormulierDefinitie"],
                                        "referentieTabellen": []} for h in cd["humanTaskDefinitions"]]
        conf["userEventListenerParameters"] = [{"id": u["id"], "naam": u["naam"], "toelichting": ""}
                                               for u in cd["userEventListenerDefinitions"]]
        res = r.put(f"{Z}/rest/zaakafhandelparameters", data=json.dumps(conf), headers={"Content-Type": "application/json"})
        print("PUT", res.status, res.text()[:300] if res.status >= 400 else "")
        print("valide:", r.get(f"{Z}/rest/zaakafhandelparameters/{zt}").json().get("valide"))
    b.close()
