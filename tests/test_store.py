import pytest

from hitl_gate.policy import default_policy
from hitl_gate.store import GateStore


def make_store(tmp_path):
    return GateStore(default_policy(), tmp_path / "gate.jsonl")


def test_auto_route_settles_at_once(tmp_path):
    store = make_store(tmp_path)
    req = store.submit("agent", "file.read", "read_only", "Read a config")
    assert req["status"] == "auto_approved"
    assert req["decided_by"] == "policy"
    assert store.pending() == []


def test_deny_route_settles_at_once(tmp_path):
    store = make_store(tmp_path)
    req = store.submit("agent", "db.drop", "destructive", "Drop a table")
    assert req["status"] == "denied"


def test_human_route_waits_then_decides(tmp_path):
    store = make_store(tmp_path)
    req = store.submit("agent", "email.send", "external_send", "Send a draft")
    assert req["status"] == "pending"
    decided = store.decide(req["id"], "approve", "jesun", "draft checked")
    assert decided["status"] == "approved"
    assert decided["decided_by"] == "jesun"
    assert decided["reason"] == "draft checked"


def test_reject_path(tmp_path):
    store = make_store(tmp_path)
    req = store.submit("agent", "payment.charge", "financial", "Charge a card")
    decided = store.decide(req["id"], "reject", "jesun", "not this month")
    assert decided["status"] == "rejected"


def test_double_decision_rejected(tmp_path):
    store = make_store(tmp_path)
    req = store.submit("agent", "file.write", "data_write", "Write notes")
    store.decide(req["id"], "approve", "jesun", "")
    with pytest.raises(ValueError):
        store.decide(req["id"], "approve", "jesun", "")


def test_unknown_request_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(KeyError):
        store.decide("req-9999", "approve", "jesun", "")


def test_state_survives_reopen(tmp_path):
    path = tmp_path / "gate.jsonl"
    store = GateStore(default_policy(), path)
    req = store.submit("agent", "file.write", "data_write", "Write notes")
    store.decide(req["id"], "approve", "jesun", "fine")
    reopened = GateStore(default_policy(), path)
    assert reopened.requests[req["id"]]["status"] == "approved"
    assert reopened.stats()["total"] == 1


def test_stats_rates(tmp_path):
    store = make_store(tmp_path)
    store.submit("a", "file.read", "read_only", "r")
    store.submit("a", "db.drop", "destructive", "d")
    human = store.submit("a", "file.write", "data_write", "w")
    store.decide(human["id"], "approve", "jesun", "")
    stats = store.stats()
    assert stats["total"] == 3
    assert stats["auto_approve_rate"] == pytest.approx(1 / 3)
    assert stats["deny_rate"] == pytest.approx(1 / 3)
    assert stats["escalation_rate"] == pytest.approx(1 / 3)
    assert stats["human_approval_rate"] == 1.0
    assert stats["human_latency_seconds"]["count"] == 1
