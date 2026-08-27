from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from clawlocal.config import load_contract


def _now() -> str:
    return datetime.now(UTC).isoformat()


def learning_policy() -> dict[str, Any]:
    return load_contract("pedagogy_policy.yaml")


def accessibility_policy() -> dict[str, Any]:
    return load_contract("accessibility_policy.yaml")


def initialize_learning(
    project: Path,
    *,
    profile: str | None = None,
    mode: str | None = None,
) -> None:
    policy = learning_policy()
    selected_profile = profile or str(policy.get("default_profile", "balanced"))
    selected_mode = mode or str(policy.get("default_mode", "assisted"))
    profiles = policy.get("profiles", {})
    modes = set(policy.get("modes", []))
    if selected_profile not in profiles:
        raise ValueError(f"profil pédagogique inconnu: {selected_profile}")
    if selected_mode not in modes:
        raise ValueError(f"mode pédagogique inconnu: {selected_mode}")

    root = project / "context" / "learning"
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILLS_MATRIX.csv").write_text(
        "skill,status,evidence,last_review,next_review\n",
        encoding="utf-8",
    )
    (root / "LEARNING_JOURNAL.md").write_text(
        "# Journal d'apprentissage\n\n"
        "La livraison reste prioritaire. Une entrée est ajoutée uniquement lorsqu'un "
        "apprentissage utile mérite d'être conservé.\n\n",
        encoding="utf-8",
    )
    (root / "TEACH_BACK.md").write_text(
        "# Teach-back ciblé\n\n"
        "À utiliser aux jalons importants pour expliquer avec ses propres mots :\n\n"
        "- le concept ;\n"
        "- son utilité dans le projet ;\n"
        "- sa principale limite ou son risque ;\n"
        "- une preuve pratique réellement observée.\n",
        encoding="utf-8",
    )
    retention = {
        "schema_version": "1.0.0",
        "policy": "targeted_only",
        "default_intervals_days": [7, 30],
        "items": [],
    }
    (root / "RETENTION_PLAN.yaml").write_text(
        yaml.safe_dump(retention, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    profile_payload = {
        "schema_version": "1.0.0",
        "profile": selected_profile,
        "mode": selected_mode,
        "delivery_priority": bool(policy.get("delivery_priority", True)),
        **profiles[selected_profile],
    }
    (root / "learning_profile.json").write_text(
        json.dumps(profile_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    access = accessibility_policy()
    document_profile = {
        "schema_version": "1.0.0",
        "mode": access.get("default_mode", "universal_progressive"),
        "reading_depths": access.get("reading_depths", []),
        "principles": access.get("principles", {}),
    }
    (project / "context" / "documentation_profile.json").write_text(
        json.dumps(document_profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_learning_entry(
    project: Path,
    *,
    title: str,
    understanding: str,
    evidence: str,
    next_step: str | None = None,
) -> None:
    journal = project / "context" / "learning" / "LEARNING_JOURNAL.md"
    if not journal.is_file():
        raise FileNotFoundError(journal)
    entry = [
        f"## {_now()} — {title.strip()}",
        "",
        f"- Compréhension acquise : {understanding.strip()}",
        f"- Preuve pratique : {evidence.strip()}",
    ]
    if next_step:
        entry.append(f"- Prochaine étape : {next_step.strip()}")
    entry.append("")
    with journal.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry) + "\n")


def update_skill(
    project: Path,
    *,
    skill: str,
    status: str,
    evidence: str,
    next_review: str = "",
) -> None:
    path = project / "context" / "learning" / "SKILLS_MATRIX.csv"
    if not path.is_file():
        raise FileNotFoundError(path)
    allowed = {"NOT_STARTED", "IN_PROGRESS", "ACQUIRED", "TO_REINFORCE"}
    if status not in allowed:
        raise ValueError(f"statut compétence invalide: {status}")

    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows.extend(dict(row) for row in reader)

    now = _now()
    updated = False
    for row in rows:
        if row.get("skill") == skill:
            row.update(
                status=status,
                evidence=evidence,
                last_review=now,
                next_review=next_review,
            )
            updated = True
            break
    if not updated:
        rows.append(
            {
                "skill": skill,
                "status": status,
                "evidence": evidence,
                "last_review": now,
                "next_review": next_review,
            }
        )

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "skill",
                "status",
                "evidence",
                "last_review",
                "next_review",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
