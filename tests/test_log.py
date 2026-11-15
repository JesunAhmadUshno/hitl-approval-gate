from hitl_gate.log import AppendOnlyLog, verify_log

TS = "2026-11-15T00:00:00+00:00"


def _make_log(path, n=5):
    log = AppendOnlyLog(path)
    for i in range(n):
        log.append("event", {"i": i}, TS)
    return log


def test_append_and_verify(tmp_path):
    path = tmp_path / "log.jsonl"
    _make_log(path)
    ok, message = verify_log(path)
    assert ok, message


def test_chain_links_records(tmp_path):
    path = tmp_path / "log.jsonl"
    log = _make_log(path, 3)
    records = list(log.records())
    assert records[0]["prev"] == "0" * 64
    assert records[1]["prev"] == records[0]["hash"]
    assert records[2]["prev"] == records[1]["hash"]
    assert [r["seq"] for r in records] == [1, 2, 3]


def test_tampered_record_breaks_verification(tmp_path):
    path = tmp_path / "log.jsonl"
    _make_log(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[2] = lines[2].replace('"i": 2', '"i": 99')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, message = verify_log(path)
    assert not ok
    assert "record 3" in message


def test_deleted_record_breaks_verification(tmp_path):
    path = tmp_path / "log.jsonl"
    _make_log(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, _ = verify_log(path)
    assert not ok


def test_reopen_continues_chain(tmp_path):
    path = tmp_path / "log.jsonl"
    _make_log(path, 2)
    log = AppendOnlyLog(path)
    rec = log.append("event", {"i": 2}, TS)
    assert rec["seq"] == 3
    ok, _ = verify_log(path)
    assert ok


def test_missing_file_fails_verification(tmp_path):
    ok, _ = verify_log(tmp_path / "nope.jsonl")
    assert not ok
