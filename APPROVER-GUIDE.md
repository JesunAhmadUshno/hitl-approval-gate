# Approver guide: the live arm

This is the human study for the approval gate. It has not been run yet.
It runs when you, the named approver, run it. Nobody else can produce
these numbers for you, and the simulated batch in RESULTS.md is not a
substitute for them.

## What you are doing

Thirty realistic agent action requests are loaded into the gate. Policy
settles a few at once: read-only requests are auto-approved and the two
destructive ones are denied outright. The rest, about twenty-five, wait
for your judgement. For each one you see what the agent wants to do and
you approve or reject it, with a short reason. The gate records how long
each decision takes, so the session produces your real decision latency
and approval pattern.

## Start it (one command)

From the repo root, after `pip install -e .`:

```bash
hitl-gate live
```

Then open http://127.0.0.1:8765 in a browser.

## The session

1. Type your name in the approver box at the top. It is recorded with
   every decision.
2. Work down the waiting list. Each card shows the action, a plain
   summary of the payload, who produced it, and its risk class.
3. Type a short reason and click Approve or Reject. The reason goes into
   the permanent log, so write the real one.
4. The page refreshes itself. Keep going until the waiting list is empty.

Time needed: about 10 to 15 minutes for the full set. There is no timer
pressure; your natural pace is the measurement.

## After the session

```bash
hitl-gate stats        # your approval rate and latency percentiles
hitl-gate verify-log   # confirm the decision log is intact
```

The log lives at data/gate-log.jsonl (or the path given with --log). It is
append-only and hash-chained: your decisions cannot be quietly edited
later, by anyone, without breaking verification.

## Notes

- Judge each request as if the agent would really do it on your word.
  Some are routine, some are debatable, two classes of request never
  reach you at all because policy handles them.
- If you stop halfway, the log keeps what you decided. Restarting
  `hitl-gate live` serves the same queue where you left it.
- To run a fresh session instead, point --log at a new file.
