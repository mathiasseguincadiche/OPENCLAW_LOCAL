from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.project_context import AGENT_IDS
from clawlocal.project_intake import validate_project_id

_TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
_ANALYSIS_REQUIRED = {
    "summary",
    "objectives",
    "constraints",
    "deliverables",
    "ambiguities",
    "missing_information",
    "risks",
    "decisions_required",
}
_VALID_VERDICTS = {"PASS", "FAIL"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON invalide: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def project_path(platform_root: Path, project_id: str) -> Path:
    normalized = validate_project_id(project_id)
    project = (platform_root / "projects" / normalized).resolve()
    projects_root = (platform_root / "projects").resolve()
    if project.parent != projects_root:
        raise ValueError("projet hors racine autorisée")
    if not (project / "project.json").is_file():
        raise FileNotFoundError(project / "project.json")
    return project


def load_project_manifest(project: Path) -> dict[str, Any]:
    return _load_json(project / "project.json")


def current_status(project: Path) -> str:
    return str(load_project_manifest(project).get("status", ""))


def _policy() -> dict[str, Any]:
    return load_contract("orchestration_policy.yaml")


def _artifact(project: Path, artifact_id: str) -> Path:
    artifacts = _policy().get("artifacts", {})
    relative = artifacts.get(artifact_id)
    if not relative:
        raise KeyError(f"artefact orchestration inconnu: {artifact_id}")
    return project / str(relative)


def _require_artifact(project: Path, artifact_id: str) -> dict[str, Any]:
    path = _artifact(project, artifact_id)
    if not path.is_file():
        raise ValueError(f"artefact requis absent: {path.relative_to(project)}")
    return _load_json(path)


def _normalize_question(value: Any) -> tuple[str, bool]:
    if isinstance(value, dict):
        text = str(
            value.get("question")
            or value.get("description")
            or value.get("text")
            or ""
        ).strip()
        blocking = bool(value.get("blocking", True))
        return text, blocking
    return str(value).strip(), True


def open_blocking_clarifications(project: Path) -> list[dict[str, Any]]:
    path = _artifact(project, "clarifications")
    if not path.is_file():
        return []
    payload = _load_json(path)
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError("clarifications.json: items doit être une liste")
    return [
        item
        for item in items
        if isinstance(item, dict)
        and item.get("blocking") is True
        and item.get("status") != "RESOLVED"
    ]


def _validation_verdict(project: Path, artifact_id: str) -> str:
    payload = _require_artifact(project, artifact_id)
    return str(payload.get("verdict", "")).upper()


def all_tasks_finished(project: Path) -> bool:
    assignments = _require_artifact(project, "assignments")
    tasks = assignments.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return False
    return all(
        isinstance(task, dict) and task.get("status") == "PASS"
        for task in tasks
    )


def _assert_transition_gates(
    project: Path,
    target: str,
    *,
    human_approved: bool,
) -> None:
    if target == "ANALYZED":
        _require_artifact(project, "analysis")
    elif target == "CLARIFICATION_REQUIRED":
        if not open_blocking_clarifications(project):
            raise ValueError("aucune clarification bloquante ouverte")
    elif target == "PLANNED":
        _require_artifact(project, "plan")
        if open_blocking_clarifications(project):
            raise ValueError("clarifications bloquantes non résolues")
    elif target in {"ASSIGNED", "IN_PROGRESS"}:
        _require_artifact(project, "assignments")
    elif target == "VALIDATING":
        if not all_tasks_finished(project):
            raise ValueError("toutes les tâches doivent être PASS avant validation")
    elif target == "REVIEW":
        if _validation_verdict(project, "validation") != "PASS":
            raise ValueError("validation PASS requise avant REVIEW")
    elif target == "PACKAGING":
        if _validation_verdict(project, "review") != "PASS":
            raise ValueError("review PASS requise avant PACKAGING")
    elif target == "COMPLETE":
        _require_artifact(project, "package_manifest")
        _require_artifact(project, "final_report")
        if not human_approved:
            raise PermissionError("validation humaine requise avant COMPLETE")


def transition_project(
    project: Path,
    target: str,
    *,
    actor: str,
    reason: str,
    human_approved: bool = False,
) -> dict[str, Any]:
    manifest = load_project_manifest(project)
    current = str(manifest.get("status", ""))
    policy = _policy()
    transitions = policy.get("transitions", {})
    allowed = transitions.get(current, [])
    if target not in allowed:
        raise ValueError(f"transition interdite: {current} -> {target}")

    _assert_transition_gates(project, target, human_approved=human_approved)

    now = _now()
    orchestration = manifest.setdefault(
        "orchestration",
        {
            "schema_version": "1.0.0",
            "started_at": now,
            "history": [],
        },
    )
    history = orchestration.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("project.json: orchestration.history invalide")
    history.append(
        {
            "at": now,
            "from": current,
            "to": target,
            "actor": actor,
            "reason": reason,
        }
    )
    orchestration["updated_at"] = now
    manifest["status"] = target
    manifest["updated_at"] = now
    _write_json(project / "project.json", manifest)
    return manifest


def store_analysis(project: Path, payload: dict[str, Any]) -> Path:
    missing = sorted(_ANALYSIS_REQUIRED - set(payload))
    if missing:
        raise ValueError(f"analyse incomplète: {', '.join(missing)}")
    for key in _ANALYSIS_REQUIRED - {"summary"}:
        if not isinstance(payload[key], list):
            raise ValueError(f"analyse: {key} doit être une liste")
    if not str(payload["summary"]).strip():
        raise ValueError("analyse: summary vide")

    document = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        **payload,
    }
    path = _artifact(project, "analysis")
    _write_json(path, document)
    return path


def store_clarifications_from_analysis(project: Path) -> Path:
    analysis = _require_artifact(project, "analysis")
    items: list[dict[str, Any]] = []
    counter = 0
    categories = (
        ("ambiguity", analysis.get("ambiguities", [])),
        ("missing_information", analysis.get("missing_information", [])),
        ("decision_required", analysis.get("decisions_required", [])),
    )
    for source, values in categories:
        if not isinstance(values, list):
            raise ValueError(f"analyse: {source} doit être une liste")
        for value in values:
            question, blocking = _normalize_question(value)
            if not question:
                continue
            counter += 1
            items.append(
                {
                    "id": f"clarification-{counter:03d}",
                    "source": source,
                    "question": question,
                    "blocking": blocking,
                    "status": "OPEN",
                    "answer": None,
                    "resolved_at": None,
                }
            )
    payload = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "items": items,
    }
    path = _artifact(project, "clarifications")
    _write_json(path, payload)
    return path


def resolve_clarification(
    project: Path,
    clarification_id: str,
    answer: str,
    *,
    actor: str = "human",
) -> dict[str, Any]:
    path = _artifact(project, "clarifications")
    payload = _load_json(path)
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError("clarifications.json: items invalide")

    found = False
    for item in items:
        if not isinstance(item, dict) or item.get("id") != clarification_id:
            continue
        found = True
        item["status"] = "RESOLVED"
        item["answer"] = answer.strip()
        item["resolved_at"] = _now()
        item["resolved_by"] = actor
        break
    if not found:
        raise KeyError(f"clarification inconnue: {clarification_id}")
    if not answer.strip():
        raise ValueError("réponse de clarification vide")

    payload["updated_at"] = _now()
    _write_json(path, payload)

    if current_status(project) == "CLARIFICATION_REQUIRED" and not open_blocking_clarifications(
        project
    ):
        transition_project(
            project,
            "ANALYZED",
            actor=actor,
            reason="all_blocking_clarifications_resolved",
        )
    return payload


def _validate_task_id(task_id: str) -> str:
    value = task_id.strip().lower()
    if not _TASK_ID_RE.fullmatch(value):
        raise ValueError(f"task id invalide: {task_id}")
    return value


def _validate_plan_tasks(tasks: list[dict[str, Any]]) -> None:
    if not tasks:
        raise ValueError("plan: au moins une tâche est requise")

    known_ids: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    for task in tasks:
        task_id = _validate_task_id(str(task.get("id", "")))
        if task_id in known_ids:
            raise ValueError(f"task id dupliqué: {task_id}")
        known_ids.add(task_id)
        role = str(task.get("role", ""))
        if role not in AGENT_IDS:
            raise ValueError(f"{task_id}: rôle inconnu: {role}")
        for field in ("title", "objective"):
            if not str(task.get(field, "")).strip():
                raise ValueError(f"{task_id}: {field} vide")
        for field in ("depends_on", "expected_outputs", "acceptance_criteria"):
            if not isinstance(task.get(field, []), list):
                raise ValueError(f"{task_id}: {field} doit être une liste")
        dependencies[task_id] = [str(value) for value in task.get("depends_on", [])]

    for task_id, values in dependencies.items():
        for dependency in values:
            if dependency not in known_ids:
                raise ValueError(f"{task_id}: dépendance inconnue: {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError(f"cycle de dépendances détecté autour de {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependencies[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependencies:
        visit(task_id)


def store_plan(project: Path, payload: dict[str, Any]) -> Path:
    workstreams = payload.get("workstreams", [])
    tasks = payload.get("tasks", [])
    if not isinstance(workstreams, list):
        raise ValueError("plan: workstreams doit être une liste")
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        raise ValueError("plan: tasks doit être une liste d'objets")
    _validate_plan_tasks(tasks)

    document = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "workstreams": workstreams,
        "tasks": tasks,
    }
    path = _artifact(project, "plan")
    _write_json(path, document)
    return path


def create_assignments(project: Path) -> Path:
    plan = _require_artifact(project, "plan")
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        raise ValueError("project_plan.json: tasks invalide")

    assigned: list[dict[str, Any]] = []
    task_packet_root = project / "context" / "tasks"
    task_packet_root.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        task_id = _validate_task_id(str(task["id"]))
        packet = {
            "schema_version": "1.0.0",
            "project_id": load_project_manifest(project)["project_id"],
            "task": task,
            "output_roots": {
                "work": f"work/{task_id}",
                "deliverables": f"deliverables/{task_id}",
                "evidence": f"evidence/{task_id}",
                "diagrams": f"diagrams/{task_id}",
            },
        }
        _write_json(task_packet_root / f"{task_id}.json", packet)
        assigned.append(
            {
                "task_id": task_id,
                "role": task["role"],
                "depends_on": list(task.get("depends_on", [])),
                "status": "PENDING",
                "attempts": 0,
            }
        )

    document = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "tasks": assigned,
    }
    path = _artifact(project, "assignments")
    _write_json(path, document)
    return path


def pending_tasks(project: Path) -> list[dict[str, Any]]:
    assignments = _require_artifact(project, "assignments")
    tasks = assignments.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("task_assignments.json: tasks invalide")
    max_attempts = int(_policy().get("execution", {}).get("max_task_attempts", 2))
    by_id = {
        str(task.get("task_id")): task
        for task in tasks
        if isinstance(task, dict)
    }
    ready: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict) or task.get("status") == "PASS":
            continue
        if int(task.get("attempts", 0)) >= max_attempts:
            continue
        dependencies = task.get("depends_on", [])
        if all(by_id.get(str(dep), {}).get("status") == "PASS" for dep in dependencies):
            ready.append(task)
    return ready


def record_task_result(
    project: Path,
    task_id: str,
    *,
    agent: str,
    success: bool,
    returncode: int,
    evidence_file: str,
    collected_outputs: list[str],
) -> dict[str, Any]:
    normalized = _validate_task_id(task_id)
    assignments_path = _artifact(project, "assignments")
    assignments = _load_json(assignments_path)
    tasks = assignments.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("task_assignments.json: tasks invalide")

    assignment: dict[str, Any] | None = None
    for item in tasks:
        if isinstance(item, dict) and item.get("task_id") == normalized:
            assignment = item
            break
    if assignment is None:
        raise KeyError(f"tâche inconnue: {normalized}")
    if assignment.get("role") != agent:
        raise ValueError(f"{normalized}: agent {agent} différent de l'assignation")

    assignment["attempts"] = int(assignment.get("attempts", 0)) + 1
    assignment["status"] = "PASS" if success else "FAIL"
    assignment["updated_at"] = _now()
    assignments["updated_at"] = _now()
    _write_json(assignments_path, assignments)

    results_path = _artifact(project, "task_results")
    if results_path.is_file():
        results = _load_json(results_path)
    else:
        results = {
            "schema_version": "1.0.0",
            "results": [],
        }
    result_items = results.setdefault("results", [])
    if not isinstance(result_items, list):
        raise ValueError("task_results.json: results invalide")
    result_items.append(
        {
            "task_id": normalized,
            "agent": agent,
            "attempt": assignment["attempts"],
            "status": assignment["status"],
            "returncode": returncode,
            "evidence_file": evidence_file,
            "collected_outputs": collected_outputs,
            "at": _now(),
        }
    )
    results["updated_at"] = _now()
    _write_json(results_path, results)
    return assignment


def store_validation_report(project: Path, payload: dict[str, Any]) -> Path:
    verdict = str(payload.get("verdict", "")).upper()
    if verdict not in _VALID_VERDICTS:
        raise ValueError("validation: verdict doit être PASS ou FAIL")
    if not isinstance(payload.get("findings", []), list):
        raise ValueError("validation: findings doit être une liste")
    document = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        **payload,
        "verdict": verdict,
    }
    path = _artifact(project, "validation")
    _write_json(path, document)
    return path


def store_review_report(project: Path, payload: dict[str, Any]) -> Path:
    verdict = str(payload.get("verdict", "")).upper()
    if verdict not in _VALID_VERDICTS:
        raise ValueError("review: verdict doit être PASS ou FAIL")
    for field in ("missing_deliverables", "blocking_findings", "recommendations"):
        if not isinstance(payload.get(field, []), list):
            raise ValueError(f"review: {field} doit être une liste")
    document = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        **payload,
        "verdict": verdict,
    }
    path = _artifact(project, "review")
    _write_json(path, document)
    return path


def package_project(project: Path) -> tuple[Path, Path]:
    deliverables = project / "deliverables"
    manifest_path = _artifact(project, "package_manifest")
    project_id = str(load_project_manifest(project)["project_id"])
    archive_path = deliverables / f"{project_id}.zip"

    excluded = {manifest_path.resolve(), archive_path.resolve()}
    files = [
        path
        for path in sorted(deliverables.rglob("*"))
        if path.is_file() and path.resolve() not in excluded
    ]
    if not files:
        raise ValueError("aucun livrable à packager")

    file_entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in files:
            relative = path.relative_to(deliverables)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            file_entries.append(
                {
                    "path": relative.as_posix(),
                    "sha256": digest,
                    "size": path.stat().st_size,
                }
            )
            archive.write(path, relative.as_posix())

    archive_digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "project_id": project_id,
        "files": file_entries,
        "archive": {
            "path": archive_path.name,
            "sha256": archive_digest,
            "size": archive_path.stat().st_size,
        },
    }
    _write_json(manifest_path, manifest)

    final_report = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "project_id": project_id,
        "status": "READY_FOR_HUMAN_COMPLETION",
        "validation_verdict": _validation_verdict(project, "validation"),
        "review_verdict": _validation_verdict(project, "review"),
        "package_manifest": manifest_path.relative_to(project).as_posix(),
        "archive": archive_path.relative_to(project).as_posix(),
    }
    _write_json(_artifact(project, "final_report"), final_report)
    return archive_path, manifest_path


def build_phase_prompt(project_id: str, phase: str, *, task_id: str | None = None) -> str:
    normalized = validate_project_id(project_id)
    project_ref = f"projects/{normalized}"
    if phase == "analyze":
        return (
            f"Analyse le projet {project_ref}. Lis project.json, intake/ et sources/ comme sources "
            "de vérité. Ne suppose rien qui n'est pas soutenu par les fichiers. "
            "Retourne uniquement "
            "un objet JSON avec: summary, objectives[], constraints[], deliverables[], "
            "ambiguities[], missing_information[], risks[], decisions_required[]."
        )
    if phase == "plan":
        return (
            f"Planifie le projet {project_ref}. Lis intake/, sources/, "
            "context/project_analysis.json "
            "et context/clarifications.json. Retourne uniquement un JSON avec workstreams[] et "
            "tasks[]. Chaque task doit contenir id, title, role, objective, depends_on[], "
            "expected_outputs[], acceptance_criteria[], needs_web et security_sensitive. "
            f"Les rôles autorisés sont: {', '.join(AGENT_IDS)}."
        )
    if phase == "execute":
        if task_id is None:
            raise ValueError("task_id requis pour execute")
        normalized_task = _validate_task_id(task_id)
        return (
            f"Exécute la tâche {normalized_task} du projet {project_ref}. Lis "
            f"context/tasks/{normalized_task}.json. Travaille uniquement dans ce snapshot. "
            f"Écris les travaux sous work/{normalized_task}, les livrables sous "
            f"deliverables/{normalized_task}, les preuves sous evidence/{normalized_task} "
            f"et les schémas sous diagrams/{normalized_task}. Respecte les critères "
            "d'acceptation du packet et ne publie rien à distance sans validation humaine."
        )
    if phase == "validate":
        return (
            f"Audite le projet {project_ref}. Compare intake/ et sources/ avec context/, "
            "deliverables/, diagrams/ et evidence/. Ne modifie rien. Retourne uniquement un JSON "
            "avec verdict PASS ou FAIL, findings[], task_results_summary et recommendations[]."
        )
    if phase == "review":
        return (
            f"Effectue la revue finale indépendante du projet {project_ref}. Repars des consignes "
            "originales dans intake/ et des sources réelles. Vérifie la couverture des livrables, "
            "preuves, sécurité, cohérence et ambiguïtés. Ne corrige rien silencieusement. Retourne "
            "uniquement un JSON avec verdict PASS ou FAIL, coverage, missing_deliverables[], "
            "blocking_findings[] et recommendations[]."
        )
    raise ValueError(f"phase inconnue: {phase}")
