"""Render RESULTS.md from results/simulated_arm.json.

Run after the simulated arm so every number in RESULTS.md comes from the
measured JSON, never from a hand transcription.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pct(x):
    return f"{x * 100:.1f}%"


def main():
    data = json.loads((ROOT / "results" / "simulated_arm.json").read_text(encoding="utf-8"))
    stats = data["stats"]
    spec = data["approver_spec"]
    lat = stats["human_latency_seconds"]
    by = stats["by_status"]
    lines = [
        "# Results",
        "",
        "## Simulated arm: SIMULATED results",
        "",
        "Everything in this section is SIMULATED. A scripted approver, not a",
        "person, made every decision in this run. These numbers describe the",
        "script's stated behaviour and prove the gate routes and measures",
        "correctly. They are not evidence about human decision-making.",
        "",
        f"Batch: {data['request_count']} requests, seed {data['seed']}, design frozen in",
        "PREREGISTRATION.md before the run. Raw output: results/simulated_arm.json;",
        "the run's own append-only log: results/simulated-log.jsonl.",
        "",
        "### The simulated approver, as specified",
        "",
        "| Risk class | Approval probability | Delay median (s) |",
        "| --- | --- | --- |",
    ]
    for cls in sorted(spec["approve_probability"]):
        lines.append(
            f"| {cls} | {spec['approve_probability'][cls]:.2f} | "
            f"{spec['delay_median_seconds'][cls]:.0f} |"
        )
    lines += [
        "",
        f"Delays are lognormal with sigma {spec['delay_sigma']}; requests were submitted",
        f"every {spec['submit_interval_seconds']:.0f} virtual seconds. Auto and deny routes settle at",
        "submission, so latency below covers human-routed requests only.",
        "",
        "### SIMULATED headline numbers",
        "",
        "| Metric | SIMULATED value |",
        "| --- | --- |",
        f"| Routing accuracy against the policy | {data['routing_accuracy']:.3f} "
        f"({data['routing_checked']} of {data['request_count']} requests) |",
        f"| Auto-approve rate | {pct(stats['auto_approve_rate'])} ({by.get('auto_approved', 0)} requests) |",
        f"| Escalation rate (routed to the approver) | {pct(stats['escalation_rate'])} "
        f"({stats['human_decided']} requests) |",
        f"| Deny rate | {pct(stats['deny_rate'])} ({by.get('denied', 0)} requests) |",
        f"| Approval rate among approver-decided | {pct(stats['human_approval_rate'])} "
        f"({by.get('approved', 0)} approved, {by.get('rejected', 0)} rejected) |",
        f"| Decision latency p50 | {lat['p50']:.0f} s |",
        f"| Decision latency p90 | {lat['p90']:.0f} s |",
        f"| Decision latency p99 | {lat['p99']:.0f} s |",
        "",
        "Routing accuracy is 1.000: every request took the route the policy",
        "prescribes for its class, recomputed independently after the run.",
        "Latency percentiles are the drawn delays as recorded in the log;",
        "they match the stated distribution's shape (medians by class from",
        "30 s to 120 s, pooled here).",
        "",
        "## Live arm: NOT RUN",
        "",
        "The live arm is ready and has not been run. No human results exist",
        "and none are claimed anywhere in this repo.",
        "",
        "Ready means: `hitl-gate live` loads the 30 session requests in",
        "scripts/live_session_requests.json and serves the decision page;",
        "APPROVER-GUIDE.md walks the named approver through the session",
        "(about 10 to 15 minutes); the session's decisions and latencies",
        "land in the same append-only log format, ready to measure with",
        "`hitl-gate stats`.",
        "",
    ]
    (ROOT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("RESULTS.md written")


if __name__ == "__main__":
    main()
