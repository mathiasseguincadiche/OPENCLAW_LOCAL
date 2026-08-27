from pathlib import Path

import pytest

from clawlocal.architecture_artifacts import write_architecture_artifact
from clawlocal.project_intake import create_project


def test_architecture_writer_is_scoped(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "arch-demo", "Arch Demo")
    adr = write_architecture_artifact(
        project,
        kind="architecture",
        relative_path="ADR-001.md",
        content="# ADR 001\n",
    )
    diagram = write_architecture_artifact(
        project,
        kind="diagram",
        relative_path="system.d2",
        content="user -> openclaw\n",
    )
    assert adr == project / "context" / "architecture" / "ADR-001.md"
    assert diagram == project / "diagrams" / "system.d2"

    with pytest.raises(ValueError):
        write_architecture_artifact(
            project,
            kind="architecture",
            relative_path="../../sources/pwned.txt",
            content="bad",
        )
