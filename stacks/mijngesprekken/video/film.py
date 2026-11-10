import os, time
from playwright.sync_api import sync_playwright
CP, AP = os.environ['CP'], os.environ['AP']
REGIE = 'https://gesprekken.demostack.nl/regie/'
W, H = 1920, 1080
OVERLAY = """
(() => { if (window.top !== window) return;
  const mk = () => {
    if (document.getElementById('__cap')) return;
    const c = document.createElement('div'); c.id='__cap';
    c.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);max-width:1500px;z-index:2147483647;background:rgba(15,30,60,.92);color:#fff;font:600 26px/1.35 system-ui,sans-serif;padding:14px 26px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.35);pointer-events:none;text-align:center;opacity:0;transition:opacity .3s';
    const k = document.createElement('div'); k.id='__cur';
    k.style.cssText='position:fixed;left:-60px;top:-60px;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:rgba(255,200,0,.45);border:3px solid rgba(230,120,0,.95);z-index:2147483647;pointer-events:none;transition:left .6s ease, top .6s ease, transform .15s';
    document.documentElement.append(c, k);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mk); else mk();
})();
"""
cur = [W/2, H/2]
def cap(p, html, wait=2.2):
    p.evaluate("""h => { const c=document.getElementById('__cap'); if(!c) return; if(!h){c.style.opacity=0;return;} c.innerHTML=h; c.style.opacity=1; }""", html)
    p.wait_for_timeout(int(wait*1000))
def move(p, loc):
    loc.scroll_into_view_if_needed(); p.wait_for_timeout(300)
    b = loc.bounding_box(); x, y = b['x']+b['width']/2, b['y']+b['height']/2
    p.evaluate("([x,y]) => { const k=document.getElementById('__cur'); if(k){k.style.left=x+'px'; k.style.top=y+'px';} }", [x, y])
    p.mouse.move(x, y, steps=20); p.wait_for_timeout(650)
def click(p, loc, after=900):
    move(p, loc)
    p.evaluate("() => { const k=document.getElementById('__cur'); if(k){k.style.transform='scale(.6)'; setTimeout(()=>k.style.transform='',180);} }")
    loc.click(); p.wait_for_timeout(after)
def typ(p, loc, text, delay=28):
    click(p, loc, 300); loc.press_sequentially(text, delay=delay); p.wait_for_timeout(700)

OIP_ = 'Open Inwoner <span style="opacity:.75">(Maykin)</span>'
GRC_ = 'Gesprekken API <span style="opacity:.75">(OneGround)</span>'
OK_ = 'Open Klant <span style="opacity:.75">(Maykin)</span>'
OND = 'Wanneer wordt de stoeptegel gerepareerd?'
VRAAG = 'Ik meldde op 6 oktober een losse stoeptegel voor Dorpsstraat 12. De tegel ligt nu helemaal los en mijn buurvrouw met rollator struikelde er gisteren bijna over. Wanneer wordt dit gemaakt? Ik heb een foto bijgevoegd.'
ANTW = 'Beste mevrouw Moulin, dank voor uw foto. We hebben vandaag een afzetting bij de tegel geplaatst. De aannemer legt de tegel donderdag 13 november opnieuw. Excuses dat het zo lang duurde. Met vriendelijke groet, Team Openbare Ruimte'
REPLY = 'Fijn, dank u wel! Ik laat het mijn buurvrouw weten.'

with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': W, 'height': H}, record_video_dir='video', record_video_size={'width': W, 'height': H},
                        http_credentials={'username': 'demo', 'password': CP}, locale='nl-NL')
    ctx.add_init_script(OVERLAY)
    ctx.on('page', lambda pg: None)
    p = ctx.new_page()
    p.on('dialog', lambda d: d.accept())
    p.goto(REGIE); p.wait_for_timeout(1500)
    cap(p, 'MijnGesprekken: één gesprek bij de zaak, voor inwoner en gemeente<br><span style="font-weight:400;font-size:22px">Regiepagina (ingelogd als <b>demo</b>): links de inwoner, rechts de medewerker</span>', 4)
    oip = p.frame_locator('iframe[title="Open Inwoner"]'); mw = p.frame_locator('iframe[title="Medewerker"]')
    # Inloggen DigiD
    cap(p, f'Suzanne Moulin logt in bij {OIP_} met DigiD', 1.5)
    try: click(p, oip.get_by_text('Alles toestaan'), 600)
    except Exception: pass
    click(p, oip.locator('a[href^="/digid/login/"]').last, 2000)
    click(p, oip.get_by_text('Met burgerservicenummer'), 1500)
    cap(p, 'DigiD (testomgeving): inloggen met burgerservicenummer 999993653', 0.5)
    typ(p, oip.locator('input[name=auth_bsn]'), '999993653', 90)
    click(p, oip.locator('button[type=submit], input[type=submit]').first, 3000)
    try: click(p, oip.get_by_text('Alles toestaan'), 600)
    except Exception: pass
    oip.locator('#gesprekken').wait_for(timeout=60000)
    # Zaak bekijken
    cap(p, f'{OIP_}: Suzanne bekijkt haar melding "Losliggende stoeptegel"<br><span style="font-weight:400;font-size:22px">Gemeld op 6 oktober, nog steeds in behandeling. Zaak uit Open Zaak.</span>', 0.5)
    move(p, oip.locator('h1').first); p.wait_for_timeout(1500)
    move(p, oip.locator('.status-list, [class*=status]').first); p.wait_for_timeout(2000)
    cap(p, f'{OIP_}: onderaan de zaak staat "Mijn gesprekken"', 0.5)
    move(p, oip.locator('#gesprekken h2')); p.wait_for_timeout(1500)
    # Nieuw gesprek
    cap(p, 'Suzanne stelt haar vraag bij de zaak, met een foto als bijlage', 0.5)
    click(p, oip.locator('.gesprekken__start summary'))
    typ(p, oip.locator('#gesprek-start-onderwerp'), OND)
    typ(p, oip.locator('#gesprek-start-tekst'), VRAAG, 18)
    move(p, oip.locator('#gesprek-start-bijlage'))
    oip.locator('#gesprek-start-bijlage').set_input_files('foto-stoeptegel.pdf'); p.wait_for_timeout(1200)
    cap(p, f'{OIP_} stuurt het gesprek naar de {GRC_}', 0.5)
    click(p, oip.locator('.gesprekken__start button[type=submit]'), 500)
    oip.get_by_text(OND).first.wait_for(timeout=30000)
    oip.get_by_text('Bedankt voor uw bericht').wait_for(timeout=60000)
    move(p, oip.get_by_text('Bedankt voor uw bericht'))
    cap(p, f'Automatisch antwoord, direct verstuurd door de {GRC_}', 3.5)
    # Medewerker
    cap(p, 'Medewerker van Team Openbare Ruimte ziet het gesprek binnenkomen, met de zaak erbij', 0.5)
    click(p, mw.locator('.item', has_text=OND), 1800)
    cap(p, f'De foto komt via de {GRC_} (bestandsopslag S3)', 0.5)
    dl = mw.locator('#detail a[href^="/api/bestand/"]')
    move(p, dl)
    with ctx.expect_page() as np:
        click(p, dl, 300)
    try: np.value.close()
    except Exception: pass
    p.wait_for_timeout(1500)
    cap(p, f'Eventstroom: elke stap is een event van de {GRC_} dat andere systemen kunnen volgen', 0.5)
    click(p, mw.locator('nav button[data-tab=events]'), 4000)
    click(p, mw.locator('nav button[data-tab=gesprekken]'), 800)
    click(p, mw.locator('.item', has_text=OND), 1000)
    cap(p, 'De medewerker antwoordt', 0.5)
    typ(p, mw.locator('#antwoord'), ANTW, 16)
    click(p, mw.locator('#stuur'), 1000)
    # Suzanne ziet antwoord
    cap(p, f'Het antwoord verschijnt vanzelf in {OIP_}, zonder te verversen', 0.5)
    oip.get_by_text('De aannemer legt de tegel').wait_for(timeout=60000)
    move(p, oip.get_by_text('De aannemer legt de tegel')); p.wait_for_timeout(2500)
    cap(p, 'Suzanne reageert', 0.5)
    typ(p, oip.locator('.gesprekken__invoer textarea'), REPLY, 30)
    click(p, oip.locator('button.gesprekken__knop'), 500)
    oip.get_by_text('Ik laat het mijn buurvrouw weten').wait_for(timeout=30000); p.wait_for_timeout(1500)
    cap(p, 'Haar vraag is beantwoord: Suzanne sluit het gesprek af', 0.5)
    click(p, oip.locator('.gesprekken__afsluiten button'), 3000)
    click(p, oip.locator('.gesprekken__tab', has_text='Gesloten'), 2000)
    # Klantcontact
    cap(p, f'Bij het afsluiten legt de {GRC_} het gesprek vast als klantcontact in {OK_}', 0.5)
    click(p, mw.locator('nav button[data-tab=klant]'), 1500)
    for i in range(20):
        if 'Wanneer wordt de stoeptegel' in mw.locator('#kclijst').inner_text(): break
        click(p, mw.locator('nav button[data-tab=gesprekken]'), 300); click(p, mw.locator('nav button[data-tab=klant]'), 2000)
    move(p, mw.locator('#kclijst').get_by_text('Wanneer wordt de stoeptegel').first); p.wait_for_timeout(3000)
    # Open Klant beheer
    cap(p, f'Het klantcontact in het beheer van {OK_}', 1.5)
    p.goto('https://gesprekken-klant.demostack.nl/admin/login/?next=/admin/klantinteracties/klantcontact/'); p.wait_for_timeout(1200)
    typ(p, p.locator('#id_auth-username'), 'admin', 60)
    typ(p, p.locator('#id_auth-password'), AP, 40)
    click(p, p.locator('input[type=submit][value=Aanmelden]'), 2500)
    cap(p, f'Klantcontact in {OK_}: kanaal MijnGesprekken, met Suzanne en de zaak erbij', 0.5)
    link = p.locator('#result_list tbody tr').first.locator('th a, td a').first
    move(p, link); p.wait_for_timeout(1500)
    click(p, link, 2500)
    p.mouse.wheel(0, 500); p.wait_for_timeout(2500)
    cap(p, 'Eén gesprek bij de zaak, voor inwoner en medewerker<br><span style="font-weight:400;font-size:22px">Open Inwoner, Gesprekken API (OneGround), Open Klant en Open Zaak, via standaard API\'s</span>', 5)
    vid = p.video
    ctx.close(); b.close()
    print('VIDEO', vid.path())
