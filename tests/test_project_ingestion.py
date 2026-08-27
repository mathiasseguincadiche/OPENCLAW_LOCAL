from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from clawlocal.project_ingestion import (
    ingest_project_documents,
    validate_ingestion_index,
    validate_source_coverage,
)

_METHOD_BY_KIND = {
    "pdf": "pdf",
    "image": "view_image",
    "docx": "local_zip_xml_extract",
    "pptx": "local_zip_xml_extract",
    "xlsx": "local_zip_xml_extract",
    "text": "local_text_extract",
    "unknown": "raw_file",
}


def _write_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<w:document xmlns:w="urn:w"><w:body><w:p><w:r>'
                '<w:t>Bonjour DOCX</w:t></w:r></w:p></w:body></w:document>'
            ),
        )


def _write_pptx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml",
            (
                '<p:sld xmlns:p="urn:p" xmlns:a="urn:a"><p:cSld><a:p><a:r>'
                '<a:t>Slide locale</a:t></a:r></a:p></p:cSld></p:sld>'
            ),
        )


def _write_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="urn:x"><si><t>Valeur partagée</t></si></sst>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<worksheet xmlns="urn:x"><sheetData><row>'
                '<c r="A1" t="s"><v>0</v></c>'
                '<c r="B1"><f>1+1</f><v>2</v></c>'
                '</row></sheetData></worksheet>'
            ),
        )


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    intake = project / "intake"
    intake.mkdir(parents=True)
    (intake / "notes.md").write_text("# Notes\nTexte local\n", encoding="utf-8")
    (intake / "brief.pdf").write_bytes(b"%PDF-1.4\n% local test\n")
    (intake / "schema.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (intake / "opaque.bin").write_bytes(b"\x00\x01\x02")
    _write_docx(intake / "document.docx")
    _write_pptx(intake / "slides.pptx")
    _write_xlsx(intake / "tableau.xlsx")
    return project


def test_ingestion_indexes_multimodal_and_office_files(tmp_path: Path) -> None:
    project = _project(tmp_path)
    index_path = ingest_project_documents(project)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    entries = {entry["relative_path"]: entry for entry in payload["entries"]}

    assert entries["brief.pdf"]["tool"] == "pdf"
    assert entries["brief.pdf"]["status"] == "READY_TOOL"
    assert entries["schema.png"]["tool"] == "view_image"
    assert entries["schema.png"]["status"] == "READY_TOOL"
    assert entries["notes.md"]["status"] == "READY_TEXT"
    assert entries["opaque.bin"]["status"] == "INVENTORY_ONLY"

    for name, expected in (
        ("document.docx", "Bonjour DOCX"),
        ("slides.pptx", "Slide locale"),
        ("tableau.xlsx", "A1: Valeur partagée"),
    ):
        derived = project / entries[name]["derived_path"]
        text = derived.read_text(encoding="utf-8")
        assert expected in text
        assert "source de vérité" in text

    validated = validate_ingestion_index(project)
    assert validated["entry_count"] == 7


def test_source_coverage_requires_every_document(tmp_path: Path) -> None:
    project = _project(tmp_path)
    payload = json.loads(ingest_project_documents(project).read_text(encoding="utf-8"))
    coverage = []
    missing_information: list[str] = []
    for entry in payload["entries"]:
        status = "UNREADABLE" if entry["kind"] == "unknown" else "READ"
        coverage.append(
            {
                "document_id": entry["document_id"],
                "status": status,
                "method": _METHOD_BY_KIND[entry["kind"]],
                "notes": "test",
            }
        )
        if status == "UNREADABLE":
            missing_information.append(
                f"{entry['document_id']} ({entry['source_path']}) ne peut pas être lu"
            )

    normalized = validate_source_coverage(project, coverage, missing_information)
    assert len(normalized) == 7
    assert {item["status"] for item in normalized} >= {"READ", "UNREADABLE"}

    with pytest.raises(ValueError, match="source_coverage incomplet"):
        validate_source_coverage(project, coverage[:-1], missing_information)


def test_unreadable_document_must_be_reported(tmp_path: Path) -> None:
    project = _project(tmp_path)
    payload = json.loads(ingest_project_documents(project).read_text(encoding="utf-8"))
    coverage = [
        {
            "document_id": entry["document_id"],
            "status": "UNREADABLE",
            "method": _METHOD_BY_KIND[entry["kind"]],
            "notes": "illisible",
        }
        for entry in payload["entries"]
    ]

    with pytest.raises(ValueError, match="missing_information"):
        validate_source_coverage(project, coverage, [])


def test_source_coverage_rejects_method_incompatible_with_document_kind(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    payload = json.loads(ingest_project_documents(project).read_text(encoding="utf-8"))
    pdf = next(entry for entry in payload["entries"] if entry["kind"] == "pdf")

    with pytest.raises(ValueError, match="incompatible"):
        validate_source_coverage(
            project,
            [
                {
                    "document_id": pdf["document_id"],
                    "status": "READ",
                    "method": "raw_file",
                    "notes": "méthode volontairement incorrecte",
                }
            ],
            [],
        )


def test_stale_ingestion_index_is_rejected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ingest_project_documents(project)
    (project / "intake" / "notes.md").write_text("modifié", encoding="utf-8")

    with pytest.raises(ValueError, match="périmé"):
        validate_ingestion_index(project)
