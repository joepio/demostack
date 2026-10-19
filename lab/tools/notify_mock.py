"""Nabootsing van NotifyNL (de GOV.UK Notify-API) voor NotifyNL OMC in stack dimpact.

POST /v2/notifications/email   bewaart het e-mailverzoek en antwoordt zoals Notify
POST /v2/notifications/sms     idem voor sms
GET  /v2/template/<id>         een sjabloon (OMC vraagt sjablonen soms op)
GET  /berichten                de laatste 500 verzoeken als JSON (voor de tests)
GET  /health                   200

Alleen voor de demo: alles in het geheugen, geen controle van het JWT van de afzender
(wel of er een Bearer-token meekwam).
"""
import json
import uuid
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BERICHTEN = deque(maxlen=500)


class Handler(BaseHTTPRequestHandler):
    def _antwoord(self, status, body=None):
        data = json.dumps(body if body is not None else {}, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        pad = self.path.split("?")[0].rstrip("/")
        soort = {"/v2/notifications/email": "email", "/v2/notifications/sms": "sms"}.get(pad)
        if not soort:
            return self._antwoord(404, {"errors": [{"error": "NotFound", "message": pad}]})
        lengte = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(lengte) or b"{}")
        except json.JSONDecodeError:
            return self._antwoord(400, {"errors": [{"error": "BadRequest", "message": "geen JSON"}]})
        nid = str(uuid.uuid4())
        BERICHTEN.append({
            "id": nid, "soort": soort, "ontvangen": datetime.now(timezone.utc).isoformat(),
            "bearer": self.headers.get("Authorization", "").startswith("Bearer "), "verzoek": body,
        })
        print(f"notify {soort}: sjabloon {body.get('template_id')} aan "
              f"{body.get('email_address') or body.get('phone_number')}", flush=True)
        template = {"id": body.get("template_id"), "version": 1,
                    "uri": f"http://notify-mock.local:8080/v2/template/{body.get('template_id')}"}
        content = {"body": json.dumps(body.get("personalisation") or {}, ensure_ascii=False)}
        if soort == "email":
            content.update({"subject": "Bericht van Gemeente Voorbeeldstad", "from_email": "noreply@voorbeeldstad.example"})
        else:
            content["from_number"] = "Voorbeeldstad"
        return self._antwoord(201, {"id": nid, "reference": body.get("reference"), "content": content,
                                    "uri": f"http://notify-mock.local:8080/v2/notifications/{nid}",
                                    "template": template})

    def do_GET(self):
        pad = self.path.split("?")[0].rstrip("/")
        if pad == "/health":
            return self._antwoord(200, {"status": "ok"})
        if pad in ("", "/berichten"):
            return self._antwoord(200, {"aantal": len(BERICHTEN), "berichten": list(BERICHTEN)})
        if pad.startswith("/v2/template/"):
            tid = pad.rsplit("/", 1)[-1]
            return self._antwoord(200, {"id": tid, "name": "Demogemeente", "type": "email", "version": 1,
                                        "body": "((zaak.omschrijving))", "subject": "Uw zaak",
                                        "created_at": "2026-10-01T00:00:00.000000Z", "created_by": "demo",
                                        "updated_at": None, "letter_contact_block": None,
                                        "personalisation": {}, "postage": None})
        return self._antwoord(404, {"errors": [{"error": "NotFound", "message": pad}]})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
