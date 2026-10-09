"""Zet één voorbeeldmail in Mailpit (statusbericht aan de testinwoner), zodat de mailbox niet leeg is."""
import urllib.parse
import json, smtplib, urllib.request
from email.message import EmailMessage

SUBJECT = "Uw melding ZAAK-2026-0000000001 is in behandeling"
try:
    with urllib.request.urlopen("http://mailpit:8025/api/v1/search?query=" + urllib.parse.quote(f'subject:"{SUBJECT}"')) as r:
        if json.load(r).get("messages_count"):
            print("voorbeeldmail bestaat al"); raise SystemExit
except (OSError, ValueError):
    pass
m = EmailMessage()
m["From"] = "Gemeente Demostad <noreply@demogemeente.local>"
m["To"] = "s.moulin@example.com"
m["Subject"] = SUBJECT
m.set_content("Beste mevrouw Moulin,\n\nUw melding over een losliggende stoeptegel aan de Dorpsstraat 12 is in behandeling genomen.\n"
              "Een opzichter komt deze week kijken.\n\nMet vriendelijke groet,\nTeam Meldingen, Gemeente Demostad")
with smtplib.SMTP("mailpit", 1025) as s:
    s.send_message(m)
print("voorbeeldmail verstuurd")
