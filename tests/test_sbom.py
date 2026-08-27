from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_sbom_module() -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "25_generate_sbom.py"
    spec = importlib.util.spec_from_file_location("generate_sbom", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sbom_is_cyclonedx_and_contains_runtime_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    module = _load_sbom_module()
    sbom = module.build_sbom(root)

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert sbom["metadata"]["component"]["name"] == "clawlocal"
    assert any(component["name"].lower() == "pyyaml" for component in sbom["components"])
