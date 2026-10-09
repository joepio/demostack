"""Minimale webhook-ontvanger voor Open Notificaties.

POST /callback  bewaart de notificatie (alleen met het juiste token)
GET  /notificaties  geeft de laatste 500 notificaties als JSON
GET  /health  geeft 200

Alleen voor de demo: alles staat in het geheugen.
"""
import json
import os
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get("NOTIFICATIE_SINK_TOKEN", "")
ONTVANGEN = deque(maxlen=500)


class Handler(BaseHTTPRequestHandler):
    def _antwoord(self, status, body=None):
        data = json.dumps(body if body is not None else {}, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.rstrip("/") != "/callback":
            return self._antwoord(404, {"fout": "onbekend pad"})
        if TOKEN and self.headers.get("Authorization", "") not in (f"Token {TOKEN}", f"Bearer {TOKEN}"):
            return self._antwoord(403, {"fout": "ongeldig token"})
        lengte = int(self.headers.get("Content-Length") or 0)
        try:
            bericht = json.loads(self.rfile.read(lengte) or b"{}")
        except json.JSONDecodeError:
            return self._antwoord(400, {"fout": "geen JSON"})
        ONTVANGEN.append({"ontvangen": datetime.now(timezone.utc).isoformat(), "notificatie": bericht})
        print(f"notificatie: {bericht.get('kanaal')} {bericht.get('actie')} {bericht.get('resourceUrl')}", flush=True)
        return self._antwoord(204)

    def do_GET(self):
        pad = self.path.split("?")[0].rstrip("/")
        if pad == "/health":
            return self._antwoord(200, {"status": "ok"})
        if pad in ("", "/notificaties"):
            return self._antwoord(200, {"aantal": len(ONTVANGEN), "notificaties": list(ONTVANGEN)})
        return self._antwoord(404, {"fout": "onbekend pad"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
