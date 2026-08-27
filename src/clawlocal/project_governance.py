from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.project_contracts import validate_project_manifest


def _now() -> str:
    return datetime.now(UTC).isoformat()


def initialize_governance(project: Path) -> None:
    root = project / "context" / "governance"
    root.mkdir(parents=True, exist_ok=True)
    decisions = root / "DECISIONS.md"
    risks = root / "RISKS.md"
    if not decisions.exists():
        decisions.write_text("# Journal des décisions\n\n", encoding="utf-8")
    if not risks.exists():
        risks.write_text("# Registre des risques\n\n", encoding="utf-8")


def append_decision(project: Path, *, decision: str, rationale: str, actor: str) -> None:
    initialize_governance(project)
    path = project / "context" / "governance" / "DECISIONS.md"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"## {_now()} — {actor}\n\n- Décision : {decision.strip()}\n"
            f"- Justification : {rationale.strip()}\n\n"
        )


def append_risk(
    project: Path,
    *,
    risk: str,
    impact: str = "à évaluer",
    mitigation: str = "à définir",
) -> None:
    initialize_governance(project)
    path = project / "context" / "governance" / "RISKS.md"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"## {_now()}\n\n- Risque : {risk.strip()}\n- Impact : {impact.strip()}\n"
            f"- Mitigation : {mitigation.strip()}\n\n"
        )


def required_criticality_gates(manifest: dict[str, Any]) -> set[str]:
    validate_project_manifest(manifest)
    policy = load_contract("project_schema_policy.yaml")
    gates = policy.get("criticality_gates", {}).get(manifest["criticality"], [])
    if not isinstance(gates, list):
        raise ValueError("project_schema_policy: criticality_gates invalide")
    return {str(item) for item in gates}


def cloud_policy_for_project(
    manifest: dict[str, Any],
    *,
    redacted: bool = False,
    human_approved: bool = False,
) -> dict[str, Any]:
    validate_project_manifest(manifest)
    policy = load_contract("project_schema_policy.yaml")
    classification = str(manifest["classification"])
    entry = policy.get("cloud_policy", {}).get(classification, {})
    allowed = entry.get("allowed") is True
    redaction_required = entry.get("redaction_required") is True
    approval_required = entry.get("human_approval_required") is True
    if manifest["criticality"] in {"high", "critical"}:
        approval_required = True
    effective = allowed and (redacted or not redaction_required) and (
        human_approved or not approval_required
    )
    reason = "allowed" if effective else "project_data_governance_denied"
    return {
        "allowed": effective,
        "classification": classification,
        "criticality": manifest["criticality"],
        "redaction_required": redaction_required,
        "human_approval_required": approval_required,
        "reason": reason,
    }


def assert_sensitive_action(
    manifest: dict[str, Any],
    action: str,
    *,
    human_approved: bool,
) -> None:
    validate_project_manifest(manifest)
    publication = load_contract("publication_policy.yaml")
    protected = {str(item) for item in publication.get("human_approval_actions", [])}
    if action not in protected:
        return
    if not human_approved:
        raise PermissionError(f"approbation humaine requise pour l'action: {action}")
    if action == "make_public" and manifest["classification"] == "restricted":
        raise PermissionError("un projet restricted ne peut pas être rendu public")
