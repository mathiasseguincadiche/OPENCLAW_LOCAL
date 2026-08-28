from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.safe_fs import assert_no_link_like, secure_path_within

_ALLOWED_OUTPUT_ROOTS = {"work", "deliverables", "evidence", "diagrams"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _policy() -> dict[str, Any]:
    return load_contract("artifact_exchange_policy.yaml")


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _plan_tasks(project: Path) -> dict[str, dict[str, Any]]:
    plan = _load_json(project / "context" / "project_plan.json")
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("project_plan.json: tasks invalide")
    result: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("project_plan.json: task invalide")
        task_id = str(task.get("id", "")).strip()
        values = task.get("depends_on", [])
        role = str(task.get("role", "")).strip()
        if not task_id or not role or not isinstance(values, list):
            raise ValueError("project_plan.json: id/role/depends_on invalide")
        result[task_id] = task
    return result


def _plan_dependencies(project: Path) -> dict[str, list[str]]:
    return {
        task_id: [str(value) for value in task.get("depends_on", [])]
        for task_id, task in _plan_tasks(project).items()
    }


def _dependent_tasks(
    dependencies: dict[str, list[str]],
    producer: str,
    *,
    transitive: bool,
) -> list[tuple[str, bool]]:
    if producer not in dependencies:
        raise KeyError(f"tâche productrice inconnue: {producer}")
    direct = sorted(task for task, values in dependencies.items() if producer in values)
    if not transitive:
        return [(task, True) for task in direct]
    discovered = set(direct)
    queue = list(direct)
    while queue:
        upstream = queue.pop(0)
        for task, values in dependencies.items():
            if upstream not in values or task in discovered:
                continue
            discovered.add(task)
            queue.append(task)
    return [(task, task in direct) for task in sorted(discovered)]


def _safe_output(project: Path, relative: str) -> Path:
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts or not value.parts:
        raise ValueError(f"sortie échangée invalide: {relative}")
    if value.parts[0] not in _ALLOWED_OUTPUT_ROOTS:
        raise ValueError(f"racine de sortie non autorisée: {relative}")
    return secure_path_within(
        project / value,
        project,
        require_file=True,
        label="sortie échangée",
    )


def _bundle_path(project: Path, producer: str, consumer: str | None, attempt: int) -> Path:
    root = project / "context" / "exchange"
    if consumer is None:
        return root / producer / "self" / f"run-{attempt:03d}"
    return root / consumer / "dependencies" / producer / f"run-{attempt:03d}"


def _write_bundle(
    project: Path,
    *,
    producer: str,
    consumer: str | None,
    agent: str,
    attempt: int,
    status: str,
    collected_outputs: list[str],
    direct_dependency: bool | None,
) -> Path:
    destination = _bundle_path(project, producer, consumer, attempt)
    if destination.exists():
        raise FileExistsError(f"bundle d'échange existe déjà: {destination}")
    artifacts = destination / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, Any]] = []
    aggregate = hashlib.sha256()
    for relative in sorted(set(collected_outputs)):
        source = _safe_output(project, relative)
        target = artifacts / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = _sha256(source)
        size = source.stat().st_size
        records.append({"path": relative, "sha256": digest, "size": size})
        aggregate.update(f"{relative}\0{digest}\0{size}\n".encode())

    manifest = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "producer_task_id": producer,
        "consumer_task_id": consumer,
        "producer_agent": agent,
        "attempt": attempt,
        "producer_status": status,
        "direct_dependency": direct_dependency,
        "files": records,
        "aggregate_sha256": aggregate.hexdigest(),
        "immutable_provenance": True,
        "consumer_must_not_modify_in_place": True,
    }
    _write_json(destination / "manifest.json", manifest)
    assert_no_link_like(destination, label="bundle d'échange")
    return destination


def _append_index(project: Path, records: list[dict[str, Any]]) -> None:
    path = project / str(_policy().get("index_path", "context/exchange/index.json"))
    if path.is_file():
        payload = _load_json(path)
    else:
        payload = {"schema_version": "1.0.0", "records": []}
    entries = payload.setdefault("records", [])
    if not isinstance(entries, list):
        raise ValueError("artifact exchange index invalide")
    entries.extend(records)
    payload["updated_at"] = _now()
    _write_json(path, payload)


def publish_task_outputs(
    project: Path,
    *,
    producer_task_id: str,
    agent: str,
    attempt: int,
    status: str,
    collected_outputs: list[str],
) -> list[str]:
    if attempt < 1:
        raise ValueError("artifact exchange: attempt doit être >= 1")
    normalized_status = status.strip().upper()
    if normalized_status not in {"PASS", "FAIL"}:
        raise ValueError(f"artifact exchange: statut invalide: {status}")
    dependencies = _plan_dependencies(project)
    if producer_task_id not in dependencies:
        raise KeyError(f"artifact exchange: tâche inconnue: {producer_task_id}")

    published: list[Path] = []
    self_bundle = _write_bundle(
        project,
        producer=producer_task_id,
        consumer=None,
        agent=agent,
        attempt=attempt,
        status=normalized_status,
        collected_outputs=collected_outputs,
        direct_dependency=None,
    )
    published.append(self_bundle)

    propagation = _policy().get("propagation", {})
    if normalized_status == "PASS" and bool(propagation.get("direct_dependents", True)):
        dependents = _dependent_tasks(
            dependencies,
            producer_task_id,
            transitive=bool(propagation.get("transitive_dependents", True)),
        )
        for consumer, is_direct in dependents:
            published.append(
                _write_bundle(
                    project,
                    producer=producer_task_id,
                    consumer=consumer,
                    agent=agent,
                    attempt=attempt,
                    status=normalized_status,
                    collected_outputs=collected_outputs,
                    direct_dependency=is_direct,
                )
            )

    index_records = [
        {
            "at": _now(),
            "producer_task_id": producer_task_id,
            "consumer_task_id": None if path.parent.name == "self" else path.parents[2].name,
            "attempt": attempt,
            "status": normalized_status,
            "bundle": path.relative_to(project).as_posix(),
        }
        for path in published
    ]
    _append_index(project, index_records)
    return [path.relative_to(project).as_posix() for path in published]


def affected_agents_after_publish(
    project: Path,
    producer_task_id: str,
    *,
    status: str,
) -> list[str]:
    tasks = _plan_tasks(project)
    if producer_task_id not in tasks:
        raise KeyError(f"artifact exchange: tâche inconnue: {producer_task_id}")
    task_ids = {producer_task_id}
    if status.strip().upper() == "PASS":
        dependencies = _plan_dependencies(project)
        transitive = bool(_policy().get("propagation", {}).get("transitive_dependents", True))
        task_ids.update(
            task_id
            for task_id, _ in _dependent_tasks(
                dependencies,
                producer_task_id,
                transitive=transitive,
            )
        )
    return sorted({str(tasks[task_id]["role"]) for task_id in task_ids})


def validate_exchange_bundle(project: Path, bundle: Path) -> list[str]:
    try:
        secure_path_within(bundle, project, require_dir=True, label="bundle d'échange")
        assert_no_link_like(bundle, label="bundle d'échange")
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return [str(exc)]

    manifest_path = bundle / "manifest.json"
    if not manifest_path.is_file():
        return [f"manifest absent: {bundle.relative_to(project).as_posix()}"]
    payload = _load_json(manifest_path)
    files = payload.get("files", [])
    if not isinstance(files, list):
        return [f"manifest files invalide: {manifest_path.relative_to(project).as_posix()}"]
    failures: list[str] = []
    aggregate = hashlib.sha256()
    for raw in files:
        if not isinstance(raw, dict):
            failures.append("entrée manifeste invalide")
            continue
        relative = str(raw.get("path", ""))
        expected = str(raw.get("sha256", ""))
        target = bundle / "artifacts" / relative
        try:
            safe_target = secure_path_within(
                target,
                bundle / "artifacts",
                require_file=True,
                label="artefact échangé",
            )
        except (FileNotFoundError, ValueError):
            failures.append(f"artefact absent ou non sûr: {relative}")
            continue
        observed = _sha256(safe_target)
        if observed != expected:
            failures.append(f"artefact modifié: {relative}")
        size = safe_target.stat().st_size
        aggregate.update(f"{relative}\0{observed}\0{size}\n".encode())
    expected_aggregate = str(payload.get("aggregate_sha256", ""))
    if aggregate.hexdigest() != expected_aggregate:
        failures.append("digest agrégé du bundle invalide")
    return failures


def validate_exchange_for_task(project: Path, task_id: str) -> list[str]:
    root = project / "context" / "exchange" / task_id
    if not root.exists():
        return []
    try:
        assert_no_link_like(root, label="artifact exchange")
    except ValueError as exc:
        return [str(exc)]
    failures: list[str] = []
    for manifest in sorted(root.rglob("manifest.json")):
        failures.extend(validate_exchange_bundle(project, manifest.parent))
    return failures


def validate_exchange_completeness(project: Path) -> list[str]:
    assignments = _load_json(project / "context" / "task_assignments.json")
    tasks = assignments.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("task_assignments.json: tasks invalide")
    dependencies = _plan_dependencies(project)
    transitive = bool(_policy().get("propagation", {}).get("transitive_dependents", True))
    failures: list[str] = []

    exchange_root = project / "context" / "exchange"
    if exchange_root.exists():
        try:
            assert_no_link_like(exchange_root, label="artifact exchange")
        except ValueError as exc:
            failures.append(str(exc))
            return failures

    for raw in tasks:
        if not isinstance(raw, dict):
            failures.append("assignation invalide")
            continue
        task_id = str(raw.get("task_id", ""))
        attempts = int(raw.get("attempts", 0))
        status = str(raw.get("status", ""))
        if attempts < 1:
            continue
        self_bundle = _bundle_path(project, task_id, None, attempts)
        if not self_bundle.is_dir():
            failures.append(f"self-history absent: {task_id} run-{attempts:03d}")
        else:
            failures.extend(validate_exchange_bundle(project, self_bundle))
        if status != "PASS":
            continue
        for consumer, _ in _dependent_tasks(dependencies, task_id, transitive=transitive):
            bundle = _bundle_path(project, task_id, consumer, attempts)
            if not bundle.is_dir():
                failures.append(
                    f"propagation absente: {task_id} -> {consumer} run-{attempts:03d}"
                )
            else:
                failures.extend(validate_exchange_bundle(project, bundle))
    return failures
