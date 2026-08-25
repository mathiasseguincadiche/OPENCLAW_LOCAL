from __future__ import annotations

from clawlocal.config import load_contract


def test_eight_roles_have_routes() -> None:
    roles = load_contract("role_matrix.yaml")["roles"]
    routes = load_contract("model_routing.yaml")["agents"]
    assert len(roles) == 8
    assert set(roles) == set(routes)


def test_cloud_defaults_to_disabled() -> None:
    routing = load_contract("model_routing.yaml")
    platform = load_contract("platform.yaml")
    assert routing["cloud_enabled_by_default"] is False
    assert platform["cloud"]["enabled_by_default"] is False


def test_local_provider_is_loopback() -> None:
    platform = load_contract("platform.yaml")
    assert platform["local_provider"]["base_url"].startswith("http://127.0.0.1:")
