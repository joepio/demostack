// Screenshots van stack g4: NL Portal (burgers A, B en D via de DigiD-simulatie),
// GZAC (behandelaar) en de IKO-beheer-UI (beheerder). Gebruik (op de host, stack draait):
//   export DIGID_SIM_WACHTWOORD=... MEDEWERKER_WACHTWOORD=...   (uit .env)
//   NODE_PATH=$(npm root -g) node stacks/g4/screenshots.mjs
// ALLEEN=nlportal,gzac,iko kiest de onderdelen.
// Chromium komt uit PLAYWRIGHT_BROWSERS_PATH (standaard /opt/pw-browsers).
import { createRequire } from "module";
const require = createRequire(import.meta.url);
process.env.PLAYWRIGHT_BROWSERS_PATH ||= "/opt/pw-browsers";
const { chromium } = require("playwright");

const NLP = `http://localhost:${process.env.PORT_NLPORTAL || 8203}`;
const NLP_API = `http://localhost:${process.env.PORT_NLPORTAL_BACKEND || 8204}`;
const GZAC = `http://localhost:${process.env.PORT_GZAC || 8205}`;
const IKO = `http://localhost:${process.env.PORT_IKO || 8207}`;
const DIGID_WW = process.env.DIGID_SIM_WACHTWOORD;
const MEDEWERKER_WW = process.env.MEDEWERKER_WACHTWOORD;
const UIT = process.env.UIT || "docs/screenshots/g4";
const BURGERS = { A: "999990627", B: "999997609", D: "999991991" };

async function keycloak(page, gebruiker, wachtwoord) {
  await page.waitForSelector("#kc-form-login", { timeout: 60000 });
  await page.fill("#username", gebruiker);
  await page.fill("#password", wachtwoord);
  // GZAC blijft pollen: wachten tot de browser Keycloak verlaat, niet op networkidle
  await Promise.all([page.waitForURL(u => !u.href.includes("/realms/"), { timeout: 60000 }), page.click("#kc-login")]);
}

async function shot(page, naam, wacht = 2500) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(wacht);
  await page.screenshot({ path: `${UIT}/${naam}.png`, fullPage: true });
  console.log(`${naam}.png  ${page.url()}`);
}

// Zaak-uuid's per burger via de GraphQL-API, met het token uit de sessie van de frontend
async function zaken(page) {
  return page.evaluate(async (api) => {
    const sleutel = Object.keys(sessionStorage).find(k => k.startsWith("oidc.user:"));
    let token = sleutel ? JSON.parse(sessionStorage.getItem(sleutel)).access_token : null;
    if (!token) {
      for (const k of Object.keys(localStorage)) {
        try { const v = JSON.parse(localStorage.getItem(k)); if (v && v.access_token) token = v.access_token; } catch (e) {}
      }
    }
    if (!token) return [];
    const r = await fetch(`${api}/graphql`, { method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ query: "{ getZaken(pageSize: 50) { content { uuid identificatie } } }" }) });
    const j = await r.json();
    return j.data ? j.data.getZaken.content : [];
  }, NLP_API);
}

const browser = await chromium.launch();
const zaakVan = {};
const alleen = (process.env.ALLEEN || "nlportal,gzac,iko").split(",");
if (alleen.includes("nlportal")) for (const [wie, bsn] of Object.entries(BURGERS)) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "nl-NL" });
  const page = await ctx.newPage();
  await page.goto(`${NLP}/`);
  await keycloak(page, bsn, DIGID_WW);
  await page.waitForURL(u => u.href.startsWith(NLP) && !u.href.includes("/oidc/callback"), { timeout: 60000 }).catch(() => {});
  const p = `nlportal-burger-${wie.toLowerCase()}`;
  await shot(page, `${p}-1-overzicht`, 4000);
  await page.goto(`${NLP}/zaken`); await shot(page, `${p}-2-mijn-zaken`, 4000);
  const lijst = await zaken(page);
  zaakVan[wie] = lijst;
  const eerste = lijst.find(z => wie !== "D" || !z.identificatie.startsWith("VBS-")) || lijst[0];
  if (eerste) { await page.goto(`${NLP}/zaken/zaak/${eerste.uuid}`); await shot(page, `${p}-3-zaakdetail`, 4000); }
  if (wie !== "D") {
    await page.goto(`${NLP}/taken`); await shot(page, `${p}-4-mijn-taken`, 4000);
    await page.goto(`${NLP}/berichten`); await shot(page, `${p}-5-berichten`, 4000);
  }
  if (wie === "A") {
    await page.goto(`${NLP}/account`); await shot(page, `${p}-6-account-brp`, 4000);
  }
  if (wie === "B" && zaakVan.A && zaakVan.A.length) {
    // B probeert een zaak van A te openen via de URL
    await page.goto(`${NLP}/zaken/zaak/${zaakVan.A[0].uuid}`);
    await shot(page, `nlportal-burger-b-7-probeert-zaak-van-a`, 4000);
  }
  await ctx.close();
}

// GZAC: behandelaar
if (alleen.includes("gzac")) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "nl-NL" });
  const page = await ctx.newPage();
  await page.goto(`${GZAC}/`);
  await keycloak(page, "behandelaar.bakker", MEDEWERKER_WW);
  await page.waitForTimeout(6000);
  await shot(page, "gzac-1-dashboard", 3000);
  // via het menu, zoals een behandelaar: Dossiers > Parkeervergunning bewoners
  await page.getByText("Dossiers", { exact: true }).first().click();
  await page.getByText("Parkeervergunning", { exact: false }).first().click();
  await shot(page, "gzac-2-dossiers-parkeervergunning", 5000);
  const dossier = page.locator("tbody tr, .cds--data-table tbody tr").first();
  if (await dossier.count()) { await dossier.click(); await shot(page, "gzac-3-dossier-detail", 6000); }
  await page.goto(`${GZAC}/tasks`);
  await page.waitForTimeout(3000);
  await page.getByText("Alle taken", { exact: true }).first().click().catch(() => {});
  await shot(page, "gzac-4-alle-taken", 5000);
  await ctx.close();
}

// IKO: beheerder
if (alleen.includes("iko")) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "nl-NL" });
  const page = await ctx.newPage();
  await page.goto(`${IKO}/admin`);
  await keycloak(page, "beheer.yilmaz", MEDEWERKER_WW);
  await page.goto(`${IKO}/admin/aggregated-data-profiles`); await shot(page, "iko-1-profielen", 2000);
  await page.goto(`${IKO}/admin/connectors`); await shot(page, "iko-2-connectoren", 2000);
  await ctx.close();
}
await browser.close();
