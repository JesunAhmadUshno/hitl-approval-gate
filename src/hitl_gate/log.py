"""Append-only event log with a hash chain.

Every request and every decision is one JSON line. Each record carries the
hash of the previous record, so editing or deleting any earlier line breaks
the chain and is detected by verify(). Records are never updated or removed
through this API: the only write operation is append.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def _record_hash(record_without_hash) -> str:
    payload = json.dumps(record_without_hash, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AppendOnlyLog:
    def __init__(self, path):
        self.path = Path(path)
        self._seq = 0
        self._prev = GENESIS
        if self.path.exists():
            for rec in self.records():
                self._seq = rec["seq"]
                self._prev = rec["hash"]

    def append(self, event: str, data: dict, ts: str) -> dict:
        """Append one event and return the stored record."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "seq": self._seq + 1,
            "ts": ts,
            "event": event,
            "data": data,
            "prev": self._prev,
        }
        record["hash"] = _record_hash(record)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            fh.flush()
        self._seq = record["seq"]
        self._prev = record["hash"]
        return record

    def records(self):
        """Yield every record in order. Missing file means no records."""
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)


def verify_log(path):
    """Check the hash chain. Returns (ok, message)."""
    path = Path(path)
    if not path.exists():
        return False, f"log file not found: {path}"
    prev = GENESIS
    expected_seq = 1
    count = 0
    for rec in AppendOnlyLog(path).records():
        count += 1
        if rec.get("seq") != expected_seq:
            return False, f"sequence gap at record {count}: seq {rec.get('seq')} != {expected_seq}"
        if rec.get("prev") != prev:
            return False, f"broken chain at record {count}: prev hash does not match record {count - 1}"
        body = {k: v for k, v in rec.items() if k != "hash"}
        if _record_hash(body) != rec.get("hash"):
            return False, f"hash mismatch at record {count}: contents were altered after writing"
        prev = rec["hash"]
        expected_seq += 1
    return True, f"chain intact: {count} records verified"
