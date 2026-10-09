"""Rookproef: dien het demoformulier in via de publieke API en toon de status."""
import os, sys, time, requests
B = f"https://formulieren.{os.environ['BASE_DOMAIN']}"
s = requests.Session(); s.headers.update({"Content-Type": "application/json", "Referer": f"{B}/melding-openbare-ruimte"})
s.hooks["response"].append(lambda r, *a, **k: r.headers.get("X-CSRFToken") and s.headers.update({"X-CSRFToken": r.headers["X-CSRFToken"]}))
form = s.get(f"{B}/api/v2/forms/melding-openbare-ruimte").json()
sub = s.post(f"{B}/api/v2/submissions", json={"form": form["url"], "formUrl": f"{B}/melding-openbare-ruimte"}); sub.raise_for_status(); sub = sub.json()
step = sub["steps"][0]["url"]
r = s.put(step, json={"data": {"soortMelding": "stoeptegel", "locatie": "Stoep 1, Demostad",
          "omschrijving": "Losliggende tegel voor nummer 1 (rooktest)", "naam": "Inwoner", "email": "inwoner@example.com"}})
print("step", r.status_code, r.text[:300] if r.status_code >= 400 else "")
r = s.post(f"{sub['url']}/_complete", json={"privacyPolicyAccepted": True, "statementOfTruthAccepted": True})
print("complete", r.status_code, r.text[:800])
st = r.json().get("statusUrl")
for _ in range(30):
    time.sleep(3); j = s.get(st).json()
    if j.get("status") == "done": print("status", j); break
else: print("status", j)
