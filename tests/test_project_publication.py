from pathlib import Path

import pytest

from clawlocal.project_intake import create_project
from clawlocal.project_publication import (
    load_publication,
    set_publication_evidence,
    transition_publication,
)


def _set_local_checks(project: Path) -> None:
    payload = load_publication(project)
    for key in payload["checks"]:
        set_publication_evidence(project, key=key, value=True)


def test_publication_requires_local_evidence_and_human_gates(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "publish-demo", "Publish Demo")
    assert load_publication(project)["state"] == "LOCAL_IN_PROGRESS"

    with pytest.raises(ValueError):
        transition_publication(
            project,
            "LOCAL_VALIDATED",
            actor="test",
            reason="missing checks",
        )

    _set_local_checks(project)
    transition_publication(
        project,
        "LOCAL_VALIDATED",
        actor="test",
        reason="local gates green",
    )
    transition_publication(
        project,
        "READY_TO_PUBLISH",
        actor="test",
        reason="ready",
    )
    set_publication_evidence(project, key="canonical_forge", value="github")
    set_publication_evidence(
        project,
        key="canonical_repository_url",
        value="https://github.com/example/project",
    )

    with pytest.raises(PermissionError):
        transition_publication(
            project,
            "REMOTE_CREATED",
            actor="test",
            reason="no approval",
        )

    payload = transition_publication(
        project,
        "REMOTE_CREATED",
        actor="human",
        reason="approved remote creation",
        human_approved=True,
    )
    assert payload["state"] == "REMOTE_CREATED"
