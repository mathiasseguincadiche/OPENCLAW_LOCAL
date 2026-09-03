from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def default_root() -> Path:
    value = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if value:
        return Path(value)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def _activate_repository_runtime() -> None:
    platform_root = default_root()
    if os.name == "nt":
        managed = platform_root / "runtime" / "venv" / "Scripts" / "python.exe"
        if managed.is_file() and Path(sys.executable).resolve() != managed.resolve():
            os.execv(
                str(managed),
                [str(managed), str(Path(__file__).resolve()), *sys.argv[1:]],
            )

    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    os.environ.setdefault("OPENCLAW_LOCAL_REPO_ROOT", str(repo_root))


def main() -> int:
    _activate_repository_runtime()

    from clawlocal.golden_projects import (
        SCENARIOS,
        evaluate_golden_project,
        execute_golden_project,
        prepare_golden_project,
    )

    parser = argparse.ArgumentParser(description="Prépare et exécute les golden projects pré-V1.")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    selected = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    failures: list[str] = []
    for scenario_id in selected:
        project = args.root / "projects" / f"golden-{scenario_id}"
        if args.prepare:
            project = prepare_golden_project(args.root, scenario_id, reset=args.reset)
            print(f"PREPARED {scenario_id}: {project}")
        if args.execute:
            if not project.exists():
                project = prepare_golden_project(args.root, scenario_id, reset=args.reset)
            project = execute_golden_project(repo_root, args.root, scenario_id)
            print(f"EXECUTED {scenario_id}: {project}")
        if args.evaluate:
            if not project.exists():
                failures.append(f"{scenario_id}: projet absent; utiliser --prepare")
                continue
            scenario_failures = evaluate_golden_project(project, scenario_id)
            if scenario_failures:
                failures.extend(scenario_failures)
            else:
                print(f"PASS {scenario_id}")

    if not any((args.prepare, args.execute, args.evaluate)):
        for scenario_id, spec in SCENARIOS.items():
            print(f"{scenario_id}: {spec['title']}")
        return 0
    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
