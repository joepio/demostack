// Screenshots van stack vcg. Gebruik (op de host, stack draait en is geseed):
//   set -a; . ./.env; set +a; NODE_PATH=$(npm root -g) node stacks/vcg/screenshots.mjs
// Chromium komt uit PLAYWRIGHT_BROWSERS_PATH (standaard /opt/pw-browsers).
//
// De VCG-basisset heeft zelf geen burgerportaal; schermafdrukken van een portaal horen bij
// de plug-in die het levert (docs/PLUGINS.md).
// 1. Medewerkers via Keycloak-realm vcg: Open Organisatie en Open Beheer als functioneel
//    beheerder, en de weigering voor een behandelaar.
// 2. De andere componenten: Operaton Tasklist, publicatiebank, WordPress (OpenPDC),
//    OpenRegister in Nextcloud en de FSC-controller van Voorbeeldstad.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
process.env.PLAYWRIGHT_BROWSERS_PATH ||= "/opt/pw-browsers";
const { chromium } = require("playwright");

const P = (n, d) => `http://localhost:${process.env[`PORT_${n}`] || d}`;
const UIT = process.env.UIT || "docs/screenshots/vcg";
const MW = process.env.MEDEWERKER_WACHTWOORD;
const ADMIN = [process.env.ADMIN_USERNAME || "admin", process.env.ADMIN_PASSWORD];

async function shot(page, naam) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${UIT}/${naam}.png`, fullPage: true });
  console.log(`${naam}.png  ${page.url()}`);
}

async function keycloak(page, gebruiker) {
  await page.waitForSelector("#kc-form-login", { timeout: 30000 });
  await page.fill("#username", gebruiker);
  await page.fill("#password", MW);
  await Promise.all([page.waitForLoadState("networkidle"), page.click("#kc-login")]);
}

const browser = await chromium.launch();
const nieuw = async () => (await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "nl-NL" })).newPage();

// 1. Medewerkers via realm vcg
for (const [naam, basis, pad] of [["openorganisatie", P("OPENORGANISATIE", 8251), "/admin/medewerkers/medewerker/"],
                                  ["openbeheer", P("OPENBEHEER", 8155), "/"]]) {
  const page = await nieuw();
  await page.goto(`${basis}/auth/oidc/authenticate/?next=${encodeURIComponent(pad)}`);
  await keycloak(page, "beheer.devos");
  if (naam === "openbeheer") {
    // De frontend (via openbeheer-ui) gaat zelf naar de zaaktypen van de catalogus
    await page.goto(`${basis}/`); await page.waitForTimeout(5000);
    await shot(page, `${naam}-1-beheer-devos`);
    await page.getByRole("link", { name: "VBS-PARKVERG" }).first().click();
    await page.waitForTimeout(4000);
    await shot(page, `${naam}-3-zaaktype-parkeervergunning`);
  } else {
    await page.goto(`${basis}${pad}`);
    await shot(page, `${naam}-1-beheer-devos`);
  }
  await page.context().close();
}
{
  const page = await nieuw();
  await page.goto(`${P("OPENBEHEER", 8155)}/auth/oidc/authenticate/?next=/`);
  await keycloak(page, "a.vermeulen");
  await shot(page, "openbeheer-2-behandelaar-geweigerd");
  await page.context().close();
}

// 2. Overige componenten
{
  const page = await nieuw();
  await page.goto(`${P("OPERATON", 8254)}/operaton/app/cockpit/default/`);
  await page.waitForSelector("input[type=password]", { timeout: 30000 });
  await page.fill("input[type=text], input[name=username]", ADMIN[0]);
  await page.fill("input[type=password]", ADMIN[1]);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(4000);
  await page.goto(`${P("OPERATON", 8254)}/operaton/app/cockpit/default/#/processes`);
  await page.waitForTimeout(3000);
  await shot(page, "operaton-1-cockpit-processen");
  await page.context().close();
}
{
  const page = await nieuw();
  const basis = P("PUBLICATIEBANK", 8252);
  await page.goto(`${basis}/admin/login/?next=/admin/publications/publication/`);
  await page.fill("#id_auth-username, #id_username", ADMIN[0]);
  await page.fill("#id_auth-password, #id_password", ADMIN[1]);
  await Promise.all([page.waitForLoadState("networkidle"), page.press("#id_auth-password, #id_password", "Enter")]);
  await page.goto(`${basis}/admin/publications/publication/`);
  await shot(page, "publicatiebank-1-publicaties");
  await page.context().close();
}
{
  const page = await nieuw();
  const basis = P("WORDPRESS", 8256);
  await page.goto(`${basis}/wp-login.php`);
  await page.fill("#user_login", ADMIN[0]);
  await page.fill("#user_pass", ADMIN[1]);
  await Promise.all([page.waitForLoadState("networkidle"), page.click("#wp-submit")]);
  await page.goto(`${basis}/wp-admin/edit.php?post_type=pdc-item`);
  await shot(page, "openpdc-1-producten-en-diensten");
  await page.context().close();
}
{
  const page = await nieuw();
  const basis = P("NEXTCLOUD", 8257);
  await page.goto(`${basis}/login`);
  await page.fill("#user", ADMIN[0]);
  await page.fill("#password", ADMIN[1]);
  await Promise.all([page.waitForLoadState("networkidle"), page.click("[type=submit]")]);
  await page.goto(`${basis}/index.php/apps/openregister/`);
  await page.waitForTimeout(5000);
  // Welkomstvenster van Nextcloud (firstrunwizard) sluiten
  for (let i = 0; i < 3; i++) { await page.keyboard.press("Escape"); await page.waitForTimeout(500); }
  await shot(page, "openregister-1-dashboard");
  await page.context().close();
}
{
  const page = await nieuw();
  await page.goto(`${P("FSC_VOORBEELDSTAD", 8260)}/`);
  await page.waitForTimeout(3000);
  await shot(page, "openfsc-1-controller-voorbeeldstad");
  const contracten = page.getByRole("link", { name: /Contract/i }).first();
  if (await contracten.isVisible().catch(() => false)) {
    await contracten.click(); await page.waitForTimeout(3000);
    await shot(page, "openfsc-2-contracten");
  }
  await page.context().close();
}
await browser.close();
