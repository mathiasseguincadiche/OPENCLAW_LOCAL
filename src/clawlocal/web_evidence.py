from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from clawlocal.config import load_contract

WEB_EVIDENCE_SCHEMA_VERSION = "1.0.0"
_ALLOWED_VOLATILITY = {"stable", "volatile", "current"}
_ALLOWED_CRITICALITY = {"low", "standard", "high", "critical"}
_ALLOWED_STATUS = {"VERIFIED", "CONFLICT", "UNVERIFIED"}
_ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "UNVERIFIED"}
_ALLOWED_AUTHORITY = {"source_of_truth", "primary", "secondary", "community"}
_ALLOWED_DATE_STATUS = {"known", "not_exposed"}
_ALLOWED_CONFLICT_STATUS = {"OPEN", "RESOLVED"}
_CONFIDENCE_RANK = {"UNVERIFIED": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"preuve Web invalide: racine JSON attendue: {path}")
    return payload


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: timestamp ISO-8601 requis")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label}: timestamp ISO-8601 invalide") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label}: timezone explicite requise")
    return parsed.astimezone(UTC)


def _validate_optional_timestamp(value: Any, label: str) -> None:
    if value is not None:
        _parse_timestamp(value, label)


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: chaîne non vide requise")
    return value.strip()


def _policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    return policy if policy is not None else load_contract("web_policy.yaml")


def _effective_now(now: datetime | None) -> datetime:
    value = now or datetime.now(UTC)
    if value.tzinfo is None:
        raise ValueError("now doit inclure une timezone")
    return value.astimezone(UTC)


def _is_recent(
    observed_at: datetime,
    *,
    now: datetime,
    max_age_hours: int,
    skew_minutes: int,
) -> bool:
    if observed_at > now + timedelta(minutes=skew_minutes):
        return False
    return observed_at >= now - timedelta(hours=max_age_hours)


def _validate_url(value: Any, label: str) -> str:
    url = _nonempty_string(value, label)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label}: URL http(s) absolue requise")
    return url


def _minimum_confidence(policy: dict[str, Any], criticality: str) -> str:
    minimums = policy.get("source_verification", {}).get("minimum_confidence", {})
    value = str(minimums.get(criticality, "MEDIUM")).upper()
    if value not in _ALLOWED_CONFIDENCE:
        raise ValueError(
            f"web_policy.yaml: minimum_confidence invalide pour {criticality}: {value}"
        )
    return value


def validate_web_evidence_payload(
    payload: dict[str, Any],
    *,
    expected_task_id: str | None = None,
    require_runtime: bool = False,
    policy: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    web_policy = _policy(policy)
    verification = web_policy.get("source_verification", {})
    freshness = web_policy.get("freshness_policy", {})
    current_time = _effective_now(now)

    required_root = {
        "schema_version",
        "generated_at",
        "task_id",
        "claims",
        "sources",
        "runtime_evidence",
        "conflicts",
    }
    missing_root = sorted(required_root - set(payload))
    if missing_root:
        raise ValueError(
            "preuve Web: champs racine absents: " + ", ".join(missing_root)
        )
    if payload.get("schema_version") != WEB_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("preuve Web: schema_version non supportée")

    _parse_timestamp(payload.get("generated_at"), "generated_at")
    task_id = _nonempty_string(payload.get("task_id"), "task_id")
    if expected_task_id is not None and task_id != expected_task_id:
        raise ValueError(
            f"preuve Web: task_id={task_id} != tâche attendue {expected_task_id}"
        )

    sources = payload.get("sources")
    claims = payload.get("claims")
    runtime_items = payload.get("runtime_evidence")
    conflicts = payload.get("conflicts")
    if not isinstance(sources, list) or any(not isinstance(item, dict) for item in sources):
        raise ValueError("preuve Web: sources doit être une liste d'objets")
    if not isinstance(claims, list) or any(not isinstance(item, dict) for item in claims):
        raise ValueError("preuve Web: claims doit être une liste d'objets")
    if not isinstance(runtime_items, list) or any(
        not isinstance(item, dict) for item in runtime_items
    ):
        raise ValueError("preuve Web: runtime_evidence doit être une liste d'objets")
    if not isinstance(conflicts, list) or any(
        not isinstance(item, dict) for item in conflicts
    ):
        raise ValueError("preuve Web: conflicts doit être une liste d'objets")
    if not claims:
        raise ValueError("preuve Web: au moins une affirmation vérifiée est requise")

    skew_minutes = int(freshness.get("future_clock_skew_minutes", 5))
    source_max_age = int(freshness.get("retrieval_max_age_hours", 24))
    runtime_max_age = int(freshness.get("runtime_observation_max_age_hours", 24))

    source_by_id: dict[str, dict[str, Any]] = {}
    source_url_seen: set[str] = set()
    for source in sources:
        source_id = _nonempty_string(source.get("source_id"), "source.source_id")
        if source_id in source_by_id:
            raise ValueError(f"preuve Web: source_id dupliqué: {source_id}")
        url = _validate_url(source.get("url"), f"{source_id}.url")
        if url in source_url_seen:
            raise ValueError(f"preuve Web: URL source dupliquée: {url}")
        source_url_seen.add(url)
        _nonempty_string(source.get("title"), f"{source_id}.title")
        _nonempty_string(source.get("publisher"), f"{source_id}.publisher")
        authority = str(source.get("authority", ""))
        if authority not in _ALLOWED_AUTHORITY:
            raise ValueError(f"{source_id}.authority invalide: {authority}")
        date_status = str(source.get("date_status", ""))
        if date_status not in _ALLOWED_DATE_STATUS:
            raise ValueError(f"{source_id}.date_status invalide: {date_status}")
        published_at = source.get("published_at")
        updated_at = source.get("updated_at")
        _validate_optional_timestamp(published_at, f"{source_id}.published_at")
        _validate_optional_timestamp(updated_at, f"{source_id}.updated_at")
        if date_status == "known" and published_at is None and updated_at is None:
            raise ValueError(
                f"{source_id}: published_at ou updated_at requis quand date_status=known"
            )
        if date_status == "not_exposed" and (published_at is not None or updated_at is not None):
            raise ValueError(
                f"{source_id}: dates doivent être null quand date_status=not_exposed"
            )
        retrieved_at = _parse_timestamp(
            source.get("retrieved_at"), f"{source_id}.retrieved_at"
        )
        if retrieved_at > current_time + timedelta(minutes=skew_minutes):
            raise ValueError(f"{source_id}: retrieved_at est dans le futur")
        supports_currentness = source.get("supports_currentness")
        if not isinstance(supports_currentness, bool):
            raise ValueError(f"{source_id}.supports_currentness doit être booléen")
        source_by_id[source_id] = source

    runtime_by_id: dict[str, dict[str, Any]] = {}
    for item in runtime_items:
        evidence_id = _nonempty_string(
            item.get("evidence_id"), "runtime_evidence.evidence_id"
        )
        if evidence_id in runtime_by_id:
            raise ValueError(f"preuve Web: evidence_id dupliqué: {evidence_id}")
        kind = str(item.get("kind", ""))
        allowed_kinds = set(verification.get("runtime_evidence_kinds", []))
        if kind not in allowed_kinds:
            raise ValueError(f"{evidence_id}.kind invalide: {kind}")
        observed_at = _parse_timestamp(
            item.get("observed_at"), f"{evidence_id}.observed_at"
        )
        result = str(item.get("result", "")).upper()
        if result not in {"PASS", "FAIL"}:
            raise ValueError(f"{evidence_id}.result doit être PASS ou FAIL")
        _nonempty_string(item.get("command"), f"{evidence_id}.command")
        exit_code = item.get("exit_code")
        if exit_code is not None and not isinstance(exit_code, int):
            raise ValueError(f"{evidence_id}.exit_code doit être un entier ou null")
        if observed_at > current_time + timedelta(minutes=skew_minutes):
            raise ValueError(f"{evidence_id}: observed_at est dans le futur")
        runtime_by_id[evidence_id] = item

    unresolved_conflicts = 0
    for conflict in conflicts:
        conflict_id = _nonempty_string(
            conflict.get("conflict_id"), "conflict.conflict_id"
        )
        _nonempty_string(conflict.get("description"), f"{conflict_id}.description")
        status = str(conflict.get("status", "")).upper()
        if status not in _ALLOWED_CONFLICT_STATUS:
            raise ValueError(f"{conflict_id}.status invalide: {status}")
        claim_ids = conflict.get("claim_ids")
        if not isinstance(claim_ids, list) or any(
            not isinstance(item, str) or not item.strip() for item in claim_ids
        ):
            raise ValueError(f"{conflict_id}.claim_ids doit être une liste de chaînes")
        if status == "OPEN":
            unresolved_conflicts += 1

    if (
        unresolved_conflicts
        and verification.get("unresolved_conflict_blocks_acceptance") is True
    ):
        raise ValueError("preuve Web: contradiction non résolue")

    accepted_currentness = set(verification.get("accepted_currentness_basis", []))
    target_count = int(verification.get("source_count_target", 2))
    saw_runtime_claim = False
    claim_ids_seen: set[str] = set()

    for claim in claims:
        claim_id = _nonempty_string(claim.get("claim_id"), "claim.claim_id")
        if claim_id in claim_ids_seen:
            raise ValueError(f"preuve Web: claim_id dupliqué: {claim_id}")
        claim_ids_seen.add(claim_id)
        _nonempty_string(claim.get("text"), f"{claim_id}.text")
        volatility = str(claim.get("volatility", ""))
        if volatility not in _ALLOWED_VOLATILITY:
            raise ValueError(f"{claim_id}.volatility invalide: {volatility}")
        criticality = str(claim.get("criticality", ""))
        if criticality not in _ALLOWED_CRITICALITY:
            raise ValueError(f"{claim_id}.criticality invalide: {criticality}")
        status = str(claim.get("status", "")).upper()
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"{claim_id}.status invalide: {status}")
        if status != "VERIFIED":
            raise ValueError(f"{claim_id}: affirmation non vérifiée ({status})")
        confidence = str(claim.get("confidence", "")).upper()
        if confidence not in _ALLOWED_CONFIDENCE:
            raise ValueError(f"{claim_id}.confidence invalide: {confidence}")
        minimum = _minimum_confidence(web_policy, criticality)
        if _CONFIDENCE_RANK[confidence] < _CONFIDENCE_RANK[minimum]:
            raise ValueError(
                f"{claim_id}: confiance {confidence} < minimum {minimum}"
            )

        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list) or any(
            not isinstance(item, str) or not item.strip() for item in source_ids
        ):
            raise ValueError(f"{claim_id}.source_ids doit être une liste de chaînes")
        if not source_ids:
            raise ValueError(f"{claim_id}: au moins une source est requise")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"{claim_id}: source_ids contient des doublons")
        missing_sources = [item for item in source_ids if item not in source_by_id]
        if missing_sources:
            raise ValueError(
                f"{claim_id}: sources inconnues: {', '.join(missing_sources)}"
            )

        runtime_ids = claim.get("runtime_evidence_ids")
        if not isinstance(runtime_ids, list) or any(
            not isinstance(item, str) or not item.strip() for item in runtime_ids
        ):
            raise ValueError(
                f"{claim_id}.runtime_evidence_ids doit être une liste de chaînes"
            )
        missing_runtime = [item for item in runtime_ids if item not in runtime_by_id]
        if missing_runtime:
            raise ValueError(
                f"{claim_id}: preuves runtime inconnues: {', '.join(missing_runtime)}"
            )

        machine_verifiable = claim.get("machine_verifiable")
        if not isinstance(machine_verifiable, bool):
            raise ValueError(f"{claim_id}.machine_verifiable doit être booléen")
        if machine_verifiable:
            saw_runtime_claim = True
            if not runtime_ids:
                raise ValueError(f"{claim_id}: preuve runtime obligatoire")
            for runtime_id in runtime_ids:
                runtime_item = runtime_by_id[runtime_id]
                observed_at = _parse_timestamp(
                    runtime_item.get("observed_at"), f"{runtime_id}.observed_at"
                )
                if str(runtime_item.get("result", "")).upper() != "PASS":
                    raise ValueError(f"{claim_id}: preuve runtime {runtime_id} en échec")
                if not _is_recent(
                    observed_at,
                    now=current_time,
                    max_age_hours=runtime_max_age,
                    skew_minutes=skew_minutes,
                ):
                    raise ValueError(f"{claim_id}: preuve runtime {runtime_id} trop ancienne")

        referenced_sources = [source_by_id[item] for item in source_ids]
        has_source_of_truth = any(
            str(source.get("authority")) == "source_of_truth"
            for source in referenced_sources
        )
        required_count = 1 if criticality == "low" else target_count
        if not (
            has_source_of_truth
            and verification.get("authoritative_source_of_truth_may_stand_alone") is True
        ):
            publishers = {
                str(source.get("publisher", "")).strip().casefold()
                for source in referenced_sources
            }
            if len(referenced_sources) < required_count:
                raise ValueError(
                    f"{claim_id}: {required_count} sources requises, "
                    f"{len(referenced_sources)} fournie(s)"
                )
            if (
                verification.get("distinct_publishers_for_corroboration") is True
                and len(publishers) < required_count
            ):
                raise ValueError(
                    f"{claim_id}: corroboration par éditeurs distincts insuffisante"
                )

        if volatility in {"current", "volatile"}:
            basis = str(claim.get("currentness_basis", ""))
            if basis not in accepted_currentness:
                raise ValueError(f"{claim_id}.currentness_basis invalide: {basis}")
            current_sources = [
                source
                for source in referenced_sources
                if source.get("supports_currentness") is True
                and str(source.get("authority")) in {"source_of_truth", "primary"}
            ]
            if not current_sources:
                raise ValueError(
                    f"{claim_id}: source autoritative de currentness requise"
                )
            if not any(
                _is_recent(
                    _parse_timestamp(
                        source.get("retrieved_at"),
                        f"{source.get('source_id')}.retrieved_at",
                    ),
                    now=current_time,
                    max_age_hours=source_max_age,
                    skew_minutes=skew_minutes,
                )
                for source in current_sources
            ):
                raise ValueError(
                    f"{claim_id}: aucune source de currentness récupérée récemment"
                )

    if require_runtime and not saw_runtime_claim:
        raise ValueError(
            "preuve Web: la tâche exige une vérification runtime mais aucune affirmation "
            "machine_verifiable n'est documentée"
        )
    return payload


def validate_web_evidence_file(
    path: Path,
    *,
    expected_task_id: str | None = None,
    require_runtime: bool = False,
    policy: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return validate_web_evidence_payload(
        _load_json(path),
        expected_task_id=expected_task_id,
        require_runtime=require_runtime,
        policy=policy,
        now=now,
    )


def _load_plan(project: Path) -> dict[str, Any]:
    plan_path = project / "context" / "project_plan.json"
    if not plan_path.is_file():
        raise FileNotFoundError(plan_path)
    return _load_json(plan_path)


def task_web_evidence_failures(project: Path, task_id: str) -> list[str]:
    plan = _load_plan(project)
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list):
        return ["project_plan.json: tasks invalide"]
    task = next(
        (
            item
            for item in tasks
            if isinstance(item, dict) and str(item.get("id", "")) == task_id
        ),
        None,
    )
    if task is None:
        return [f"tâche inconnue dans project_plan.json: {task_id}"]
    if task.get("web_verification_required") is not True:
        return []
    evidence_path = project / "evidence" / task_id / "web_evidence.json"
    try:
        validate_web_evidence_file(
            evidence_path,
            expected_task_id=task_id,
            require_runtime=task.get("runtime_verification_required") is True,
        )
    except (FileNotFoundError, ValueError) as exc:
        return [f"{task_id}: {exc}"]
    return []


def project_web_evidence_failures(project: Path) -> list[str]:
    plan = _load_plan(project)
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list):
        return ["project_plan.json: tasks invalide"]
    failures: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or task.get("web_verification_required") is not True:
            continue
        task_id = str(task.get("id", "")).strip()
        if not task_id:
            failures.append("project_plan.json: tâche Web sans id")
            continue
        failures.extend(task_web_evidence_failures(project, task_id))
    return failures
