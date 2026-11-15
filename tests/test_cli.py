import json

from hitl_gate.cli import main


def run_cli(tmp_path, capsys, *argv):
    log = tmp_path / "gate.jsonl"
    code = main(["--log", str(log), *argv])
    out = capsys.readouterr().out
    return code, out, log


def test_submit_pending_decide_flow(tmp_path, capsys):
    code, out, _ = run_cli(tmp_path, capsys, "submit", "--action-type", "file.write",
                           "--risk-class", "data_write", "--summary", "Write notes")
    assert code == 0
    req = json.loads(out)
    assert req["status"] == "pending"

    code, out, _ = run_cli(tmp_path, capsys, "pending")
    assert code == 0
    assert len(json.loads(out)) == 1

    code, out, _ = run_cli(tmp_path, capsys, "decide", req["id"], "approve",
                           "--approver", "jesun", "--reason", "fine")
    assert code == 0
    assert json.loads(out)["status"] == "approved"

    code, out, _ = run_cli(tmp_path, capsys, "stats")
    assert code == 0
    assert json.loads(out)["human_approval_rate"] == 1.0


def test_verify_log_command(tmp_path, capsys):
    run_cli(tmp_path, capsys, "submit", "--action-type", "file.read",
            "--risk-class", "read_only", "--summary", "Read a config")
    code, out, _ = run_cli(tmp_path, capsys, "verify-log")
    assert code == 0
    assert "chain intact" in out


def test_decide_unknown_returns_error(tmp_path, capsys):
    code, _, _ = run_cli(tmp_path, capsys, "decide", "req-9999", "approve")
    assert code == 1


def test_demo_command(tmp_path, capsys):
    code, out, _ = run_cli(tmp_path, capsys, "demo", "--count", "20", "--seed", "3")
    assert code == 0
    assert json.loads(out)["total"] == 20
