"""Maakt screenshots per ingang voor de welkomstpagina. Draait in de Playwright-container, zie screenshots.sh.

Schrijft JPEG's naar /out/<rol>-<n>.jpg. Maakt geen nieuwe zaken aan: het formulier wordt wel ingevuld, niet verstuurd.
"""
import os
from playwright.sync_api import sync_playwright

D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
OUT = "/out"
VIEW = {"width": 1280, "height": 800}


def shot(pg, name):
    pg.wait_for_timeout(800)
    pg.screenshot(path=f"{OUT}/{name}.jpg", type="jpeg", quality=72)
    print("ok", name)


def django_login(pg, host, next_path="/admin/"):
    """Inloggen in een beheerscherm via Keycloak (single sign-on) als 'demo'."""
    prefix = "/auth/oidc/authenticate/" if host == "formulieren" else "/oidc/authenticate/"
    pg.goto(f"https://{host}.{D}{prefix}?next={next_path}")
    pg.wait_for_timeout(2000)
    if pg.locator("#kc-login").count():
        pg.fill("#username", "demo"); pg.fill("#password", PW); pg.click("#kc-login")
    pg.wait_for_load_state("networkidle")


def kiss_login(pg, user="kcc"):
    pg.goto(f"https://kiss.{D}/")
    pg.wait_for_load_state("networkidle")
    pg.fill("#username", user)
    pg.fill("#password", PW)
    pg.click("#kc-login")
    pg.wait_for_load_state("networkidle")


def safe(fn):
    try:
        fn()
    except Exception as e:  # een mislukte screenshot mag de rest niet blokkeren
        print("FOUT", fn.__name__, str(e).splitlines()[0][:200])


with sync_playwright() as p:
    b = p.chromium.launch()

    def new():
        return b.new_page(viewport=VIEW, locale="nl-NL")

    def inwoner():
        pg = new()
        pg.goto(f"https://formulieren.{D}/melding-openbare-ruimte")
        pg.wait_for_load_state("networkidle")
        weiger = pg.get_by_role("button", name="Alles weigeren")
        if weiger.count():
            weiger.first.click()
        shot(pg, "inwoner-1")
        pg.get_by_text("DigiD").first.click(); pg.wait_for_timeout(3000)
        pg.fill("#username", "suzanne"); pg.fill("#password", PW); pg.click("#kc-login"); pg.wait_for_timeout(5000)
        start = pg.get_by_role("button", name="Melding starten")
        if start.count():
            start.first.click(); pg.wait_for_timeout(3000)
        kaart = pg.locator(".leaflet-container").first
        bb = kaart.bounding_box()
        if bb:
            kaart.click(position={"x": bb["width"] * 0.5, "y": bb["height"] * 0.55}); pg.wait_for_timeout(1000)
        sel = pg.get_by_label("Waar gaat uw melding over?")
        if sel.count():
            sel.first.click(); pg.wait_for_timeout(400)
            pg.get_by_text("Losliggende stoeptegel").first.click(); pg.keyboard.press("Escape")
        for label, val in [("Adres of omschrijving van de plek", "Dorpsstraat 12, Demostad"),
                           ("Wat is er aan de hand?", "De stoeptegel voor nummer 12 steekt 3 cm uit."),
                           ("Uw achternaam", "Moulin"), ("Uw e-mailadres", "s.moulin@example.com")]:
            loc = pg.get_by_label(label, exact=True)
            if loc.count():
                loc.first.fill(val)
        pg.evaluate("window.scrollTo(0, 200)")
        shot(pg, "inwoner-2")
        pg.close()

    def kcc():
        pg = new()
        kiss_login(pg)
        pg.wait_for_timeout(1500)
        shot(pg, "kcc-1")
        pg.get_by_role("button", name="Nieuw contactmoment").click()
        pg.wait_for_timeout(1000)
        pg.get_by_label("Bsn").fill("999993653")
        pg.get_by_role("button", name="Zoeken").last.click()
        pg.wait_for_timeout(4000)
        shot(pg, "kcc-2")
        pg.get_by_role("tab", name="Zaken").click()
        pg.wait_for_timeout(2500)
        pg.locator("a[title^='Details ZAAK']").first.click()
        pg.wait_for_timeout(3000)
        shot(pg, "kcc-3")
        pg.close()

    def behandelaar_zac():
        pg = new()
        pg.goto(f"https://zac.{D}/")
        pg.wait_for_timeout(3000)
        pg.fill("#username", "behandelaar"); pg.fill("#password", PW); pg.click("#kc-login")
        pg.wait_for_timeout(6000)
        pg.goto(f"https://zac.{D}/zaken/werkvoorraad"); pg.wait_for_timeout(5000)
        shot(pg, "behandelaar-zac")
        pg.goto(f"https://zac.{D}/zaken/ZAAK-2026-0000000001"); pg.wait_for_timeout(6000)
        shot(pg, "behandelaar-zac-2")
        pg.close()

    def behandelaar():
        pg = new()
        pg.goto(f"https://gzac.{D}/")
        pg.wait_for_timeout(3000)
        pg.fill("#username", "behandelaar"); pg.fill("#password", PW); pg.click("#kc-login")
        pg.wait_for_timeout(8000)
        shot(pg, "behandelaar-1")
        pg.get_by_text("Dossiers").first.click()
        pg.wait_for_timeout(1500)
        pg.locator("[class*=side-nav] >> text=Evenementenvergunnin").first.click()
        pg.wait_for_timeout(5000)
        shot(pg, "behandelaar-2")
        rows = pg.locator("table tbody tr")
        if rows.count():
            rows.first.click()
            pg.wait_for_timeout(6000)
            shot(pg, "behandelaar-3")
        pg.close()
        pg = new()
        django_login(pg, "zaken", "/admin/zaken/zaak/")
        pg.goto(f"https://zaken.{D}/admin/zaken/zaak/")
        shot(pg, "behandelaar-oz")
        pg.close()

    def beheer():
        pg = new()
        django_login(pg, "formulieren", "/admin/forms/form/")
        pg.goto(f"https://formulieren.{D}/admin/forms/form/")
        shot(pg, "beheer-1")
        pg.get_by_role("link", name="Melding openbare ruimte").first.click()
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(2500)
        tab = pg.get_by_role("tab", name="Stappen en velden")
        if tab.count():
            tab.first.click()
            pg.wait_for_timeout(2500)
        shot(pg, "beheer-2")
        pg2 = new()
        django_login(pg2, "zaken", "/admin/catalogi/zaaktype/")
        pg2.goto(f"https://zaken.{D}/admin/catalogi/zaaktype/")
        shot(pg2, "beheer-3")
        for host, path, name in [("klant", "/admin/klantinteracties/klantcontact/", "beheer-openklant"),
                                 ("objecten", "/admin/core/object/", "beheer-objecten"),
                                 ("objecttypen", "/admin/core/objecttype/", "beheer-objecttypen")]:
            pg3 = new()
            django_login(pg3, host, path)
            pg3.goto(f"https://{host}.{D}{path}")
            shot(pg3, name)
            pg3.close()
        pg.close(); pg2.close()

    def ontwikkelaar():
        pg = new()
        pg.goto(f"https://zaken.{D}/zaken/api/v1/schema/")
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(3000)
        shot(pg, "ontwikkelaar-1")
        pg.goto(f"https://klant.{D}/klantinteracties/api/v1/schema/")
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(3000)
        shot(pg, "ontwikkelaar-2")
        pg.goto(f"https://zaken.{D}/catalogi/api/v1/schema/")
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(3000)
        shot(pg, "ontwikkelaar-catalogi")
        pg3 = new()
        django_login(pg3, "notificaties", "/admin/datamodel/notificatie/")
        pg3.goto(f"https://notificaties.{D}/admin/datamodel/notificatie/")
        shot(pg3, "ontwikkelaar-notificaties")
        pg3.close()
        ctx = b.new_context(viewport=VIEW, http_credentials={"username": "admin", "password": PW})
        pg2 = ctx.new_page()
        pg2.goto(f"https://mail.{D}/")
        pg2.wait_for_load_state("networkidle")
        first = pg2.locator(".message, a[href*='/view/']").first
        if first.count():
            first.click()
            pg2.wait_for_timeout(1500)
        shot(pg2, "ontwikkelaar-mailpit")
        ctx.close()
        pg.close()

    def digid(pg):
        if pg.locator("#kc-login").count():
            pg.fill("#username", "suzanne"); pg.fill("#password", PW); pg.click("#kc-login"); pg.wait_for_timeout(6000)

    def portalen():
        # Open Inwoner: eerste keer na inloggen een registratiescherm (alleen e-mail invullen)
        pg = new()
        pg.goto(f"https://inwoner.{D}/digid-oidc/authenticate/?next=/"); pg.wait_for_timeout(2500); digid(pg)
        if "register/necessary" in pg.url:
            if not pg.locator("[name=email]").input_value():
                pg.fill("[name=email]", "suzanne@example.com")
            pg.get_by_role("button", name="Voltooi registratie").click(); pg.wait_for_timeout(4000)
        for t in ("Alles weigeren", "Weigeren"):
            if pg.get_by_role("button", name=t).count():
                pg.get_by_role("button", name=t).first.click(); break
        pg.goto(f"https://inwoner.{D}/cases/"); pg.wait_for_timeout(5000)
        shot(pg, "inwoner-oip")
        pg.close()
        pg = new()
        pg.goto(f"https://portaal.{D}/"); pg.wait_for_timeout(3000); digid(pg); pg.wait_for_timeout(3000)
        shot(pg, "inwoner-nlportal")
        pg.close()
        pg = new()
        pg.goto(f"https://mijnoverheid.{D}/"); pg.wait_for_timeout(2500); digid(pg)
        shot(pg, "inwoner-mo")
        pg.goto(f"https://mijnoverheid.{D}/#/zaken"); pg.wait_for_timeout(3000)
        pg.get_by_text("Melding openbare ruimte").first.click(); pg.wait_for_timeout(4000)
        shot(pg, "inwoner-mo-2")
        pg.close()

    def iko():
        pg = new()
        pg.goto(f"https://iko.{D}/admin"); pg.wait_for_timeout(2500)
        if pg.locator("#kc-login").count():
            pg.fill("#username", "demo"); pg.fill("#password", PW); pg.click("#kc-login"); pg.wait_for_timeout(4000)
        pg.goto(f"https://iko.{D}/admin/connectors"); pg.wait_for_timeout(2500)
        shot(pg, "beheer-iko")
        pg.close()

    alle = (inwoner, portalen, kcc, behandelaar_zac, behandelaar, beheer, iko, ontwikkelaar)
    alleen = set(filter(None, os.environ.get("ALLEEN", "").split(",")))
    for fn in alle:
        if not alleen or fn.__name__ in alleen:
            safe(fn)
    b.close()
