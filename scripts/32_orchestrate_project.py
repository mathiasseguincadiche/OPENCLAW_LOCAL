from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.project_context import (
    collect_agent_outputs,
    sync_project_context,
    sync_project_to_all_agents,
)
from clawlocal.project_governance import required_criticality_gates
from clawlocal.project_migrations import ensure_current_project_schema
from clawlocal.project_orchestrator_superset import (
    all_tasks_finished,
    build_phase_prompt,
    create_assignments,
    current_status,
    load_project_manifest,
    open_blocking_clarifications,
    package_project,
    pending_tasks,
    project_path,
    record_task_result,
    resolve_clarification,
    store_analysis,
    store_clarifications_from_analysis,
    store_plan,
    store_review_report,
    store_validation_report,
    transition_project,
)
from clawlocal.project_remediation import reopen_tasks_for_correction
from clawlocal.runtime import build_openclaw_agent_command, route_evidence, route_request
from clawlocal.telemetry import automatic_run_telemetry, extract_observed_metrics

_JSON_REQUIRED = {
    "analyze": {
        "summary",
        "objectives",
        "constraints",
        "deliverables",
        "ambiguities",
        "missing_information",
        "risks",
        "decisions_required",
    },
    "plan": {"workstreams", "tasks"},
    "validate": {"verdict", "findings"},
    "review": {
        "verdict",
        "coverage",
        "missing_deliverables",
        "blocking_findings",
        "recommendations",
    },
}


def default_root() -> Path:
    configured = os.environ.get("OPENCLAW_LOCAL_ROOT")
    if configured:
        return Path(configured)
    if Path("E:/").exists():
        return Path("E:/AI/OpenClawLocal")
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "OpenClawLocal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project Orchestrator OPENCLAW_LOCAL: flou -> plan -> livrables vérifiés."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "status",
            "analyze",
            "resolve",
            "plan",
            "assign",
            "execute",
            "validate",
            "review",
            "package",
            "complete",
            "run",
        ],
    )
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--task")
    parser.add_argument("--clarification-id")
    parser.add_argument("--answer")
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)
    return parser.parse_args()


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _write_invocation_evidence(
    project: Path,
    phase: str,
    agent: str,
    payload: dict[str, Any],
) -> Path:
    target = project / "evidence" / "orchestration" / f"{_timestamp()}-{phase}-{agent}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def _try_parse_json_text(text: str) -> Any:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(value[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _find_structured_payload(value: Any, required: set[str]) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if required <= set(value):
            return value
        for child in value.values():
            found = _find_structured_payload(child, required)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_structured_payload(child, required)
            if found is not None:
                return found
    elif isinstance(value, str):
        parsed = _try_parse_json_text(value)
        if parsed is not None and parsed != value:
            return _find_structured_payload(parsed, required)
    return None


def _local_agent_call(
    project: Path,
    agent: str,
    phase: str,
    message: str,
    *,
    execute: bool,
    timeout: int,
) -> tuple[dict[str, Any], Path | None]:
    decision, resolved_model = route_request(agent)
    command = build_openclaw_agent_command(decision, resolved_model, message)
    evidence: dict[str, Any] = {
        "phase": phase,
        "agent": agent,
        "route": route_evidence(decision, resolved_model),
        "command": command[:-3] + ["<project-prompt>", "--json"],
        "executed": execute,
    }
    if not execute:
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return evidence, None

    manifest = load_project_manifest(project)
    with automatic_run_telemetry(
        project,
        project_id=str(manifest["project_id"]),
        agent=agent,
        model=resolved_model,
        backend=resolved_model.split("/", maxsplit=1)[0],
        route_kind=decision.route_kind,
        phase=phase,
    ) as observed:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        evidence["returncode"] = completed.returncode
        if completed.stdout:
            try:
                evidence["openclaw"] = json.loads(completed.stdout)
                observed.update(extract_observed_metrics(evidence["openclaw"]))
            except json.JSONDecodeError:
                evidence["stdout"] = completed.stdout
        if completed.stderr:
            evidence["stderr"] = completed.stderr
    evidence_path = _write_invocation_evidence(project, phase, agent, evidence)
    return evidence, evidence_path


def _phase_payload(evidence: dict[str, Any], phase: str) -> dict[str, Any]:
    required = _JSON_REQUIRED[phase]
    found = _find_structured_payload(evidence, required)
    if found is None:
        raise ValueError(f"{phase}: la sortie OpenClaw ne contient pas le JSON contractuel attendu")
    return found


def _show_status(project: Path) -> None:
    manifest = load_project_manifest(project)
    output: dict[str, Any] = {
        "project_id": manifest["project_id"],
        "title": manifest["title"],
        "status": manifest["status"],
        "classification": manifest["classification"],
        "criticality": manifest["criticality"],
        "criticality_gates": sorted(required_criticality_gates(manifest)),
        "expected_deliverables": manifest.get("expected_deliverables", []),
        "open_blocking_clarifications": open_blocking_clarifications(project),
    }
    try:
        output["ready_tasks"] = pending_tasks(project)
    except (FileNotFoundError, ValueError):
        output["ready_tasks"] = []
    print(json.dumps(output, ensure_ascii=False, indent=2))


def _analyze(project: Path, root: Path, *, execute: bool, timeout: int) -> bool:
    if current_status(project) != "INTAKE_READY":
        raise ValueError("analyze exige le statut INTAKE_READY")
    sync_project_context(root, project.name, "chef-operations")
    evidence, _ = _local_agent_call(
        project,
        "chef-operations",
        "analyze",
        build_phase_prompt(project.name, "analyze"),
        execute=execute,
        timeout=timeout,
    )
    if not execute:
        return False
    analysis = _phase_payload(evidence, "analyze")
    store_analysis(project, analysis)
    store_clarifications_from_analysis(project)
    transition_project(
        project,
        "ANALYZED",
        actor="chef-operations",
        reason="project_analysis_completed",
    )
    if open_blocking_clarifications(project):
        transition_project(
            project,
            "CLARIFICATION_REQUIRED",
            actor="chef-operations",
            reason="blocking_clarifications_detected",
        )
    return True


def _plan(project: Path, root: Path, *, execute: bool, timeout: int) -> bool:
    if current_status(project) != "ANALYZED":
        raise ValueError("plan exige le statut ANALYZED")
    if open_blocking_clarifications(project):
        raise ValueError("clarifications bloquantes non résolues")
    sync_project_context(root, project.name, "chef-operations")
    evidence, _ = _local_agent_call(
        project,
        "chef-operations",
        "plan",
        build_phase_prompt(project.name, "plan"),
        execute=execute,
        timeout=timeout,
    )
    if not execute:
        return False
    store_plan(project, _phase_payload(evidence, "plan"))
    transition_project(
        project,
        "PLANNED",
        actor="chef-operations",
        reason="project_plan_completed",
    )
    return True


def _assign(project: Path, root: Path) -> None:
    if current_status(project) != "PLANNED":
        raise ValueError("assign exige le statut PLANNED")
    create_assignments(project)
    transition_project(
        project,
        "ASSIGNED",
        actor="chef-operations",
        reason="tasks_assigned_to_agents",
    )
    sync_project_to_all_agents(root, project.name)


def _execute_tasks(
    project: Path,
    root: Path,
    *,
    task_id: str | None,
    execute: bool,
    timeout: int,
) -> bool:
    status = current_status(project)
    if status == "ASSIGNED":
        transition_project(
            project,
            "IN_PROGRESS",
            actor="chef-operations",
            reason="execution_started",
        )
    elif status != "IN_PROGRESS":
        raise ValueError("execute exige ASSIGNED ou IN_PROGRESS")

    mutated = False
    while True:
        tasks = pending_tasks(project)
        if task_id is not None:
            tasks = [task for task in tasks if task.get("task_id") == task_id]
        if not tasks:
            if all_tasks_finished(project):
                transition_project(
                    project,
                    "VALIDATING",
                    actor="chef-operations",
                    reason="all_tasks_passed",
                )
                return mutated
            if task_id is not None:
                raise ValueError(f"tâche non exécutable ou inconnue: {task_id}")
            if mutated:
                return mutated
            raise ValueError(
                "aucune tâche prête: dépendance en échec ou nombre maximal de tentatives atteint"
            )

        any_failure = False
        for task in tasks:
            current_task = str(task["task_id"])
            agent = str(task["role"])
            snapshot = root / "workspaces" / agent / "projects" / project.name
            if not snapshot.exists():
                sync_project_context(root, project.name, agent)
            evidence, evidence_path = _local_agent_call(
                project,
                agent,
                "execute",
                build_phase_prompt(project.name, "execute", task_id=current_task),
                execute=execute,
                timeout=timeout,
            )
            if not execute:
                continue
            returncode = int(evidence.get("returncode", 1))
            outputs = collect_agent_outputs(root, project.name, agent, current_task)
            relative_evidence = (
                evidence_path.relative_to(project).as_posix() if evidence_path is not None else ""
            )
            record_task_result(
                project,
                current_task,
                agent=agent,
                success=returncode == 0,
                returncode=returncode,
                evidence_file=relative_evidence,
                collected_outputs=outputs,
            )
            mutated = True
            if returncode != 0:
                any_failure = True
        if not execute:
            return False
        if task_id is not None or any_failure:
            return mutated


def _validate(project: Path, root: Path, *, execute: bool, timeout: int) -> bool:
    if current_status(project) != "VALIDATING":
        raise ValueError("validate exige le statut VALIDATING")
    sync_project_context(root, project.name, "auditeur-qualite", include_outputs=True)
    prompt = build_phase_prompt(project.name, "validate") + (
        " Si le verdict est FAIL, ajoute retry_task_ids[] avec les identifiants exacts des tâches "
        "à corriger. Si le finding concerne une dépendance amont, indique la tâche amont."
    )
    evidence, _ = _local_agent_call(
        project,
        "auditeur-qualite",
        "validate",
        prompt,
        execute=execute,
        timeout=timeout,
    )
    if not execute:
        return False
    report = _phase_payload(evidence, "validate")
    store_validation_report(project, report)
    if str(report["verdict"]).upper() == "PASS":
        transition_project(
            project,
            "REVIEW",
            actor="auditeur-qualite",
            reason="validation_passed",
        )
    else:
        reopened = reopen_tasks_for_correction(project, report, source="validation")
        print("REOPENED_TASKS=" + ",".join(reopened))
        transition_project(
            project,
            "IN_PROGRESS",
            actor="auditeur-qualite",
            reason="validation_failed_tasks_reopened",
        )
    return True


def _review(project: Path, root: Path, *, execute: bool, timeout: int) -> bool:
    if current_status(project) != "REVIEW":
        raise ValueError("review exige le statut REVIEW")
    sync_project_context(root, project.name, "auditeur-qualite", include_outputs=True)
    prompt = build_phase_prompt(project.name, "review") + (
        " Si le verdict est FAIL, ajoute retry_task_ids[] avec les identifiants exacts des tâches "
        "à corriger. N'invente pas d'identifiant absent du plan."
    )
    evidence, _ = _local_agent_call(
        project,
        "auditeur-qualite",
        "review",
        prompt,
        execute=execute,
        timeout=timeout,
    )
    if not execute:
        return False
    report = _phase_payload(evidence, "review")
    store_review_report(project, report)
    if str(report["verdict"]).upper() == "PASS":
        transition_project(
            project,
            "PACKAGING",
            actor="auditeur-qualite",
            reason="independent_review_passed",
        )
    else:
        reopened = reopen_tasks_for_correction(project, report, source="review")
        print("REOPENED_TASKS=" + ",".join(reopened))
        transition_project(
            project,
            "IN_PROGRESS",
            actor="auditeur-qualite",
            reason="review_failed_tasks_reopened",
        )
    return True


def _package(project: Path) -> None:
    if current_status(project) != "PACKAGING":
        raise ValueError("package exige le statut PACKAGING")
    archive, manifest = package_project(project)
    print(f"PACKAGE={archive}")
    print(f"MANIFEST={manifest}")


def _complete(project: Path, *, human_approved: bool) -> None:
    if current_status(project) != "PACKAGING":
        raise ValueError("complete exige le statut PACKAGING")
    transition_project(
        project,
        "COMPLETE",
        actor="human",
        reason="final_human_approval",
        human_approved=human_approved,
    )
    print("STATUS=COMPLETE")


def _run(project: Path, root: Path, *, execute: bool, timeout: int) -> None:
    if not execute:
        print("RUN_DRY_MODE: une phase LLM est seulement prévisualisée.")
    for _ in range(20):
        status = current_status(project)
        if status == "INTAKE_READY":
            if not _analyze(project, root, execute=execute, timeout=timeout):
                return
        elif status == "CLARIFICATION_REQUIRED":
            _show_status(project)
            print("STOP=HUMAN_CLARIFICATION_REQUIRED")
            return
        elif status == "ANALYZED":
            if not _plan(project, root, execute=execute, timeout=timeout):
                return
        elif status == "PLANNED":
            _assign(project, root)
        elif status in {"ASSIGNED", "IN_PROGRESS"}:
            if not _execute_tasks(
                project,
                root,
                task_id=None,
                execute=execute,
                timeout=timeout,
            ):
                return
            if current_status(project) == "IN_PROGRESS":
                _show_status(project)
                print("STOP=TASK_CORRECTION_REQUIRED")
                return
        elif status == "VALIDATING":
            if not _validate(project, root, execute=execute, timeout=timeout):
                return
            if current_status(project) == "IN_PROGRESS":
                _show_status(project)
                print("STOP=VALIDATION_FAILED_TASKS_REOPENED")
                return
        elif status == "REVIEW":
            if not _review(project, root, execute=execute, timeout=timeout):
                return
            if current_status(project) == "IN_PROGRESS":
                _show_status(project)
                print("STOP=REVIEW_FAILED_TASKS_REOPENED")
                return
        elif status == "PACKAGING":
            _package(project)
            print("STOP=HUMAN_COMPLETION_APPROVAL_REQUIRED")
            return
        elif status == "COMPLETE":
            _show_status(project)
            return
        else:
            raise ValueError(f"statut projet inconnu: {status}")
    raise RuntimeError("boucle d'orchestration interrompue par garde-fou")


def main() -> int:
    args = parse_args()
    project = project_path(args.root, args.project)
    ensure_current_project_schema(project)
    if args.action == "status":
        _show_status(project)
    elif args.action == "analyze":
        _analyze(project, args.root, execute=args.execute, timeout=args.timeout)
    elif args.action == "resolve":
        if not args.clarification_id or args.answer is None:
            raise ValueError("resolve exige --clarification-id et --answer")
        resolve_clarification(project, args.clarification_id, args.answer)
        _show_status(project)
    elif args.action == "plan":
        _plan(project, args.root, execute=args.execute, timeout=args.timeout)
    elif args.action == "assign":
        _assign(project, args.root)
    elif args.action == "execute":
        _execute_tasks(
            project,
            args.root,
            task_id=args.task,
            execute=args.execute,
            timeout=args.timeout,
        )
    elif args.action == "validate":
        _validate(project, args.root, execute=args.execute, timeout=args.timeout)
    elif args.action == "review":
        _review(project, args.root, execute=args.execute, timeout=args.timeout)
    elif args.action == "package":
        _package(project)
    elif args.action == "complete":
        _complete(project, human_approved=args.human_approved)
    elif args.action == "run":
        _run(project, args.root, execute=args.execute, timeout=args.timeout)
    else:
        raise ValueError(f"action inconnue: {args.action}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        FileExistsError,
        FileNotFoundError,
        KeyError,
        PermissionError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
