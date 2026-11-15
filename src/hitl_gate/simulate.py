"""The simulated arm: a scripted stand-in approver, measured honestly.

This module exists so the gate's routing and measurement can be exercised
before a real person sits down. The approver here is NOT a human. Its
behaviour is fully specified below and in PREREGISTRATION.md:

- For each human-routed request it approves with a fixed probability that
  depends on the risk class (APPROVE_PROBABILITY).
- Its response delay is drawn from a lognormal distribution with a
  per-class median in seconds and a shared sigma (DELAY_MEDIAN_SECONDS,
  DELAY_SIGMA), using a seeded random generator, so runs are reproducible.
- Requests are submitted on a virtual clock, one every SUBMIT_INTERVAL
  seconds, and decisions land at submit time plus the drawn delay.

Every number this module produces is a simulated number and is labelled
SIMULATED in RESULTS.md and in the JSON it writes. It says nothing about
how a real approver would behave.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from .producer import generate_stream
from .store import GateStore

APPROVE_PROBABILITY = {
    "data_write": 0.90,
    "external_send": 0.80,
    "financial": 0.70,
    "system_config": 0.85,
}
DEFAULT_APPROVE_PROBABILITY = 0.85

DELAY_MEDIAN_SECONDS = {
    "data_write": 30.0,
    "external_send": 60.0,
    "financial": 120.0,
    "system_config": 45.0,
}
DEFAULT_DELAY_MEDIAN_SECONDS = 45.0
DELAY_SIGMA = 0.6

SUBMIT_INTERVAL_SECONDS = 5.0
VIRTUAL_START = datetime(2026, 11, 15, 0, 0, 0, tzinfo=timezone.utc)


class VirtualClock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> str:
        return self.now.isoformat(timespec="seconds")

    def advance(self, seconds: float):
        self.now += timedelta(seconds=seconds)


def _draw_delay(rng: random.Random, risk_class: str) -> float:
    median = DELAY_MEDIAN_SECONDS.get(risk_class, DEFAULT_DELAY_MEDIAN_SECONDS)
    return rng.lognormvariate(math.log(median), DELAY_SIGMA)


def run_simulation(policy, log_path, count: int, seed: int) -> dict:
    """Run one simulated batch and return the measured results."""
    rng = random.Random(seed)
    clock = VirtualClock(VIRTUAL_START)
    store = GateStore(policy, log_path, clock=clock)

    submitted = []
    for item in generate_stream(count, seed):
        req = store.submit(**item)
        submitted.append(req["id"])
        clock.advance(SUBMIT_INTERVAL_SECONDS)

    # The simulated approver works through the pending queue in order.
    for req in store.pending():
        delay = _draw_delay(rng, req["risk_class"])
        # Decision time is the request creation time plus the drawn delay.
        created = datetime.fromisoformat(req["created_at"])
        decision_time = created + timedelta(seconds=delay)
        clock.now = max(clock.now, decision_time)
        prob = APPROVE_PROBABILITY.get(req["risk_class"], DEFAULT_APPROVE_PROBABILITY)
        decision = "approve" if rng.random() < prob else "reject"
        store.clock = lambda dt=decision_time: dt.isoformat(timespec="seconds")
        store.decide(req["id"], decision, approver="simulated-approver",
                     reason="scripted simulated decision")
    store.clock = clock

    # Routing accuracy: an independent recheck of every request's route
    # against what the policy prescribes for its class.
    correct = sum(
        1 for r in store.all_requests() if r["route"] == policy.route_for(r["risk_class"])
    )
    stats = store.stats()
    results = {
        "arm": "SIMULATED",
        "warning": "All numbers in this file come from a scripted simulated approver. "
                   "No human decided anything in this run.",
        "seed": seed,
        "request_count": count,
        "approver_spec": {
            "approve_probability": APPROVE_PROBABILITY,
            "default_approve_probability": DEFAULT_APPROVE_PROBABILITY,
            "delay_distribution": "lognormal",
            "delay_median_seconds": DELAY_MEDIAN_SECONDS,
            "default_delay_median_seconds": DEFAULT_DELAY_MEDIAN_SECONDS,
            "delay_sigma": DELAY_SIGMA,
            "submit_interval_seconds": SUBMIT_INTERVAL_SECONDS,
        },
        "routing_accuracy": correct / len(submitted) if submitted else 0.0,
        "routing_checked": len(submitted),
        "stats": stats,
    }
    return results
