from pathlib import Path

import pytest

from clawlocal.project_publication import (
    initialize_publication,
    record_publication_evidence,
    transition_publication,
)


def _mark_local_checks(project: Path) -> None:
    for key in (
        "local_tests_green",
        "documentation_validated",
        "secret_scan_clean",
        "dependency_scan_reviewed",
        "git_status_reviewed",
        "ignore_rules_reviewed",
        "local_paths_removed",
        "rollback_documented",
        "independent_local_audit",
    ):
        record_publication_evidence(project, key, True)


def test_publication_requires_local_evidence_and_human_remote_gate(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "context").mkdir(parents=True)
    initialize_publication(project)
    with pytest.raises(ValueError):
        transition_publication(project, "LOCAL_VALIDATED", actor="auditeur-qualite")

    _mark_local_checks(project)
    payload = transition_publication(project, "LOCAL_VALIDATED", actor="auditeur-qualite")
    assert payload["state"] == "LOCAL_VALIDATED"

    record_publication_evidence(project, "local_package_reviewed", True)
    transition_publication(project, "READY_TO_PUBLISH", actor="human")
    record_publication_evidence(project, "forge", "github")
    with pytest.raises(PermissionError):
        transition_publication(project, "REMOTE_CREATED", actor="ingenieur-release-forges")
    payload = transition_publication(
        project,
        "REMOTE_CREATED",
        actor="human",
        human_approved=True,
    )
    assert payload["forge"] == "github"
