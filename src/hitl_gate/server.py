"""Tiny HTTP API plus the human decision page, standard library only.

Endpoints:
  POST /api/requests                 submit a request (producer side)
  GET  /api/requests                 list requests, optional ?status= filter
  POST /api/requests/<id>/decision   {decision, approver, reason}
  GET  /api/stats                    counts, rates, latency percentiles
  GET  /api/log/verify               hash chain check
  GET  /                               the decision page
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .log import verify_log

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Approval Gate</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 860px; padding: 0 1rem; background: #0b0e14; color: #e6e6e6; }
  h1 { font-size: 1.4rem; }
  .meta { color: #9aa4b2; font-size: 0.9rem; }
  .card { border: 1px solid #2a3242; border-radius: 8px; padding: 1rem; margin: 0.8rem 0; background: #12161f; }
  .cls { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px; background: #1d2635; font-size: 0.8rem; }
  .row { display: flex; gap: 0.5rem; margin-top: 0.6rem; flex-wrap: wrap; }
  button { border: 0; border-radius: 6px; padding: 0.45rem 0.9rem; cursor: pointer; font-size: 0.95rem; }
  .ok { background: #1f7a3d; color: #fff; }
  .no { background: #8c2f2f; color: #fff; }
  input[type=text] { background: #0b0e14; color: #e6e6e6; border: 1px solid #2a3242; border-radius: 6px; padding: 0.45rem; flex: 1; min-width: 180px; }
  .done { opacity: 0.65; }
  #stats { white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 0.85rem; background: #12161f; border: 1px solid #2a3242; border-radius: 8px; padding: 1rem; }
</style>
</head>
<body>
<h1>Approval Gate</h1>
<p class="meta">Requests routed to a human wait here. Approve or reject each one, with a reason. Every decision is written to the append-only log.</p>
<p><label>Your name: <input type="text" id="approver" placeholder="approver name" style="flex:none"></label></p>
<h2>Waiting for a decision</h2>
<div id="pending"></div>
<h2>Stats</h2>
<div id="stats">loading</div>
<h2>Recent decisions</h2>
<div id="recent"></div>
<script>
async function load() {
  const res = await fetch('/api/requests');
  const reqs = await res.json();
  const pending = reqs.filter(r => r.status === 'pending');
  const decided = reqs.filter(r => r.status !== 'pending').slice(-10).reverse();
  const box = document.getElementById('pending');
  box.innerHTML = pending.length ? '' : '<p class="meta">Nothing is waiting.</p>';
  for (const r of pending) {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = '<span class="cls">' + r.risk_class + '</span> <b>' + r.action_type + '</b>' +
      '<p>' + r.payload_summary + '</p>' +
      '<p class="meta">from ' + r.producer + ' at ' + r.created_at + ' (' + r.id + ')</p>';
    const row = document.createElement('div');
    row.className = 'row';
    const reason = document.createElement('input');
    reason.type = 'text'; reason.placeholder = 'reason (recorded in the log)';
    const ok = document.createElement('button'); ok.className = 'ok'; ok.textContent = 'Approve';
    const no = document.createElement('button'); no.className = 'no'; no.textContent = 'Reject';
    ok.onclick = () => decide(r.id, 'approve', reason.value);
    no.onclick = () => decide(r.id, 'reject', reason.value);
    row.append(reason, ok, no);
    div.append(row);
    box.append(div);
  }
  const rec = document.getElementById('recent');
  rec.innerHTML = decided.map(r =>
    '<div class="card done"><span class="cls">' + r.status + '</span> <b>' + r.action_type + '</b>' +
    '<p>' + r.payload_summary + '</p><p class="meta">by ' + (r.decided_by || '') + ': ' + (r.reason || '') + '</p></div>').join('');
  const s = await (await fetch('/api/stats')).json();
  document.getElementById('stats').textContent = JSON.stringify(s, null, 2);
}
async function decide(id, decision, reason) {
  const approver = document.getElementById('approver').value || 'web-approver';
  await fetch('/api/requests/' + id + '/decision', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({decision, approver, reason})
  });
  load();
}
load();
setInterval(load, 5000);
</script>
</body>
</html>
"""


def make_handler(store, lock):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the console quiet
            pass

        def _send(self, code, body, content_type="application/json"):
            raw = body if isinstance(body, bytes) else json.dumps(body).encode()
            if content_type != "application/json":
                raw = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            if not length:
                return {}
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if parsed.path == "/api/requests":
                status = parse_qs(parsed.query).get("status", [None])[0]
                with lock:
                    reqs = store.all_requests()
                if status:
                    reqs = [r for r in reqs if r["status"] == status]
                return self._send(200, reqs)
            if parsed.path == "/api/stats":
                with lock:
                    return self._send(200, store.stats())
            if parsed.path == "/api/log/verify":
                ok, message = verify_log(store.log.path)
                return self._send(200, {"ok": ok, "message": message})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/requests":
                data = self._body()
                missing = [k for k in ("action_type", "risk_class", "payload_summary")
                           if not data.get(k)]
                if missing:
                    return self._send(400, {"error": f"missing fields: {missing}"})
                with lock:
                    req = store.submit(
                        producer=data.get("producer", "api"),
                        action_type=data["action_type"],
                        risk_class=data["risk_class"],
                        payload_summary=data["payload_summary"],
                    )
                return self._send(201, req)
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "requests" and parts[3] == "decision":
                data = self._body()
                try:
                    with lock:
                        req = store.decide(
                            parts[2],
                            data.get("decision", ""),
                            data.get("approver", "web-approver"),
                            data.get("reason", ""),
                        )
                except (KeyError, ValueError) as exc:
                    return self._send(400, {"error": str(exc)})
                return self._send(200, req)
            return self._send(404, {"error": "not found"})

    return Handler


def serve(store, host="127.0.0.1", port=8765):
    lock = threading.Lock()
    server = ThreadingHTTPServer((host, port), make_handler(store, lock))
    print(f"approval gate serving on http://{host}:{port} (log: {store.log.path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
