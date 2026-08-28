from __future__ import annotations

import sys
from pathlib import Path

import clawlocal.config as config
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


def test_repository_root_uses_explicit_runtime_contract(monkeypatch, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fake_module = tmp_path / "venv" / "Lib" / "site-packages" / "clawlocal" / "config.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.write_text("# installed package placeholder\n", encoding="utf-8")

    monkeypatch.setattr(config, "__file__", str(fake_module))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["python"])
    monkeypatch.setenv("OPENCLAW_LOCAL_REPO_ROOT", str(repo_root))

    assert config.repository_root() == repo_root


def test_repository_root_recovers_from_repo_script_when_package_is_installed(
    monkeypatch, tmp_path: Path
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fake_module = tmp_path / "venv" / "Lib" / "site-packages" / "clawlocal" / "config.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.write_text("# installed package placeholder\n", encoding="utf-8")

    monkeypatch.delenv("OPENCLAW_LOCAL_REPO_ROOT", raising=False)
    monkeypatch.setattr(config, "__file__", str(fake_module))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(repo_root / "scripts" / "20_list_models.py")])

    assert config.repository_root() == repo_root
    assert load_contract("model_catalog.yaml")["models"]
