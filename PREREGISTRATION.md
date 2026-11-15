# Pre-registration: simulated arm measurement

Written and committed before the simulated batch was run. The live arm is
out of scope for this registration: it runs only when the named approver
(Jesun) runs it himself, and no live numbers exist at the time of writing.

## Design

- Batch size: 240 requests (requirement: at least 200).
- Seed: 20261115. The run must be exactly reproducible from this seed.
- Request stream: the demo producer's class mix (read_only 0.35,
  data_write 0.25, external_send 0.15, financial 0.10, destructive 0.10,
  system_config 0.05), templates as shipped in src/hitl_gate/producer.py.
- Policy: the shipped policy.toml (read_only auto; data_write,
  external_send, financial human; destructive deny; unknown classes fall
  back to human).
- Simulated approver, stated in full in src/hitl_gate/simulate.py:
  approval probability by class (data_write 0.90, external_send 0.80,
  financial 0.70, system_config 0.85); response delay lognormal with
  per-class median seconds (data_write 30, external_send 60, financial 120,
  system_config 45) and sigma 0.6; submissions every 5 virtual seconds
  from 2026-11-15T00:00:00Z.

## Metrics to report in RESULTS.md

- Routing accuracy: share of requests whose recorded route equals the
  route the policy prescribes, recomputed independently after the run.
  Expected value 1.0; this is a correctness check on the engine, and any
  value below 1.0 is a bug to report, not to round up.
- Decision latency percentiles (p50, p90, p99) for human-routed requests,
  from the drawn delays as recorded in the log.
- Auto-approve rate, escalation rate (human-routed share), deny rate.
- Approval rate among human-decided requests.
- Status counts for every terminal state.

## Labelling rule

Every number from this arm is labelled SIMULATED wherever it appears.
Simulated numbers describe the scripted approver only. They are not
evidence about human decision behaviour, and RESULTS.md must say so.
