// Screenshots van stack dimpact. De burgerportalen (Open Inwoner, Open Formulieren) maakt
// het script van stack maykin; dit script doet de medewerkerskant: KISS en ITA, ingelogd
// via Keycloak (realm podiumd). Gebruik (op de host, stack draait):
//   NODE_PATH=$(npm root -g) DIGID_SIM_WACHTWOORD=... UIT=docs/screenshots/dimpact \
//     node stacks/maykin/screenshots.mjs
//   NODE_PATH=$(npm root -g) MEDEWERKER_WACHTWOORD=... node stacks/dimpact/screenshots.mjs
// Chromium komt uit PLAYWRIGHT_BROWSERS_PATH (standaard /opt/pw-browsers).
import { createRequire } from "module";
const require = createRequire(import.meta.url);
process.env.PLAYWRIGHT_BROWSERS_PATH ||= "/opt/pw-browsers";
const { chromium } = require("playwright");

const KISS = process.env.KISS_URL || "http://localhost:8156";
const ITA = process.env.ITA_URL || "http://localhost:8157";
const OAB = process.env.OAB_URL || "http://localhost:8154";
const WW = process.env.MEDEWERKER_WACHTWOORD;
const UIT = process.env.UIT || "docs/screenshots/dimpact";

async function login(page, start, gebruiker) {
  await page.goto(start);
  await page.waitForSelector("#kc-form-login", { timeout: 30000 });
  await page.fill("#username", gebruiker);
  await page.fill("#password", WW);
  await Promise.all([page.waitForURL(u => !u.href.includes("/realms/"), { timeout: 30000 }), page.click("#kc-login")]);
  await page.waitForLoadState("networkidle").catch(() => {});
}

async function shot(page, naam) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${UIT}/${naam}.png`, fullPage: true });
  console.log(`${naam}.png  ${page.url()}`);
}

async function nieuw(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: "nl-NL" });
  return [ctx, await ctx.newPage()];
}

const browser = await chromium.launch();

// KISS: klantcontactmedewerker
{
  const [ctx, page] = await nieuw(browser);
  await login(page, `${KISS}/api/challenge?returnUrl=/`, "kcm.jansen");
  await shot(page, "kiss-kcm-1-start");
  await ctx.close();
}

// ITA: werkvoorraad per medewerker, en Desai opent de taak van het KCC
for (const [gebruiker, eigen, ander] of [["behandelaar.desai", "8000000001", "8000000002"],
                                         ["kcm.jansen", "8000000002", "8000000001"]]) {
  const [ctx, page] = await nieuw(browser);
  const kort = gebruiker.split(".")[1];
  await login(page, `${ITA}/api/challenge?returnUrl=/`, gebruiker);
  await shot(page, `ita-${kort}-1-werkvoorraad`);
  await page.goto(`${ITA}/contactverzoek/${eigen}`);
  await shot(page, `ita-${kort}-2-eigen-contactverzoek`);
  if (gebruiker === "behandelaar.desai") {
    const r = await page.request.get(`${ITA}/api/internetaken/${ander}`);
    console.log(`Desai vraagt taak ${ander} (KCC) op: HTTP ${r.status()}`);
    await page.goto(`${ITA}/contactverzoek/${ander}`);
    await shot(page, `ita-${kort}-3-taak-van-kcc-geweigerd`);
  }
  await ctx.close();
}

// Open Archiefbeheer: medewerker via Keycloak, de gesynchroniseerde afgesloten zaken
{
  const [ctx, page] = await nieuw(browser);
  await login(page, `${OAB}/oidc/authenticate/`, "beheer.devries");
  await page.goto(`${OAB}/admin/zaken/zaak/`);
  await shot(page, "oab-devries-1-afgesloten-zaken");
  await ctx.close();
}

await browser.close();
