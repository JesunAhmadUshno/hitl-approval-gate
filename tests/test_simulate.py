from hitl_gate.log import verify_log
from hitl_gate.policy import default_policy
from hitl_gate.simulate import run_simulation


def test_simulated_arm_small_batch(tmp_path):
    log_path = tmp_path / "sim.jsonl"
    results = run_simulation(default_policy(), log_path, count=40, seed=99)
    assert results["arm"] == "SIMULATED"
    assert results["request_count"] == 40
    assert results["routing_accuracy"] == 1.0
    stats = results["stats"]
    assert stats["total"] == 40
    assert stats["by_status"].get("pending", 0) == 0
    assert 0.0 < stats["auto_approve_rate"] < 1.0
    assert stats["human_latency_seconds"]["count"] > 0
    ok, _ = verify_log(log_path)
    assert ok


def test_simulated_arm_is_reproducible(tmp_path):
    first = run_simulation(default_policy(), tmp_path / "a.jsonl", count=40, seed=5)
    second = run_simulation(default_policy(), tmp_path / "b.jsonl", count=40, seed=5)
    assert first["stats"] == second["stats"]
