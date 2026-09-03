from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "49_run_golden_projects.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("golden_runner_cli", RUNNER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_root_is_resolved_before_runtime_activation(tmp_path: Path) -> None:
    runner = _load_runner()
    selected = runner.requested_root(
        ["--scenario", "all", "--root", str(tmp_path), "--execute"]
    )
    assert selected == tmp_path


def test_default_root_remains_available_when_root_is_not_explicit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runner = _load_runner()
    monkeypatch.setenv("OPENCLAW_LOCAL_ROOT", str(tmp_path))
    assert runner.requested_root(["--scenario", "all"]) == tmp_path
