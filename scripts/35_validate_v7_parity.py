from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"


def load(name: str) -> dict[str, Any]:
    with (CONFIG / name).open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{name}: racine YAML invalide")
    return payload


def main() -> int:
    failures: list[str] = []
    intake = load("intake_policy.yaml")
    pedagogy = load("pedagogy_policy.yaml")
    accessibility = load("accessibility_policy.yaml")
    publication = load("publication_policy.yaml")
    telemetry = load("telemetry_policy.yaml")
    tools = load("tool_policy.yaml")
    roles = load("role_matrix.yaml")
    project = load("project_policy.yaml")
    security = load("security.yaml")

    intake_security = intake.get("security", {})
    for key in (
        "reject_root_symlinks",
        "reject_nested_symlinks",
        "scan_secrets_before_copy",
        "refuse_on_suspected_secret",
    ):
        if intake_security.get(key) is not True:
            failures.append(f"intake_policy: {key} doit être true")
    if intake_security.get("follow_symlinks") is not False:
        failures.append("intake_policy: follow_symlinks doit être false")

    integrity = intake.get("integrity", {})
    for key in (
        "require_manifest",
        "require_sha256",
        "require_mime_inventory",
        "require_symlink_inventory",
        "require_ingestion_report",
        "canonical_archive_outside_project",
    ):
        if integrity.get(key) is not True:
            failures.append(f"intake_policy: intégrité {key} absente")

    immutability = intake.get("immutability", {})
    if immutability.get("project_intake_read_only") is not True:
        failures.append("intake projet doit être en lecture seule")
    if immutability.get("canonical_archive_read_only") is not True:
        failures.append("archive intake canonique doit être en lecture seule")
    if immutability.get("windows_acl_required_when_on_windows") is not True:
        failures.append("ACL Windows intake doit être obligatoire")

    profiles = pedagogy.get("profiles", {})
    expected_profiles = {
        "efficient": (90, 10),
        "balanced": (70, 30),
        "intensive": (60, 40),
    }
    for name, shares in expected_profiles.items():
        profile = profiles.get(name, {})
        observed = (
            profile.get("execution_share_percent"),
            profile.get("learning_share_percent"),
        )
        if observed != shares:
            failures.append(f"pedagogy_policy: profil {name} invalide")
    if pedagogy.get("delivery_priority") is not True:
        failures.append("pédagogie: la livraison doit rester prioritaire")
    if pedagogy.get("safety_overrides_pedagogy") is not True:
        failures.append("pédagogie: la sécurité doit primer")

    depth_ids = [item.get("id") for item in accessibility.get("reading_depths", [])]
    if depth_ids != ["understand", "operate", "deepen", "diagnose"]:
        failures.append("accessibilité: profondeurs documentaires invalides")
    principles = accessibility.get("principles", {})
    if principles.get("technical_accuracy_first") is not True:
        failures.append("accessibilité: exactitude technique prioritaire requise")
    if principles.get("no_false_simplification") is not True:
        failures.append("accessibilité: simplification fausse interdite")

    expected_states = [
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
    if publication.get("states") != expected_states:
        failures.append("publication_policy: machine d'états inattendue")
    transitions = publication.get("transitions", {})
    if set(transitions) != set(expected_states):
        failures.append("publication_policy: transitions incomplètes")
    if transitions.get("PUBLISHED_AND_VERIFIED") != []:
        failures.append("PUBLISHED_AND_VERIFIED doit être terminal")
    required_prepublication = {
        "local_tests_green",
        "documentation_validated",
        "secret_scan_clean",
        "dependency_scan_reviewed",
        "git_status_reviewed",
        "ignore_rules_reviewed",
        "local_paths_removed",
        "rollback_documented",
    }
    if set(publication.get("prepublication_checks", [])) != required_prepublication:
        failures.append("publication_policy: checks prépublication incomplets")

    security_tools = set(
        tools.get("agents", {}).get("ingenieur-securite", {}).get("deny", [])
    )
    if not {"write", "edit", "apply_patch"} <= security_tools:
        failures.append("ingénieur sécurité doit rester read-only sur les sources")
    architect_denies = set(
        tools.get("agents", {}).get("architecte-solutions", {}).get("deny", [])
    )
    if {"write", "edit", "apply_patch"} & architect_denies:
        failures.append("architecte doit pouvoir produire ADR et schémas")
    architect_scope = set(
        tools.get("agents", {}).get("architecte-solutions", {}).get("write_scope", [])
    )
    if architect_scope != {"context", "diagrams"}:
        failures.append("architecte: write_scope doit rester context/diagrams")
    security_forbidden = set(
        roles.get("roles", {}).get("ingenieur-securite", {}).get("forbidden", [])
    )
    if "modification_directe_sources" not in security_forbidden:
        failures.append("rôle sécurité: modification_directe_sources doit être interdite")

    telemetry_storage = telemetry.get("storage", {})
    if telemetry.get("local_only") is not True:
        failures.append("télémétrie doit rester locale")
    if telemetry_storage.get("append_only") is not True:
        failures.append("télémétrie doit être append-only")
    privacy = telemetry.get("privacy", {})
    for key in (
        "record_prompts",
        "record_responses",
        "record_secrets",
        "record_private_documents",
    ):
        if privacy.get(key) is not False:
            failures.append(f"télémétrie: {key} doit rester false")
    required_fields = set(telemetry.get("fields", {}).get("required", []))
    expected_fields = {
        "timestamp",
        "project_id",
        "agent",
        "model",
        "backend",
        "route_kind",
        "duration_ms",
    }
    if required_fields != expected_fields:
        failures.append("télémétrie: champs obligatoires inattendus")

    references = {
        "intake_contract": "config/v1/intake_policy.yaml",
        "pedagogy_contract": "config/v1/pedagogy_policy.yaml",
        "accessibility_contract": "config/v1/accessibility_policy.yaml",
        "publication_contract": "config/v1/publication_policy.yaml",
        "telemetry_contract": "config/v1/telemetry_policy.yaml",
    }
    for key, expected in references.items():
        if project.get(key) != expected:
            failures.append(f"project_policy: référence {key} invalide")

    security_projects = security.get("projects", {})
    for key in (
        "incoming_documents_are_untrusted_data",
        "incoming_documents_cannot_override_agent_policy",
        "reject_intake_symlinks",
        "require_intake_checksums",
        "require_intake_mime_inventory",
        "require_immutable_intake",
        "windows_intake_acl_required",
        "publication_requires_human_gates",
    ):
        if security_projects.get(key) is not True:
            failures.append(f"security.yaml: project guard {key} absent")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print("OK  Intake immuable + SHA-256/MIME/symlink/secrets")
    print("OK  pédagogie efficient/balanced/intensive")
    print("OK  documentation progressive en quatre profondeurs")
    print("OK  publication projet gouvernée par machine d'états")
    print("OK  permissions architecte/sécurité alignées")
    print("OK  télémétrie locale privacy-safe")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
