"""Command line interface for the approval gate.

Examples:
  hitl-gate serve                     serve the API and the decision page
  hitl-gate submit --action-type file.read --risk-class read_only --summary "Read a config"
  hitl-gate pending                   list requests waiting for a human
  hitl-gate decide req-0003 approve --approver jesun --reason "checked the draft"
  hitl-gate stats                     counts, rates, latency percentiles
  hitl-gate verify-log                check the append-only hash chain
  hitl-gate demo --count 40           run the demo producer stream
  hitl-gate simulate --count 240      run the SIMULATED arm (no human involved)
  hitl-gate live                      load the live session and serve the page
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .log import verify_log
from .policy import load_policy
from .producer import generate_stream
from .server import serve
from .simulate import run_simulation
from .store import GateStore

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "policy.toml"
DEFAULT_SESSION = REPO_ROOT / "scripts" / "live_session_requests.json"


def _store(args) -> GateStore:
    policy = load_policy(args.policy)
    return GateStore(policy, args.log)


def _print_json(obj):
    print(json.dumps(obj, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hitl-gate", description=__doc__)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY), help="policy TOML file")
    parser.add_argument("--log", default="data/gate-log.jsonl", help="append-only log file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("serve", help="serve the HTTP API and decision page").add_argument(
        "--port", type=int, default=8765)
    sub.choices["serve"].add_argument("--host", default="127.0.0.1")

    p_submit = sub.add_parser("submit", help="submit one action request")
    p_submit.add_argument("--producer", default="cli")
    p_submit.add_argument("--action-type", required=True)
    p_submit.add_argument("--risk-class", required=True)
    p_submit.add_argument("--summary", required=True)

    sub.add_parser("pending", help="list requests waiting for a human")

    p_decide = sub.add_parser("decide", help="approve or reject a pending request")
    p_decide.add_argument("request_id")
    p_decide.add_argument("decision", choices=["approve", "reject"])
    p_decide.add_argument("--approver", default="cli-approver")
    p_decide.add_argument("--reason", default="")

    sub.add_parser("stats", help="show counts, rates, and latency percentiles")
    sub.add_parser("verify-log", help="verify the append-only hash chain")

    p_demo = sub.add_parser("demo", help="run the demo producer stream")
    p_demo.add_argument("--count", type=int, default=40)
    p_demo.add_argument("--seed", type=int, default=7)

    p_sim = sub.add_parser("simulate", help="run the SIMULATED arm (scripted approver)")
    p_sim.add_argument("--count", type=int, default=240)
    p_sim.add_argument("--seed", type=int, default=20261115)
    p_sim.add_argument("--out", default="results/simulated_arm.json")
    p_sim.add_argument("--sim-log", default="results/simulated-log.jsonl",
                       help="the simulated arm always writes to its own log")

    p_live = sub.add_parser("live", help="load the live session requests and serve")
    p_live.add_argument("--session", default=str(DEFAULT_SESSION))
    p_live.add_argument("--port", type=int, default=8765)
    p_live.add_argument("--host", default="127.0.0.1")

    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(_store(args), host=args.host, port=args.port)
        return 0

    if args.command == "live":
        store = _store(args)
        if not store.all_requests():
            session = json.loads(Path(args.session).read_text(encoding="utf-8"))
            for item in session["requests"]:
                store.submit(**item)
            print(f"loaded {len(session['requests'])} session requests into {args.log}")
        print("Open the decision page, work through the queue, then run: hitl-gate stats")
        serve(store, host=args.host, port=args.port)
        return 0

    if args.command == "submit":
        req = _store(args).submit(args.producer, args.action_type,
                                  args.risk_class, args.summary)
        _print_json(req)
        return 0

    if args.command == "pending":
        _print_json(_store(args).pending())
        return 0

    if args.command == "decide":
        try:
            req = _store(args).decide(args.request_id, args.decision,
                                      args.approver, args.reason)
        except (KeyError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        _print_json(req)
        return 0

    if args.command == "stats":
        _print_json(_store(args).stats())
        return 0

    if args.command == "verify-log":
        ok, message = verify_log(args.log)
        print(message)
        return 0 if ok else 1

    if args.command == "demo":
        store = _store(args)
        for item in generate_stream(args.count, args.seed):
            store.submit(**item)
        _print_json(store.stats())
        return 0

    if args.command == "simulate":
        policy = load_policy(args.policy)
        results = run_simulation(policy, args.sim_log, args.count, args.seed)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"SIMULATED arm complete: {args.count} requests, results in {out}")
        _print_json(results["stats"])
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
