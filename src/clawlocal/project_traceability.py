from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.project_ingestion import load_ingestion_index

_REQ_RE = re.compile(r"^REQ-[0-9]{3,5}$")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON invalide: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _text(value: Any) -> str:
    if isinstance(value, dict):
        for key in (
            "statement",
            "description",
            "text",
            "objective",
            "name",
            "title",
        ):
            candidate = str(value.get(key, "")).strip()
            if candidate:
                return candidate
    return str(value).strip()


def normalize_analysis_requirements(
    project: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(payload)
    index = load_ingestion_index(project)
    known_documents = {
        str(entry.get("document_id"))
        for entry in index.get("entries", [])
        if isinstance(entry, dict) and entry.get("document_id")
    }
    raw_requirements = payload.get("requirements")
    explicit = isinstance(raw_requirements, list) and bool(raw_requirements)
    requirements: list[dict[str, Any]] = []

    if explicit:
        assert isinstance(raw_requirements, list)
        for position, raw in enumerate(raw_requirements, start=1):
            if not isinstance(raw, dict):
                raise ValueError(
                    "analyse: requirements doit contenir uniquement des objets"
                )
            requirement_id = str(raw.get("id") or f"REQ-{position:03d}").upper().strip()
            if not _REQ_RE.fullmatch(requirement_id):
                raise ValueError(f"analyse: requirement id invalide: {requirement_id}")
            statement = _text(raw)
            if not statement:
                raise ValueError(f"analyse: {requirement_id} sans statement")
            source_document_ids = raw.get("source_document_ids", [])
            source_refs = raw.get("source_refs", [])
            if not isinstance(source_document_ids, list) or any(
                not isinstance(item, str) for item in source_document_ids
            ):
                raise ValueError(
                    f"analyse: {requirement_id}.source_document_ids invalide"
                )
            if not isinstance(source_refs, list) or any(
                not isinstance(item, str) for item in source_refs
            ):
                raise ValueError(f"analyse: {requirement_id}.source_refs invalide")
            unknown_documents = sorted(set(source_document_ids) - known_documents)
            if unknown_documents:
                raise ValueError(
                    f"analyse: {requirement_id} référence des documents inconnus: "
                    + ", ".join(unknown_documents)
                )
            requirements.append(
                {
                    "id": requirement_id,
                    "statement": statement,
                    "type": str(raw.get("type", "functional")).strip()
                    or "functional",
                    "priority": str(raw.get("priority", "must")).strip() or "must",
                    "source_document_ids": sorted(set(source_document_ids)),
                    "source_refs": list(dict.fromkeys(source_refs)),
                    "acceptance_hint": str(raw.get("acceptance_hint", "")).strip(),
                }
            )
    else:
        counter = 0
        for category in ("objectives", "constraints", "deliverables"):
            values = payload.get(category, [])
            if not isinstance(values, list):
                continue
            for position, value in enumerate(values, start=1):
                statement = _text(value)
                if not statement:
                    continue
                counter += 1
                requirements.append(
                    {
                        "id": f"REQ-{counter:03d}",
                        "statement": statement,
                        "type": category.rstrip("s"),
                        "priority": "must",
                        "source_document_ids": [],
                        "source_refs": [
                            f"project_analysis.{category}[{position - 1}]"
                        ],
                        "acceptance_hint": "",
                    }
                )

    seen: set[str] = set()
    for item in requirements:
        requirement_id = str(item["id"])
        if requirement_id in seen:
            raise ValueError(f"analyse: requirement id dupliqué: {requirement_id}")
        seen.add(requirement_id)
    if not requirements:
        raise ValueError("analyse: aucune exigence traçable n'a pu être établie")

    normalized["requirements"] = requirements
    normalized["requirements_origin"] = (
        "explicit" if explicit else "derived_compatibility"
    )
    normalized["requirements_schema_version"] = "1.0.0"
    return normalized


def validate_plan_requirement_links(project: Path, plan: dict[str, Any]) -> None:
    analysis = _load_json(project / "context" / "project_analysis.json")
    requirements = analysis.get("requirements", [])
    known = {
        str(item.get("id"))
        for item in requirements
        if isinstance(item, dict) and item.get("id")
    }
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("plan: tasks invalide pour la traçabilité")
    mapped: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            continue
        refs = task.get("requirement_ids", [])
        if not isinstance(refs, list) or any(
            not isinstance(item, str) for item in refs
        ):
            raise ValueError(f"plan: {task.get('id', '?')}.requirement_ids invalide")
        unknown = sorted(set(refs) - known)
        if unknown:
            raise ValueError(
                f"plan: {task.get('id', '?')} référence des exigences inconnues: "
                + ", ".join(unknown)
            )
        mapped.update(refs)
    if analysis.get("requirements_origin") == "explicit":
        missing = sorted(known - mapped)
        if missing:
            raise ValueError(
                "plan: exigences non affectées à une tâche: " + ", ".join(missing)
            )


def _latest_results(project: Path) -> dict[str, dict[str, Any]]:
    path = project / "evidence" / "task_results.json"
    if not path.is_file():
        return {}
    payload = _load_json(path)
    latest: dict[str, dict[str, Any]] = {}
    for raw in payload.get("results", []):
        if not isinstance(raw, dict):
            continue
        task_id = str(raw.get("task_id", ""))
        if not task_id:
            continue
        previous = latest.get(task_id)
        if previous is None or int(raw.get("attempt", 0)) >= int(
            previous.get("attempt", 0)
        ):
            latest[task_id] = raw
    return latest


def refresh_traceability_matrix(project: Path) -> Path:
    analysis = _load_json(project / "context" / "project_analysis.json")
    plan_path = project / "context" / "project_plan.json"
    plan = _load_json(plan_path) if plan_path.is_file() else {"tasks": []}
    assignments_path = project / "context" / "task_assignments.json"
    assignments = (
        _load_json(assignments_path)
        if assignments_path.is_file()
        else {"tasks": []}
    )
    task_status = {
        str(item.get("task_id")): str(item.get("status", "PENDING"))
        for item in assignments.get("tasks", [])
        if isinstance(item, dict)
    }
    latest = _latest_results(project)
    tasks = [item for item in plan.get("tasks", []) if isinstance(item, dict)]

    rows: list[dict[str, Any]] = []
    for requirement in analysis.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        requirement_id = str(requirement.get("id", ""))
        linked = [
            task
            for task in tasks
            if requirement_id in task.get("requirement_ids", [])
        ]
        linked_ids = [str(task.get("id", "")) for task in linked]
        outputs: list[str] = []
        acceptance: list[str] = []
        evidence: list[str] = []
        observed_outputs: list[str] = []
        statuses: dict[str, str] = {}
        for task in linked:
            task_id = str(task.get("id", ""))
            outputs.extend(str(value) for value in task.get("expected_outputs", []))
            acceptance.extend(
                str(value) for value in task.get("acceptance_criteria", [])
            )
            statuses[task_id] = task_status.get(task_id, "PENDING")
            result = latest.get(task_id, {})
            evidence_file = str(result.get("evidence_file", "")).strip()
            if evidence_file:
                evidence.append(evidence_file)
            observed_outputs.extend(
                str(value) for value in result.get("collected_outputs", [])
            )
        if not linked:
            verdict = "UNMAPPED"
        elif any(status == "FAIL" for status in statuses.values()):
            verdict = "FAIL"
        elif statuses and all(status == "PASS" for status in statuses.values()):
            verdict = "PASS" if evidence or observed_outputs else "PASS_WITHOUT_EVIDENCE"
        else:
            verdict = "PENDING"
        rows.append(
            {
                "requirement_id": requirement_id,
                "statement": requirement.get("statement", ""),
                "sources": {
                    "document_ids": requirement.get("source_document_ids", []),
                    "refs": requirement.get("source_refs", []),
                },
                "tasks": linked_ids,
                "expected_outputs": list(dict.fromkeys(outputs)),
                "acceptance_criteria": list(dict.fromkeys(acceptance)),
                "observed_outputs": list(dict.fromkeys(observed_outputs)),
                "evidence": list(dict.fromkeys(evidence)),
                "task_statuses": statuses,
                "verdict": verdict,
            }
        )

    validation_path = project / "evidence" / "validation_report.json"
    review_path = project / "evidence" / "review_report.json"
    validation_verdict = (
        _load_json(validation_path).get("verdict")
        if validation_path.is_file()
        else None
    )
    review_verdict = (
        _load_json(review_path).get("verdict") if review_path.is_file() else None
    )
    payload = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "requirements_origin": analysis.get("requirements_origin", "unknown"),
        "rows": rows,
        "validation_verdict": validation_verdict,
        "review_verdict": review_verdict,
    }
    target = project / "context" / "traceability" / "requirements_matrix.json"
    _write_json(target, payload)

    md = [
        "# Matrice de traçabilité des exigences",
        "",
        "| Exigence | Tâches | Sorties observées | Preuves | Verdict |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        md.append(
            "| {req} | {tasks} | {outputs} | {evidence} | {verdict} |".format(
                req=str(row["requirement_id"]),
                tasks=", ".join(row["tasks"]) or "—",
                outputs=", ".join(row["observed_outputs"]) or "—",
                evidence=", ".join(row["evidence"]) or "—",
                verdict=str(row["verdict"]),
            )
        )
    report = target.parent / "REQUIREMENTS_TRACEABILITY.md"
    report.write_text("\n".join(md) + "\n", encoding="utf-8")
    return target


def traceability_failures(project: Path, *, require_completed: bool) -> list[str]:
    matrix_path = refresh_traceability_matrix(project)
    payload = _load_json(matrix_path)
    if payload.get("requirements_origin") != "explicit":
        return []
    failures: list[str] = []
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        verdict = str(row.get("verdict", ""))
        requirement_id = str(row.get("requirement_id", "?"))
        if verdict == "UNMAPPED":
            failures.append(f"{requirement_id}: aucune tâche associée")
        elif require_completed and verdict != "PASS":
            failures.append(
                f"{requirement_id}: verdict de traçabilité {verdict}, PASS requis"
            )
    return failures
