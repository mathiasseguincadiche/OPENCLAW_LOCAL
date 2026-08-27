from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from clawlocal.config import load_contract

_VALID_PROFILES = {"efficient", "balanced", "intensive"}
_VALID_SKILL_STATUS = {"OBSERVED", "PRACTICING", "VALIDATED", "ACQUIRED"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _profile_contract(profile: str) -> dict[str, Any]:
    policy = load_contract("pedagogy_policy.yaml")
    profiles = policy.get("profiles", {})
    if profile not in _VALID_PROFILES or profile not in profiles:
        raise ValueError(f"profil pédagogique inconnu: {profile}")
    selected = profiles[profile]
    if not isinstance(selected, dict):
        raise ValueError(f"profil pédagogique invalide: {profile}")
    return selected


def _guidance_text(profile: str) -> str:
    accessibility = load_contract("accessibility_policy.yaml")
    selected = _profile_contract(profile)
    depths = accessibility.get("reading_depths", [])
    depth_lines = []
    for item in depths:
        if not isinstance(item, dict):
            continue
        depth_lines.append(
            f"- **{item.get('label', item.get('id', ''))}** : "
            + ", ".join(str(value) for value in item.get("content", []))
        )

    return (
        "# Guidance projet\n\n"
        "Ce fichier est généré par OPENCLAW_LOCAL et fait partie du contexte contractuel.\n\n"
        "## Profil pédagogique\n\n"
        f"- profil : `{profile}`\n"
        f"- exécution : {selected.get('execution_share_percent')} %\n"
        f"- apprentissage : {selected.get('learning_share_percent')} %\n"
        f"- objectifs d'apprentissage maximum : {selected.get('max_learning_objectives')}\n"
        f"- finalité : {selected.get('purpose')}\n\n"
        "La livraison reste prioritaire. Ne crée pas de quiz systématique, ne duplique pas "
        "la documentation et ne marque jamais une compétence acquise sur simple exposition.\n\n"
        "## Documentation progressive\n\n"
        "Pour les documents explicatifs, utiliser les profondeurs suivantes lorsqu'elles "
        "sont pertinentes. Un format de livrable imposé reste prioritaire.\n\n"
        + "\n".join(depth_lines)
        + "\n\n"
        "Toujours privilégier l'exactitude technique, les prérequis explicites, les preuves "
        "et le rollback lorsqu'il est pertinent.\n"
    )


def initialize_learning_context(project: Path, profile: str = "balanced") -> Path:
    selected = _profile_contract(profile)
    root = project / "context" / "learning"
    root.mkdir(parents=True, exist_ok=True)

    _write_json(
        root / "profile.json",
        {
            "schema_version": "1.0.0",
            "profile": profile,
            "mode": "assisted",
            "execution_share_percent": int(selected["execution_share_percent"]),
            "learning_share_percent": int(selected["learning_share_percent"]),
            "max_learning_objectives": int(selected["max_learning_objectives"]),
            "updated_at": _now(),
        },
    )

    skills = root / "SKILLS_MATRIX.csv"
    if not skills.exists():
        skills.write_text(
            "skill,status,evidence,last_review,next_review\n",
            encoding="utf-8",
        )

    journal = root / "LEARNING_JOURNAL.md"
    if not journal.exists():
        journal.write_text(
            "# Journal d'apprentissage\n\n"
            "Conserver uniquement les apprentissages utiles au projet et leurs preuves.\n",
            encoding="utf-8",
        )

    teach_back = root / "TEACH_BACK.md"
    if not teach_back.exists():
        teach_back.write_text(
            "# Teach-back ciblé\n\n"
            "- Concept expliqué avec ses propres mots :\n"
            "- Pourquoi il est utile dans le projet :\n"
            "- Risque ou limite principale :\n"
            "- Exemple ou commande réellement utilisé :\n",
            encoding="utf-8",
        )

    retention = root / "RETENTION_PLAN.yaml"
    if not retention.exists():
        retention.write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0.0",
                    "policy": "targeted_only",
                    "default_intervals_days": [7, 30],
                    "items": [],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    guidance = project / "context" / "PROJECT_GUIDANCE.md"
    guidance.write_text(_guidance_text(profile), encoding="utf-8")
    return root


def set_learning_profile(project: Path, profile: str) -> Path:
    return initialize_learning_context(project, profile)


def record_learning(
    project: Path,
    *,
    skill: str,
    status: str,
    evidence: str = "",
    note: str = "",
    human_validated: bool = False,
) -> None:
    normalized_status = status.strip().upper()
    if normalized_status not in _VALID_SKILL_STATUS:
        raise ValueError(f"statut de compétence inconnu: {status}")
    if normalized_status == "ACQUIRED" and not human_validated:
        raise PermissionError(
            "ACQUIRED exige une validation humaine ou une évaluation explicitement attestée"
        )
    skill_name = skill.strip()
    if not skill_name:
        raise ValueError("skill vide")

    root = project / "context" / "learning"
    if not root.is_dir():
        initialize_learning_context(project)

    matrix = root / "SKILLS_MATRIX.csv"
    rows: list[dict[str, str]] = []
    if matrix.exists():
        with matrix.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

    now = _now()
    found = False
    for row in rows:
        if row.get("skill") == skill_name:
            row["status"] = normalized_status
            row["evidence"] = evidence
            row["last_review"] = now
            found = True
            break
    if not found:
        rows.append(
            {
                "skill": skill_name,
                "status": normalized_status,
                "evidence": evidence,
                "last_review": now,
                "next_review": "",
            }
        )

    with matrix.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["skill", "status", "evidence", "last_review", "next_review"],
        )
        writer.writeheader()
        writer.writerows(rows)

    journal = root / "LEARNING_JOURNAL.md"
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {now} — {skill_name}\n\n"
            f"- Statut : `{normalized_status}`\n"
            f"- Preuve : {evidence or 'non renseignée'}\n"
            f"- Note : {note or 'non renseignée'}\n"
        )
