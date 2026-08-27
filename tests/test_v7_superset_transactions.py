from pathlib import Path

import pytest

import clawlocal.project_intake as project_intake


def test_intake_archive_copy_failure_is_transactional(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "requirements.md"
    source.write_text("safe input", encoding="utf-8")
    platform = tmp_path / "platform"

    def fail_copy(_source: Path, _destination: Path) -> None:
        raise OSError("simulated archive copy failure")

    monkeypatch.setattr(project_intake, "_copy_one", fail_copy)
    with pytest.raises(OSError, match="simulated archive copy failure"):
        project_intake.create_project(
            platform,
            "archive-rollback",
            "Archive Rollback",
            intake_items=[source],
        )

    assert not (platform / "state" / "intake" / "archive-rollback").exists()
    assert not (platform / "projects" / "archive-rollback").exists()


def test_project_build_failure_removes_archive_and_partial_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intake_file = tmp_path / "requirements.md"
    intake_file.write_text("safe input", encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("safe", encoding="utf-8")
    platform = tmp_path / "platform"

    def fail_sources(_items: object, _destination: Path) -> list[str]:
        raise OSError("simulated source copy failure")

    monkeypatch.setattr(project_intake, "_copy_sources", fail_sources)
    with pytest.raises(OSError, match="simulated source copy failure"):
        project_intake.create_project(
            platform,
            "project-rollback",
            "Project Rollback",
            intake_items=[intake_file],
            source_items=[source],
        )

    project_archive_root = platform / "state" / "intake" / "project-rollback"
    if project_archive_root.exists():
        assert list(project_archive_root.iterdir()) == []
    assert not (platform / "projects" / "project-rollback").exists()
