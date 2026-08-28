from __future__ import annotations

import argparse
from pathlib import Path

from clawlocal.project_web_evidence import project_web_evidence_failures
from clawlocal.web_evidence import validate_web_evidence_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Valide les preuves Web fraîches et corroborées OPENCLAW_LOCAL."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Fichier web_evidence.json à valider")
    group.add_argument("--project", type=Path, help="Racine d'un projet orchestré")
    parser.add_argument("--task-id", help="Identifiant attendu avec --file")
    parser.add_argument(
        "--require-runtime",
        action="store_true",
        help="Exige au moins une affirmation machine_verifiable avec preuve runtime PASS",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.file is not None:
        try:
            validate_web_evidence_file(
                args.file,
                expected_task_id=args.task_id,
                require_runtime=args.require_runtime,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"WEB_EVIDENCE=FAIL\nERROR={exc}")
            return 1
        print(f"WEB_EVIDENCE=PASS\nFILE={args.file.resolve()}")
        return 0

    project = args.project.resolve()
    failures = project_web_evidence_failures(project)
    if failures:
        print("WEB_EVIDENCE=FAIL")
        for failure in failures:
            print(f"ERROR={failure}")
        return 1
    print(f"WEB_EVIDENCE=PASS\nPROJECT={project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
