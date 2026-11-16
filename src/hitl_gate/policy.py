"""Policy engine: maps a request's risk class to a route.

Routes are "auto" (approve at once), "human" (wait for a person), and
"deny" (refuse at once). The policy lives in one readable TOML file so the
gate's behaviour can be reviewed and changed without touching code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROUTES = ("auto", "human", "deny")


@dataclass(frozen=True)
class Policy:
    class_routes: dict = field(default_factory=dict)
    default_route: str = "human"

    def route_for(self, risk_class: str) -> str:
        """Return the route the policy prescribes for a risk class."""
        return self.class_routes.get(risk_class, self.default_route)


def _check_route(route, where):
    """Validate one route value read from the policy file.

    Called for every route at load time, so a typo in policy.toml fails
    fast with a named location instead of silently misrouting requests.
    """
    if route not in ROUTES:
        raise ValueError(f"invalid route for {where}: {route!r} (expected one of {ROUTES})")
    return route


def load_policy(path) -> Policy:
    """Load a policy from a TOML file."""
    with open(Path(path), "rb") as fh:
        raw = tomllib.load(fh)
    routes = {}
    for name, spec in raw.get("classes", {}).items():
        routes[name] = _check_route(spec.get("route"), f"class {name}")
    default = _check_route(raw.get("default_route", "human"), "default_route")
    return Policy(class_routes=routes, default_route=default)


def default_policy() -> Policy:
    """The policy shipped in policy.toml at the repo root, as data."""
    return Policy(
        class_routes={
            "read_only": "auto",
            "data_write": "human",
            "external_send": "human",
            "financial": "human",
            "destructive": "deny",
        },
        default_route="human",
    )
