from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"


def _load_yaml(name: str) -> dict[str, Any]:
    with (CONFIG / name).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return data


def _check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    intake = _load_yaml("intake_policy.yaml")
    pedagogy = _load_yaml("pedagogy_policy.yaml")
    accessibility = _load_yaml("accessibility_policy.yaml")
    publication = _load_yaml("publication_policy.yaml")
    telemetry = _load_yaml("telemetry_policy.yaml")
    tools = _load_yaml("tool_policy.yaml")
    roles = _load_yaml("role_matrix.yaml")
    project = _load_yaml("project_policy.yaml")
    security = _load_yaml("security.yaml")

    untrusted = intake.get("untrusted_input", {})
    integrity = intake.get("integrity", {})
    immutability = intake.get("immutability", {})
    _check(
        untrusted.get("documents_are_authoritative_instructions") is False,
        "intake: documents entrants ne doivent pas devenir instructions d'autorité",
        failures,
    )
    _check(untrusted.get("follow_symlinks") is False, "intake: follow_symlinks doit rester false", failures)
    _check(untrusted.get("reject_symlinks_in_intake") is True, "intake: les symlinks doivent être refusés", failures)
    _check(untrusted.get("fail_on_suspected_secret") is True, "intake: secret potentiel doit bloquer l'ingestion", failures)
    _check(integrity.get("require_manifest") is True, "intake: manifeste obligatoire", failures)
    _check(integrity.get("require_checksums") is True, "intake: checksums obligatoires", failures)
    _check(integrity.get("hash_algorithm") == "sha256", "intake: SHA-256 requis", failures)
    _check(integrity.get("require_mime_inventory") is True, "intake: inventaire MIME obligatoire", failures)
    _check(immutability.get("read_only_after_ingestion") is True, "intake: lecture seule après ingestion requise", failures)
    _check(immutability.get("windows_acl_required_on_windows") is True, "intake: ACL Windows requise", failures)

    profiles = pedagogy.get("profiles", {})
    _check(set(profiles) == {"efficient", "balanced", "intensive"}, "pédagogie: profils requis", failures)
    expected_shares = {
        "efficient": (90, 10),
        "balanced": (70, 30),
        "intensive": (60, 40),
    }
    for name, shares in expected_shares.items():
        profile = profiles.get(name, {})
        actual = (
            profile.get("execution_share_percent"),
            profile.get("learning_share_percent"),
        )
        _check(actual == shares, f"pédagogie: ratios inattendus pour {name}", failures)
    guardrails = pedagogy.get("guardrails", {})
    _check(
        guardrails.get("never_mark_acquired_from_exposure_only") is True,
        "pédagogie: exposition seule ne doit jamais valider une compétence",
        failures,
    )
    _check(
        guardrails.get("acquired_requires_human_or_assessment_evidence") is True,
        "pédagogie: ACQUIRED doit exiger une preuve",
        failures,
    )

    depths = accessibility.get("reading_depths", [])
    depth_ids = [item.get("id") for item in depths if isinstance(item, dict)]
    _check(
        depth_ids == ["understand", "operate", "deepen", "diagnose"],
        "accessibilité: quatre profondeurs progressives requises",
        failures,
    )
    principles = accessibility.get("principles", {})
    _check(principles.get("technical_accuracy_first") is True, "accessibilité: exactitude technique prioritaire", failures)
    _check(principles.get("no_false_simplification") is True, "accessibilité: simplification fausse interdite", failures)

    expected_publication_states = [
        "LOCAL_IN_PROGRESS",
        "LOCAL_VALIDATED",
        "READY_TO_PUBLISH",
        "REMOTE_CREATED",
        "BRANCH_PUSHED",
        "PR_MR_OPEN",
        "CI_GREEN",
        "REMOTE_CLONE_VALIDATED",
        "RELEASE_CREATED",
        "PUBLISHED_AND_VERIFIED",
    ]
    _check(publication.get("states") == expected_publication_states, "publication: machine d'états incomplète", failures)
    pub_rules = publication.get("rules", {})
    _check(pub_rules.get("direct_push_to_main") is False, "publication: push direct main interdit", failures)
    _check(pub_rules.get("remote_ci_required") is True, "publication: CI distante obligatoire", failures)
    _check(pub_rules.get("clean_clone_test_required") is True, "publication: clean clone obligatoire", failures)
    _check(pub_rules.get("independent_remote_audit_required") is True, "publication: audit distant indépendant obligatoire", failures)

    storage = telemetry.get("storage", {})
    privacy = telemetry.get("privacy", {})
    _check(storage.get("commit_to_git") is False, "télémétrie: événements runtime hors Git", failures)
    for key in (
        "record_prompt_content",
        "record_response_content",
        "record_source_documents",
        "record_secrets",
    ):
        _check(privacy.get(key) is False, f"télémétrie: {key} doit rester false", failures)
    optional = set(telemetry.get("optional_fields", []))
    required_metrics = {
        "agent",
        "model",
        "backend",
        "ttft_ms",
        "tokens_per_second",
        "vram_mb",
        "ram_mb",
        "tool_calls",
        "retries",
        "local_to_deep_transition",
        "cloud_escalation",
        "cloud_cost_eur",
    }
    _check(required_metrics <= optional, "télémétrie: métriques opérationnelles incomplètes", failures)

    agent_tools = tools.get("agents", {})
    architect_denied = set(agent_tools.get("architecte-solutions", {}).get("deny", []))
    security_denied = set(agent_tools.get("ingenieur-securite", {}).get("deny", []))
    _check(not {"write", "edit", "apply_patch"} & architect_denied, "permissions: architecte doit pouvoir produire ADR/schémas", failures)
    _check({"exec", "process"} <= architect_denied, "permissions: architecte ne doit pas exécuter de commandes", failures)
    _check({"write", "edit", "apply_patch"} <= security_denied, "permissions: sécurité doit rester read-only", failures)

    security_forbidden = set(roles.get("roles", {}).get("ingenieur-securite", {}).get("forbidden", []))
    _check("modification_directe_sources" in security_forbidden, "role_matrix: sécurité ne modifie pas les sources", failures)

    project_rules = project.get("rules", {})
    _check(project_rules.get("intake_manifest_required") is True, "project: manifeste intake requis", failures)
    _check(project_rules.get("intake_checksums_required") is True, "project: checksums intake requis", failures)
    _check(project_rules.get("publication_requires_separate_state_machine") is True, "project: état publication séparé requis", failures)
    _check(project_rules.get("operational_telemetry_stays_outside_git") is True, "project: télémétrie hors Git requise", failures)

    security_projects = security.get("projects", {})
    _check(security_projects.get("intake_is_untrusted_data") is True, "sécurité: intake doit être non fiable", failures)
    _check(security.get("telemetry", {}).get("fabricated_hardware_metrics_forbidden") is True, "sécurité: métriques fabriquées interdites", failures)

    required_files = (
        "src/clawlocal/project_learning.py",
        "src/clawlocal/project_publication.py",
        "src/clawlocal/telemetry.py",
        "scripts/33_project_learning.py",
        "scripts/34_project_publication.py",
        "scripts/35_telemetry.py",
        "docs/INTAKE_INTEGRITY.md",
        "docs/LEARNING_AND_ACCESSIBILITY.md",
        "docs/PROJECT_PUBLICATION.md",
        "docs/TELEMETRY.md",
    )
    for relative in required_files:
        _check((ROOT / relative).is_file(), f"fichier V7 parity absent: {relative}", failures)

    shared_contract = (ROOT / "agents" / "_shared" / "CONTRACT.md").read_text(encoding="utf-8")
    _check("PROJECT_GUIDANCE.md" in shared_contract, "agents: guidance projet non imposée", failures)
    _check("donnée non fiable" in shared_contract, "agents: intake non fiable non documenté", failures)

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print("OK  Intake Integrity: manifeste + SHA-256 + MIME + symlinks + secrets + read-only")
    print("OK  Learning: efficient/balanced/intensive + preuves d'acquisition")
    print("OK  Accessibility: comprendre/utiliser/approfondir/diagnostiquer")
    print("OK  Publication: GitHub/GitLab + CI + clean clone + audit + humain")
    print("OK  Telemetry: local/off-Git/privacy-first + métriques exploitation")
    print("OK  Permissions: architecte producteur d'artefacts, sécurité read-only")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
