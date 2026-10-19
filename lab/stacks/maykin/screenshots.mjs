// Screenshots van de burgerportalen in stack maykin (Open Inwoner en Open Formulieren),
// ingelogd via de DigiD-simulatie in Keycloak. Gebruik (op de host, stack draait):
//   NODE_PATH=$(npm root -g) DIGID_SIM_WACHTWOORD=... node stacks/maykin/screenshots.mjs
// Chromium komt uit PLAYWRIGHT_BROWSERS_PATH (standaard /opt/pw-browsers).
import { createRequire } from "module";
const require = createRequire(import.meta.url);
process.env.PLAYWRIGHT_BROWSERS_PATH ||= "/opt/pw-browsers";
const { chromium } = require("playwright");

const OIP = process.env.OIP_URL || "http://localhost:8103";
const OF = process.env.OF_URL || "http://localhost:8102";
const WW = process.env.DIGID_SIM_WACHTWOORD;
const UIT = process.env.UIT || "docs/screenshots/maykin";
const BURGERS = { A: "999990627", B: "999997609" };

async function keycloak(page, bsn) {
  await page.waitForSelector("#kc-form-login", { timeout: 30000 });
  await page.fill("#username", bsn);
  await page.fill("#password", WW);
  await Promise.all([page.waitForLoadState("networkidle"), page.click("#kc-login")]);
}

async function oipLogin(page, bsn, email) {
  await page.goto(`${OIP}/digid-oidc/authenticate/?next=/`);
  await keycloak(page, bsn);
  if (page.url().includes("/register/necessary")) {
    const mail = page.locator("input[name='email']");
    if (await mail.count()) await mail.fill(email);
    await Promise.all([page.waitForURL(u => !u.href.includes("/register/necessary")),
      page.locator("form:has(input[name='email']) [type='submit']").first().click()]);
  }
}

async function shot(page, naam) {
  await page.waitForLoadState("networkidle").catch(() => {});
  const weiger = page.getByRole("button", { name: "Alles weigeren" });
  if (await weiger.isVisible().catch(() => false)) { await weiger.click().catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${UIT}/${naam}.png`, fullPage: true });
  console.log(`${naam}.png  ${page.url()}`);
}

const browser = await chromium.launch();
const zaakLinks = {};
for (const [wie, bsn] of Object.entries(BURGERS)) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "nl-NL" });
  const page = await ctx.newPage();
  await oipLogin(page, bsn, `burger-${wie.toLowerCase()}@voorbeeldstad.example`);
  const p = `oip-burger-${wie.toLowerCase()}`;
  await page.goto(`${OIP}/`); await shot(page, `${p}-1-home-taken`);
  await page.goto(`${OIP}/cases/`); await shot(page, `${p}-2-mijn-aanvragen`);
  const links = await page.locator("a[href*='/cases/'][href*='/status']").evaluateAll(as => as.map(a => a.href));
  zaakLinks[wie] = [...new Set(links)];
  if (zaakLinks[wie].length) { await page.goto(zaakLinks[wie][zaakLinks[wie].length - 1]); await shot(page, `${p}-3-zaakdetail`); }
  await page.goto(`${OIP}/profile/`); await shot(page, `${p}-4-profiel-brp`);
  await page.goto(`${OIP}/cases/contactmomenten/`);
  await shot(page, `${p}-5-mijn-vragen`);
  if (wie === "A") {
    await page.goto(`${OF}/melding-openbare-ruimte/`);
    await page.waitForTimeout(3000);
    await shot(page, "of-burger-a-1-formulier-start");
    // Inloggen met DigiD (Keycloak onthoudt de sessie van Open Inwoner niet altijd)
    await Promise.all([page.waitForURL(u => !u.href.endsWith("/startpagina")),
      page.getByRole("link", { name: /Inloggen met DigiD/ }).or(page.getByRole("button", { name: /Inloggen met DigiD/ })).first().click()]);
    if (page.url().includes(":8080")) await keycloak(page, bsn);
    await page.waitForTimeout(3000);
    const start = page.getByRole("button", { name: /Formulier starten|Start/i }).first();
    if (await start.isVisible().catch(() => false)) { await start.click(); await page.waitForTimeout(4000); }
    await shot(page, "of-burger-a-2-stap-met-brp-prefill");
  }
  await ctx.close();
}

// Isolatie: A probeert de zaakdetail-URL's van B
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "nl-NL" });
const page = await ctx.newPage();
await oipLogin(page, BURGERS.A, "burger-a@voorbeeldstad.example");
for (const [i, link] of (zaakLinks.B || []).entries()) {
  const r = await page.goto(link);
  console.log(`A opent zaak van B: ${link} -> HTTP ${r.status()}`);
  await shot(page, `oip-isolatie-a-opent-zaak-van-b-${i + 1}`);
}
await browser.close();
