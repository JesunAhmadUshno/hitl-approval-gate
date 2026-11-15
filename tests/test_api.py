import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from hitl_gate.policy import default_policy
from hitl_gate.server import make_handler
from hitl_gate.store import GateStore


@pytest.fixture()
def base_url(tmp_path):
    store = GateStore(default_policy(), tmp_path / "gate.jsonl")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, threading.Lock()))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def call(base, method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def test_submit_auto_class(base_url):
    status, body = call(base_url, "POST", "/api/requests", {
        "producer": "test", "action_type": "file.read",
        "risk_class": "read_only", "payload_summary": "Read a config"})
    assert status == 201
    assert body["status"] == "auto_approved"


def test_submit_then_decide_over_http(base_url):
    _, body = call(base_url, "POST", "/api/requests", {
        "producer": "test", "action_type": "email.send",
        "risk_class": "external_send", "payload_summary": "Send a draft"})
    assert body["status"] == "pending"
    status, decided = call(base_url, "POST", f"/api/requests/{body['id']}/decision", {
        "decision": "approve", "approver": "jesun", "reason": "checked"})
    assert status == 200
    assert decided["status"] == "approved"


def test_submit_missing_field_is_400(base_url):
    status, _ = call(base_url, "POST", "/api/requests", {"action_type": "x"})
    assert status == 400


def test_decide_unknown_is_400(base_url):
    status, _ = call(base_url, "POST", "/api/requests/req-9999/decision",
                     {"decision": "approve", "approver": "jesun"})
    assert status == 400


def test_stats_and_verify_endpoints(base_url):
    call(base_url, "POST", "/api/requests", {
        "producer": "test", "action_type": "file.read",
        "risk_class": "read_only", "payload_summary": "Read a config"})
    status, stats = call(base_url, "GET", "/api/stats")
    assert status == 200 and stats["total"] == 1
    status, verify = call(base_url, "GET", "/api/log/verify")
    assert status == 200 and verify["ok"] is True


def test_decision_page_served(base_url):
    req = urllib.request.Request(base_url + "/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
    assert resp.status == 200
    assert "Approval Gate" in html
