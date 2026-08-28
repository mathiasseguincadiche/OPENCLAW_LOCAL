from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from clawlocal.project_context import collect_agent_outputs, sync_project_context
from clawlocal.project_ingestion import ingest_project_documents
from clawlocal.project_intake import create_project
from clawlocal.safe_fs import secure_path_within


def _require_symlink_support(tmp_path: Path) -> None:
    target = tmp_path / "symlink-probe-target"
    link = tmp_path / "symlink-probe-link"
    target.write_text("probe", encoding="utf-8")
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("création de symlink non autorisée sur ce runner")
    finally:
        try:
            link.unlink()
        except FileNotFoundError:
            pass
        target.unlink(missing_ok=True)


def test_project_sources_reject_nested_symlink(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    source = tmp_path / "repo"
    source.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("PRIVATE", encoding="utf-8")
    (source / "escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="lien|reparse"):
        create_project(
            tmp_path / "platform",
            "source-link-demo",
            "Source Link Demo",
            source_items=[source],
        )


def test_agent_output_collection_rejects_symlink(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    root = tmp_path / "platform"
    create_project(root, "output-link-demo", "Output Link Demo")
    snapshot = sync_project_context(root, "output-link-demo", "ingenieur-devops")
    outside = tmp_path / "outside-output.txt"
    outside.write_text("SECRET", encoding="utf-8")
    output_dir = snapshot / "deliverables" / "task-001"
    output_dir.mkdir(parents=True)
    (output_dir / "escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="lien|reparse"):
        collect_agent_outputs(
            root,
            "output-link-demo",
            "ingenieur-devops",
            "task-001",
        )


def test_secure_path_rejects_link_component(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("SECRET", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="lien|reparse"):
        secure_path_within(
            root / "linked" / "secret.txt",
            root,
            require_file=True,
            label="test",
        )


def test_office_high_compression_ratio_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    intake = project / "intake"
    intake.mkdir(parents=True)
    archive_path = intake / "bomb.docx"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", b"A" * (2 * 1024 * 1024))

    with pytest.raises(ValueError, match="ratio de compression"):
        ingest_project_documents(project)


def test_windows_junction_is_rejected_when_available(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("test spécifique Windows")
    import subprocess

    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    junction = root / "junction"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("création de junction non disponible sur ce runner")

    with pytest.raises(ValueError, match="lien|reparse"):
        secure_path_within(junction, root, require_dir=True, label="junction")
