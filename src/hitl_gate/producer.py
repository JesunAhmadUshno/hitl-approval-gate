"""Demo producer: a realistic stream of agent action requests.

Each entry is (action_type, risk_class, payload_summary), written the way an
agent runtime would describe work it wants to do. The mix covers every route
in the default policy, plus one class the policy does not list, which falls
back to the default route.
"""

from __future__ import annotations

import random

TEMPLATES = [
    # read_only: auto route
    ("file.read", "read_only", "Read config file settings.toml before planning the run"),
    ("file.list", "read_only", "List the contents of the reports directory"),
    ("web.fetch", "read_only", "Fetch a public documentation page for the API reference"),
    ("metrics.query", "read_only", "Query the local metrics store for yesterday's counts"),
    ("db.select", "read_only", "Run a read-only SELECT on the local analytics database"),
    # data_write: human route
    ("file.write", "data_write", "Write the daily summary into notes/daily-summary.md"),
    ("tracker.update", "data_write", "Mark three finished tasks as done in the tracker"),
    ("db.insert", "data_write", "Insert 42 parsed rows into the local analytics database"),
    ("file.append", "data_write", "Append the run receipt to the project log file"),
    # external_send: human route
    ("email.send", "external_send", "Send the draft status update to the collaborator"),
    ("chat.post", "external_send", "Post the build result to the team channel"),
    ("calendar.invite", "external_send", "Create a calendar invite for the review meeting"),
    ("social.post", "external_send", "Publish the prepared announcement post"),
    # financial: human route
    ("payment.charge", "financial", "Charge the card on file for this month's API credits"),
    ("payment.refund", "financial", "Refund 25.00 for the cancelled order"),
    ("funds.transfer", "financial", "Transfer the payout balance to the operating account"),
    # destructive: deny route
    ("file.delete", "destructive", "Delete the off-site backup archive"),
    ("db.drop", "destructive", "Drop the sessions table in the analytics database"),
    ("token.revoke_all", "destructive", "Revoke every API token on the account"),
    ("disk.format", "destructive", "Format the attached external drive"),
    # system_config: not in the default policy, falls back to the default route
    ("system.config", "system_config", "Change the machine timezone to America/Toronto"),
    ("package.install", "system_config", "Install a system package from the OS repository"),
]

# Class mix used by the demo and by the simulated arm's pre-registered design.
CLASS_MIX = {
    "read_only": 0.35,
    "data_write": 0.25,
    "external_send": 0.15,
    "financial": 0.10,
    "destructive": 0.10,
    "system_config": 0.05,
}


def _by_class():
    grouped = {}
    for action_type, risk_class, summary in TEMPLATES:
        grouped.setdefault(risk_class, []).append((action_type, summary))
    return grouped


def generate_stream(count: int, seed: int, producer_name: str = "demo-agent"):
    """Yield request dicts in a reproducible class mix."""
    rng = random.Random(seed)
    grouped = _by_class()
    classes = list(CLASS_MIX)
    weights = [CLASS_MIX[c] for c in classes]
    for _ in range(count):
        risk_class = rng.choices(classes, weights=weights, k=1)[0]
        action_type, summary = rng.choice(grouped[risk_class])
        yield {
            "producer": producer_name,
            "action_type": action_type,
            "risk_class": risk_class,
            "payload_summary": summary,
        }
