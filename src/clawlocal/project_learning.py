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


def _profile_payload(profile: str, mode: str) -> dict[str, Any]:
    policy = learning_policy()
    profiles = policy.get("profiles", {})
    modes = set(policy.get("modes", []))
    if profile not in profiles:
        raise ValueError(f"profil pédagogique inconnu: {profile}")
    if mode not in modes:
        raise ValueError(f"mode pédagogique inconnu: {mode}")
    return {
        "schema_version": "1.1.0",
        "profile": profile,
        "mode": mode,
        "delivery_priority": bool(policy.get("delivery_priority", True)),
        **profiles[profile],
    }


def _contract_path(project: Path) -> Path:
    return project / "context" / "learning" / "LEARNING_CONTRACT.json"


def _read_contract(project: Path) -> dict[str, Any]:
    path = _contract_path(project)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("LEARNING_CONTRACT.json invalide")
    return payload


def _write_contract(project: Path, payload: dict[str, Any]) -> Path:
    path = _contract_path(project)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def set_learning_profile(project: Path, *, profile: str, mode: str) -> Path:
    root = project / "context" / "learning"
    if not root.is_dir():
        raise FileNotFoundError(root)
    payload = _profile_payload(profile, mode)
    path = root / "learning_profile.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    contract = _read_contract(project)
    contract["profile"] = profile
    contract["mode"] = mode
    contract["evaluation_required"] = mode == "evaluation"
    contract["updated_at"] = _now()
    _write_contract(project, contract)
    return path


def initialize_learning(
    project: Path,
    *,
    profile: str | None = None,
    mode: str | None = None,
    preserve_existing: bool = False,
) -> None:
    policy = learning_policy()
    selected_profile = profile or str(policy.get("default_profile", "balanced"))
    selected_mode = mode or str(policy.get("default_mode", "assisted"))
    _profile_payload(selected_profile, selected_mode)

    root = project / "context" / "learning"
    root.mkdir(parents=True, exist_ok=True)
    defaults = {
        "SKILLS_MATRIX.csv": "skill,status,evidence,last_review,next_review\n",
        "LEARNING_JOURNAL.md": (
            "# Journal d'apprentissage\n\nLa livraison reste prioritaire. Une entrée est ajoutée "
            "uniquement lorsqu'un apprentissage utile mérite d'être conservé.\n\n"
        ),
        "TEACH_BACK.md": (
            "# Teach-back ciblé\n\nÀ utiliser aux jalons importants pour expliquer avec ses "
            "propres mots le concept, son utilité, son risque et une preuve pratique.\n"
        ),
    }
    for name, content in defaults.items():
        path = root / name
        if not preserve_existing or not path.exists():
            path.write_text(content, encoding="utf-8")
    retention = root / "RETENTION_PLAN.yaml"
    if not preserve_existing or not retention.exists():
        retention.write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.1.0",
                    "policy": "targeted_only",
                    "default_intervals_days": [7, 30],
                    "items": [],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    evaluations = root / "evaluations"
    evaluations.mkdir(exist_ok=True)
    readme = evaluations / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Évaluations d'autonomie\n\nActivées uniquement pour une soutenance, "
            "une évaluation ou un jalon explicitement décidé.\n",
            encoding="utf-8",
        )
    contract_path = _contract_path(project)
    if not preserve_existing or not contract_path.exists():
        _write_contract(
            project,
            {
                "schema_version": "1.0.0",
                "profile": selected_profile,
                "mode": selected_mode,
                "objectives": [],
                "target_skills": [],
                "evidence": [],
                "evaluation_required": selected_mode == "evaluation",
                "verdict": "NON_EVALUE",
                "technical_verdict_is_separate": True,
                "updated_at": _now(),
            },
        )
    profile_path = root / "learning_profile.json"
    if not preserve_existing or not profile_path.exists():
        profile_path.write_text(
            json.dumps(_profile_payload(selected_profile, selected_mode), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    access = accessibility_policy()
    document_profile = {
        "schema_version": "1.1.0",
        "mode": access.get("default_mode", "universal_progressive"),
        "reading_depths": access.get("reading_depths", []),
        "principles": access.get("principles", {}),
        "role_responsibilities": access.get("role_responsibilities", {}),
        "audit_checklist": access.get("audit_checklist", []),
        "proportionality_factors": access.get("proportionality_factors", []),
    }
    doc_path = project / "context" / "documentation_profile.json"
    if not preserve_existing or not doc_path.exists():
        doc_path.write_text(
            json.dumps(document_profile, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def add_learning_objective(project: Path, *, objective: str, skill: str | None = None) -> None:
    contract = _read_contract(project)
    objectives = contract.setdefault("objectives", [])
    if objective not in objectives:
        objectives.append(objective)
    if skill:
        skills = contract.setdefault("target_skills", [])
        if skill not in skills:
            skills.append(skill)
    contract["updated_at"] = _now()
    _write_contract(project, contract)


def record_learning_evidence(project: Path, *, evidence: str) -> None:
    contract = _read_contract(project)
    values = contract.setdefault("evidence", [])
    values.append({"at": _now(), "evidence": evidence.strip()})
    contract["updated_at"] = _now()
    _write_contract(project, contract)


def set_learning_verdict(project: Path, verdict: str) -> None:
    allowed = set(learning_policy().get("learning_verdicts", []))
    if verdict not in allowed:
        raise ValueError(f"verdict pédagogique invalide: {verdict}")
    contract = _read_contract(project)
    contract["verdict"] = verdict
    contract["updated_at"] = _now()
    _write_contract(project, contract)


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
    record_learning_evidence(project, evidence=evidence)


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
    if status == "ACQUIRED" and not evidence.strip():
        raise ValueError("une compétence ACQUIRED exige une preuve pratique")

    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows.extend(dict(row) for row in reader)
    now = _now()
    updated = False
    for row in rows:
        if row.get("skill") == skill:
            row.update(status=status, evidence=evidence, last_review=now, next_review=next_review)
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
            fieldnames=["skill", "status", "evidence", "last_review", "next_review"],
        )
        writer.writeheader()
        writer.writerows(rows)
