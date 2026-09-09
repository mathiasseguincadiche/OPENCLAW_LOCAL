from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

from clawlocal.project_context import collect_agent_outputs, sync_project_context
from clawlocal.project_ingestion import ingest_project_documents
from clawlocal.project_intake import create_project
from clawlocal.project_integrity import snapshot_integrity, verify_integrity_snapshot
from clawlocal.project_security import build_support_bundle
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


def test_support_bundle_rejects_linked_orchestration_file(tmp_path: Path) -> None:
    _require_symlink_support(tmp_path)
    project = create_project(tmp_path / "platform", "support-link-demo", "Support Link")
    orchestration = project / "evidence" / "orchestration"
    orchestration.mkdir(parents=True)
    outside = tmp_path / "outside-support.txt"
    outside.write_text("PRIVATE", encoding="utf-8")
    (orchestration / "escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="lien|reparse"):
        build_support_bundle(project, tmp_path / "support.zip")


def test_integrity_rejects_scope_outside_project(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "integrity-scope", "Integrity Scope")
    outside = tmp_path / "outside.txt"
    outside.write_text("PRIVATE", encoding="utf-8")

    with pytest.raises(ValueError, match="hors projet"):
        snapshot_integrity(project, "TEST", roots=["../outside.txt"])


def test_integrity_detects_added_file(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "integrity-added", "Integrity Added")
    snapshot = snapshot_integrity(project, "TEST", roots=["deliverables"])
    (project / "deliverables" / "new.txt").write_text("new", encoding="utf-8")

    assert verify_integrity_snapshot(project, snapshot) == ["ajouté: deliverables/new.txt"]


def test_integrity_rejects_unsafe_snapshot_record(tmp_path: Path) -> None:
    project = create_project(tmp_path / "platform", "integrity-record", "Integrity Record")
    deliverable = project / "deliverables" / "result.txt"
    deliverable.write_text("safe", encoding="utf-8")
    snapshot = snapshot_integrity(project, "TEST", roots=["deliverables"])
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    payload["files"][0]["path"] = "../outside.txt"
    snapshot.write_text(json.dumps(payload), encoding="utf-8")

    failures = verify_integrity_snapshot(project, snapshot)
    assert "chemin non sûr: ../outside.txt" in failures


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
    (outside / "secret.txt").write_text("PRIVATE", encoding="utf-8")
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

    project = create_project(tmp_path / "platform", "junction-project", "Junction Project")
    orchestration = project / "evidence" / "orchestration"
    orchestration.mkdir(parents=True)
    support_junction = orchestration / "junction"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(support_junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("création de junction support indisponible sur ce runner")
    try:
        with pytest.raises(ValueError, match="lien|reparse"):
            build_support_bundle(project, tmp_path / "support-junction.zip")
    finally:
        subprocess.run(
            ["cmd.exe", "/c", "rmdir", str(support_junction)],
            capture_output=True,
            text=True,
            check=False,
        )

    deliverable_junction = project / "deliverables" / "junction"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(deliverable_junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("création de junction intégrité indisponible sur ce runner")
    try:
        with pytest.raises(ValueError, match="lien|reparse"):
            snapshot_integrity(project, "JUNCTION", roots=["deliverables"])
    finally:
        subprocess.run(
            ["cmd.exe", "/c", "rmdir", str(deliverable_junction)],
            capture_output=True,
            text=True,
            check=False,
        )
