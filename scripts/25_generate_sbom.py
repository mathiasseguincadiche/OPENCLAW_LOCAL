from __future__ import annotations

import argparse
import importlib.metadata
import json
import tomllib
import uuid
from pathlib import Path
from typing import Any


def _dependency_name(requirement: str) -> str:
    for marker in (">", "<", "=", "!", "~", " ", ";", "["):
        requirement = requirement.split(marker, 1)[0]
    return requirement.strip()


def build_sbom(root: Path) -> dict[str, Any]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    name = str(project["name"])
    version = str(project["version"])
    root_ref = f"pkg:pypi/{name}@{version}"

    components: list[dict[str, Any]] = []
    dependency_refs: list[str] = []
    for requirement in project.get("dependencies", []):
        dep_name = _dependency_name(str(requirement))
        try:
            dep_version = importlib.metadata.version(dep_name)
        except importlib.metadata.PackageNotFoundError:
            dep_version = "unknown"
        dep_ref = f"pkg:pypi/{dep_name.lower()}@{dep_version}"
        dependency_refs.append(dep_ref)
        components.append(
            {
                "type": "library",
                "name": dep_name,
                "version": dep_version,
                "bom-ref": dep_ref,
                "purl": dep_ref,
            }
        )

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, root_ref)}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": name,
                "version": version,
                "bom-ref": root_ref,
                "purl": root_ref,
            }
        },
        "components": components,
        "dependencies": [
            {"ref": root_ref, "dependsOn": dependency_refs},
            *({"ref": ref, "dependsOn": []} for ref in dependency_refs),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère le SBOM CycloneDX de la release.")
    parser.add_argument("--output", type=Path, default=Path("dist/sbom.cdx.json"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sbom = build_sbom(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sbom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
