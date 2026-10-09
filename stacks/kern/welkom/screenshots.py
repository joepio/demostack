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
    pg.goto(f"https://{host}.{D}/admin/login/?next={next_path}")
    pg.fill("input[name=auth-username]", "admin")
    pg.fill("input[name=auth-password]", PW)
    pg.press("input[name=auth-password]", "Enter")
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
        pg.locator("button[type=submit], .openforms-button--primary").first.click()
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(1500)
        sel = pg.get_by_label("Waar gaat uw melding over?")
        if sel.count():
            sel.first.click(); pg.wait_for_timeout(500)
            opt = pg.get_by_text("Losliggende stoeptegel")
            if opt.count(): opt.first.click()
            pg.keyboard.press("Escape")
        for label, val in [("Waar is het? (straat en huisnummer of omschrijving)", "Dorpsstraat 12, Demostad"),
                           ("Omschrijving", "De stoeptegel voor nummer 12 steekt 3 cm uit."),
                           ("Uw achternaam", "Moulin"), ("Uw e-mailadres", "s.moulin@example.com")]:
            loc = pg.get_by_label(label, exact=True)
            if loc.count():
                loc.first.fill(val)
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

    def behandelaar():
        pg = new()
        django_login(pg, "zaken", "/admin/zaken/zaak/")
        pg.goto(f"https://zaken.{D}/admin/zaken/zaak/")
        shot(pg, "behandelaar-1")
        pg.locator("#result_list tbody tr a").first.click()
        pg.wait_for_load_state("networkidle")
        shot(pg, "behandelaar-2")
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
        pg.close()

    for fn in (inwoner, kcc, behandelaar, beheer, ontwikkelaar):
        safe(fn)
    b.close()
