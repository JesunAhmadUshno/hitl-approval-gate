# Results

## Simulated arm: SIMULATED results

Everything in this section is SIMULATED. A scripted approver, not a
person, made every decision in this run. These numbers describe the
script's stated behaviour and prove the gate routes and measures
correctly. They are not evidence about human decision-making.

Batch: 240 requests, seed 20261115, design frozen in
PREREGISTRATION.md before the run. Raw output: results/simulated_arm.json;
the run's own append-only log: results/simulated-log.jsonl.

### The simulated approver, as specified

| Risk class | Approval probability | Delay median (s) |
| --- | --- | --- |
| data_write | 0.90 | 30 |
| external_send | 0.80 | 60 |
| financial | 0.70 | 120 |
| system_config | 0.85 | 45 |

Delays are lognormal with sigma 0.6; requests were submitted
every 5 virtual seconds. Auto and deny routes settle at
submission, so latency below covers human-routed requests only.

### SIMULATED headline numbers

| Metric | SIMULATED value |
| --- | --- |
| Routing accuracy against the policy | 1.000 (240 of 240 requests) |
| Auto-approve rate | 35.4% (85 requests) |
| Escalation rate (routed to the approver) | 51.7% (124 requests) |
| Deny rate | 12.9% (31 requests) |
| Approval rate among approver-decided | 86.3% (107 approved, 17 rejected) |
| Decision latency p50 | 52 s |
| Decision latency p90 | 133 s |
| Decision latency p99 | 239 s |

Routing accuracy is 1.000: every request took the route the policy
prescribes for its class, recomputed independently after the run.
Latency percentiles are the drawn delays as recorded in the log;
they match the stated distribution's shape (medians by class from
30 s to 120 s, pooled here).

## Live arm: NOT RUN

The live arm is ready and has not been run. No human results exist
and none are claimed anywhere in this repo.

Ready means: `hitl-gate live` loads the 30 session requests in
scripts/live_session_requests.json and serves the decision page;
APPROVER-GUIDE.md walks the named approver through the session
(about 10 to 15 minutes); the session's decisions and latencies
land in the same append-only log format, ready to measure with
`hitl-gate stats`.
