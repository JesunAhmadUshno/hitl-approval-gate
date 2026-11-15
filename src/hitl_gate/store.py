"""The gate itself: submit, route, decide, and report.

State is rebuilt by replaying the append-only log on startup, so the log is
the single source of truth and separate CLI invocations share state through
it. A clock function is injected so measurements can run on a virtual clock
(the simulated arm) while the live tool uses real time.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .log import AppendOnlyLog


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def percentile(values, pct: float) -> float:
    """Nearest-rank percentile. Returns 0.0 for an empty list."""
    if not values:
        return 0.0
    import math

    ordered = sorted(values)
    # nearest-rank: ceil(pct * n), with pct given as a fraction
    rank = max(1, math.ceil(pct * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


class GateStore:
    def __init__(self, policy, log_path, clock=None):
        self.policy = policy
        self.log = AppendOnlyLog(log_path)
        self.clock = clock or utc_now_iso
        self.requests = {}
        self._counter = 0
        self._replay()

    def _replay(self):
        for rec in self.log.records():
            event, data = rec["event"], rec["data"]
            if event == "request_submitted":
                self._counter += 1
                self.requests[data["id"]] = dict(data, status="pending")
            elif event in ("auto_approved", "denied_by_policy", "decision"):
                req = self.requests.get(data["id"])
                if req is not None:
                    req.update(
                        status=data["status"],
                        decided_at=data["decided_at"],
                        decided_by=data["decided_by"],
                        reason=data.get("reason", ""),
                    )

    def submit(self, producer, action_type, risk_class, payload_summary) -> dict:
        """Record a request and route it through the policy."""
        self._counter += 1
        req_id = f"req-{self._counter:04d}"
        created = self.clock()
        route = self.policy.route_for(risk_class)
        request = {
            "id": req_id,
            "created_at": created,
            "producer": producer,
            "action_type": action_type,
            "risk_class": risk_class,
            "payload_summary": payload_summary,
            "route": route,
            "status": "pending",
            "decided_at": None,
            "decided_by": None,
            "reason": "",
        }
        self.log.append(
            "request_submitted",
            {k: request[k] for k in ("id", "created_at", "producer", "action_type",
                                     "risk_class", "payload_summary", "route")},
            created,
        )
        self.requests[req_id] = request
        if route == "auto":
            self._settle(request, "auto_approved", "auto_approved", "policy", "auto route")
        elif route == "deny":
            self._settle(request, "denied_by_policy", "denied", "policy", "deny route")
        return request

    def _settle(self, request, event, status, decided_by, reason):
        decided_at = self.clock()
        data = {
            "id": request["id"],
            "status": status,
            "decided_at": decided_at,
            "decided_by": decided_by,
            "reason": reason,
        }
        self.log.append(event, data, decided_at)
        request.update(status=status, decided_at=decided_at,
                       decided_by=decided_by, reason=reason)

    def decide(self, request_id, decision, approver, reason="") -> dict:
        """Apply a human decision to a pending request."""
        if decision not in ("approve", "reject"):
            raise ValueError(f"decision must be approve or reject, got {decision!r}")
        request = self.requests.get(request_id)
        if request is None:
            raise KeyError(f"unknown request: {request_id}")
        if request["status"] != "pending":
            raise ValueError(f"request {request_id} is already {request['status']}")
        status = "approved" if decision == "approve" else "rejected"
        self._settle(request, "decision", status, approver, reason)
        return request

    def pending(self):
        return [r for r in self.requests.values() if r["status"] == "pending"]

    def all_requests(self):
        return list(self.requests.values())

    def stats(self) -> dict:
        """Counts, rates, and decision latency percentiles from the log state."""
        reqs = self.all_requests()
        total = len(reqs)
        by_status = {}
        for r in reqs:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        human_lat = [
            (_parse(r["decided_at"]) - _parse(r["created_at"])).total_seconds()
            for r in reqs
            if r["route"] == "human" and r["decided_at"]
        ]
        decided_human = by_status.get("approved", 0) + by_status.get("rejected", 0)
        return {
            "total": total,
            "by_status": by_status,
            "auto_approve_rate": (by_status.get("auto_approved", 0) / total) if total else 0.0,
            "escalation_rate": (
                (sum(1 for r in reqs if r["route"] == "human") / total) if total else 0.0
            ),
            "deny_rate": (by_status.get("denied", 0) / total) if total else 0.0,
            "human_decided": decided_human,
            "human_approval_rate": (
                (by_status.get("approved", 0) / decided_human) if decided_human else 0.0
            ),
            "human_latency_seconds": {
                "count": len(human_lat),
                "p50": percentile(human_lat, 0.50),
                "p90": percentile(human_lat, 0.90),
                "p99": percentile(human_lat, 0.99),
            },
        }
