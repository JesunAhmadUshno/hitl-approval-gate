import pytest

from hitl_gate.policy import Policy, default_policy, load_policy


def test_default_policy_routes():
    policy = default_policy()
    assert policy.route_for("read_only") == "auto"
    assert policy.route_for("data_write") == "human"
    assert policy.route_for("external_send") == "human"
    assert policy.route_for("financial") == "human"
    assert policy.route_for("destructive") == "deny"


def test_unknown_class_falls_back_to_default():
    assert default_policy().route_for("system_config") == "human"
    strict = Policy(class_routes={}, default_route="deny")
    assert strict.route_for("anything") == "deny"


def test_load_policy_from_repo_file(tmp_path):
    path = tmp_path / "p.toml"
    path.write_text(
        'default_route = "deny"\n\n[classes.safe]\nroute = "auto"\n',
        encoding="utf-8",
    )
    policy = load_policy(path)
    assert policy.route_for("safe") == "auto"
    assert policy.route_for("other") == "deny"


def test_load_policy_rejects_bad_route(tmp_path):
    path = tmp_path / "p.toml"
    path.write_text('[classes.x]\nroute = "maybe"\n', encoding="utf-8")
    with pytest.raises(ValueError):
        load_policy(path)


def test_shipped_policy_file_matches_default_policy():
    from pathlib import Path

    repo_policy = load_policy(Path(__file__).resolve().parents[1] / "policy.toml")
    assert repo_policy.class_routes == default_policy().class_routes
    assert repo_policy.default_route == default_policy().default_route
