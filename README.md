# hitl-approval-gate

A human-in-the-loop approval gate for agent actions. Agents ask before they
act; a policy decides what is safe to auto-approve, what a person must
judge, and what is refused outright. Every request and every decision is
written to an append-only, hash-chained log, so the full decision history
is auditable and decision latency is measurable.

## Why

Autonomous agents are useful exactly where they are dangerous: sending,
spending, deleting. This tool puts one narrow, reviewable checkpoint in
front of those actions. It is deliberately small: one policy file, one log
file, a CLI, a tiny HTTP API, and a single web page for the human.

## The policy model

Each request carries a risk class. The policy (policy.toml, plain TOML)
maps classes to routes:

| Route | Meaning |
| --- | --- |
| auto | Approved at once. No human involved. |
| human | Waits in the queue until a person approves or rejects it, with a reason. |
| deny | Refused at once. No one can approve it through this gate. |

Default policy: read_only is auto; data_write, external_send, and financial
are human; destructive is deny; any unlisted class falls back to human.
Change the TOML file and the gate follows it. Nothing else needs editing.

## Pieces

- Producers submit requests through the CLI or the HTTP API
  (POST /api/requests).
- Humans decide on the web page served by the tool, or by CLI
  (hitl-gate decide).
- The log (JSON lines) records submissions and decisions with timestamps.
  Each record carries the previous record's hash; hitl-gate verify-log
  detects any later edit or deletion.
- A demo producer generates a realistic stream of agent requests across
  all classes.

## Run it

Install: `pip install -e .` (Python 3.11 or newer, no runtime dependencies
beyond the standard library).

```bash
hitl-gate serve                 # API and decision page on http://127.0.0.1:8765
hitl-gate submit --action-type email.send --risk-class external_send --summary "Send the draft update"
hitl-gate pending               # what is waiting for a human
hitl-gate decide req-0003 approve --approver jesun --reason "draft checked"
hitl-gate stats                 # counts, rates, latency percentiles
hitl-gate verify-log            # hash chain check
hitl-gate demo --count 40       # demo producer stream into the log
```

## The two measurement arms

Simulated arm (already run, numbers in RESULTS.md): a scripted approver
with stated approval probabilities and stated response-delay distributions
decides a 240-request batch on a virtual clock. It exercises the routing
and the measurement end to end. Every number from this arm is labelled
SIMULATED. It is not a human study and says nothing about how a person
would decide.

```bash
hitl-gate simulate --count 240 --seed 20261115
```

Live arm (ready, not yet run): one command loads 30 realistic requests and
serves the decision page for the named approver to judge in one sitting.
See APPROVER-GUIDE.md.

```bash
hitl-gate live
```

## Claims ceiling

This is a portfolio tool built to a research standard: pre-registered
measurement design, a tested policy engine, and an auditable log. The
simulated arm's numbers describe a script, not a person. The human study
exists only when the named approver runs the live arm; until then there
are no human results to report, and this repo reports none.

## Layout

- src/hitl_gate/policy.py: the policy engine
- src/hitl_gate/log.py: the append-only hash-chained log
- src/hitl_gate/store.py: submit, route, decide, stats
- src/hitl_gate/server.py: HTTP API and decision page
- src/hitl_gate/cli.py: the hitl-gate command
- src/hitl_gate/producer.py: the demo request stream
- src/hitl_gate/simulate.py: the simulated arm, approver spec included
- scripts/live_session_requests.json: the 30 live-arm requests
- tests/: policy routing, log integrity, store, API, CLI, simulated arm

## License

Apache-2.0. See LICENSE.
