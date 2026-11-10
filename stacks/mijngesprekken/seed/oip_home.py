# Korte welkomsttekst op de homepage met een link naar Mijn aanvragen.
from cms.api import add_plugin
from cms.models import PageContent
c = PageContent.admin_manager.get(page__reverse_id="home", language="nl")
ph = c.get_placeholders().get(slot="content")
if not ph.get_plugins().exists():
    add_plugin(ph, "TextPlugin", "nl", body=(
        "<h1>Welkom bij Demogemeente</h1>"
        "<p>Dit is de MijnGesprekken-demo. Ga naar <a href=\"/cases/\">Mijn aanvragen</a>, open een zaak "
        "en start onderaan een gesprek met de gemeente. U kunt ook een bijlage meesturen.</p>"))
    print("homepage gevuld")
