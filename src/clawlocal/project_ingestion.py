from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from clawlocal.config import load_contract

_DOC_ID_RE = re.compile(r"[^a-z0-9]+")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _policy() -> dict[str, Any]:
    return load_contract("document_ingestion_policy.yaml")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _iter_intake_files(project: Path) -> list[Path]:
    root = project / "intake"
    if not root.is_dir():
        raise FileNotFoundError(root)
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"ingestion: lien symbolique interdit: {path}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _extension_set(policy: dict[str, Any], kind: str) -> set[str]:
    values = policy.get("formats", {}).get(kind, {}).get("extensions", [])
    if not isinstance(values, list):
        raise ValueError(f"document_ingestion_policy: extensions {kind} invalides")
    return {str(value).casefold() for value in values}


def _classify(path: Path, policy: dict[str, Any]) -> tuple[str, str, str | None]:
    suffix = path.suffix.casefold()
    name = path.name.casefold()
    if suffix in _extension_set(policy, "pdf"):
        entry = policy["formats"]["pdf"]
        return "pdf", str(entry["method"]), str(entry["tool"])
    if suffix in _extension_set(policy, "image"):
        entry = policy["formats"]["image"]
        return "image", str(entry["method"]), str(entry["tool"])
    if suffix in _extension_set(policy, "office_text"):
        return "docx", "local_zip_xml_extract", None
    if suffix in _extension_set(policy, "office_slides"):
        return "pptx", "local_zip_xml_extract", None
    if suffix in _extension_set(policy, "office_sheet"):
        return "xlsx", "local_zip_xml_extract", None
    if suffix in _extension_set(policy, "text") or name in {"dockerfile", "makefile"}:
        return "text", "local_text_extract", None
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if mime.startswith("text/"):
        return "text", "local_text_extract", None
    return "unknown", "inventory_only", None


def _document_id(relative: str) -> str:
    stem = _DOC_ID_RE.sub("-", Path(relative).stem.casefold()).strip("-") or "document"
    stem = stem[:36].rstrip("-")
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:10]
    return f"doc-{stem}-{digest}"


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    marker = "\n\n[TRUNCATED_BY_LOCAL_INGESTION_POLICY]\n"
    return text[: max(0, limit - len(marker))] + marker, True


def _extract_text_file(path: Path, limit: int) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return _truncate(text, limit)


def _xml_paragraphs(data: bytes) -> list[str]:
    root = ElementTree.fromstring(data)
    paragraphs: list[str] = []
    for element in root.iter():
        if not (element.tag.endswith("}p") or element.tag == "p"):
            continue
        parts = [
            str(child.text)
            for child in element.iter()
            if (child.tag.endswith("}t") or child.tag == "t") and child.text
        ]
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)
    return paragraphs


def _extract_docx(path: Path, limit: int) -> tuple[str, bool]:
    sections: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if name == "word/document.xml"
            or name.startswith("word/header")
            or name.startswith("word/footer")
            or name in {
                "word/footnotes.xml",
                "word/endnotes.xml",
                "word/comments.xml",
            }
        )
        if "word/document.xml" not in names:
            raise ValueError(f"DOCX invalide: {path.name}")
        for name in names:
            paragraphs = _xml_paragraphs(archive.read(name))
            if paragraphs:
                sections.append(f"## {name}\n\n" + "\n\n".join(paragraphs))
    return _truncate("\n\n".join(sections), limit)


def _slide_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"slide(\d+)\.xml$", name)
    return (int(match.group(1)) if match else 10**9, name)


def _extract_pptx(path: Path, limit: int) -> tuple[str, bool]:
    sections: list[str] = []
    with zipfile.ZipFile(path) as archive:
        slides = sorted(
            (
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ),
            key=_slide_sort_key,
        )
        if not slides:
            raise ValueError(f"PPTX invalide: {path.name}")
        for index, name in enumerate(slides, start=1):
            paragraphs = _xml_paragraphs(archive.read(name))
            sections.append(f"## Slide {index}\n\n" + "\n\n".join(paragraphs))
    return _truncate("\n\n".join(sections), limit)


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.iter():
        if not (item.tag.endswith("}si") or item.tag == "si"):
            continue
        parts = [
            str(child.text)
            for child in item.iter()
            if (child.tag.endswith("}t") or child.tag == "t") and child.text
        ]
        values.append("".join(parts))
    return values


def _child_text(element: ElementTree.Element, suffix: str) -> str | None:
    for child in element.iter():
        if child.tag.endswith(suffix) or child.tag == suffix.lstrip("}"):
            if child.text is not None:
                return str(child.text)
    return None


def _extract_xlsx(path: Path, limit: int) -> tuple[str, bool]:
    sections: list[str] = []
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheets = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        if not sheets:
            raise ValueError(f"XLSX invalide: {path.name}")
        for index, name in enumerate(sheets, start=1):
            root = ElementTree.fromstring(archive.read(name))
            cells: list[str] = []
            for cell in root.iter():
                if not (cell.tag.endswith("}c") or cell.tag == "c"):
                    continue
                coordinate = cell.attrib.get("r", "?")
                cell_type = cell.attrib.get("t", "")
                formula = _child_text(cell, "}f")
                value = _child_text(cell, "}v")
                if cell_type == "s" and value is not None:
                    try:
                        rendered = shared[int(value)]
                    except (ValueError, IndexError):
                        rendered = value
                elif cell_type == "inlineStr":
                    rendered = _child_text(cell, "}t") or ""
                else:
                    rendered = value or ""
                if formula:
                    cells.append(f"{coordinate}: ={formula} -> {rendered}")
                elif rendered:
                    cells.append(f"{coordinate}: {rendered}")
            sections.append(f"## Worksheet {index}\n\n" + "\n".join(cells))
    return _truncate("\n\n".join(sections), limit)


def _extract_office(path: Path, kind: str, limit: int) -> tuple[str, bool]:
    try:
        if kind == "docx":
            return _extract_docx(path, limit)
        if kind == "pptx":
            return _extract_pptx(path, limit)
        if kind == "xlsx":
            return _extract_xlsx(path, limit)
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError(f"document Office illisible: {path.name}") from exc
    raise ValueError(f"format Office inconnu: {kind}")


def _derived_header(entry: dict[str, Any]) -> str:
    return (
        "# Représentation dérivée locale\n\n"
        f"- Original immuable : `{entry['source_path']}`\n"
        f"- SHA-256 original : `{entry['sha256']}`\n"
        f"- MIME : `{entry['mime']}`\n"
        f"- Méthode : `{entry['method']}`\n\n"
        "Cette représentation n'est pas une nouvelle source de vérité. En cas de divergence, "
        "l'original sous `intake/` prévaut.\n\n"
    )


def ingest_project_documents(project: Path, *, force: bool = False) -> Path:
    policy = _policy()
    root = project / str(policy.get("artifact_root", "context/ingestion"))
    index_path = project / str(policy.get("index_path", "context/ingestion/index.json"))
    if root.exists():
        if not force:
            raise FileExistsError(f"ingestion déjà présente: {root}")
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=False)

    limit = int(policy.get("extraction", {}).get("max_text_characters_per_file", 2_000_000))
    intake_root = project / "intake"
    entries: list[dict[str, Any]] = []
    aggregate = hashlib.sha256()

    for path in _iter_intake_files(project):
        relative = path.relative_to(intake_root).as_posix()
        document_id = _document_id(relative)
        kind, method, tool = _classify(path, policy)
        digest = _sha256(path)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        entry: dict[str, Any] = {
            "document_id": document_id,
            "source_path": f"intake/{relative}",
            "relative_path": relative,
            "sha256": digest,
            "size": path.stat().st_size,
            "mime": mime,
            "kind": kind,
            "method": method,
            "tool": tool,
            "status": "INVENTORY_ONLY",
            "derived_path": None,
            "truncated": False,
        }
        document_root = root / document_id
        document_root.mkdir(parents=True, exist_ok=False)

        if kind == "text":
            text, truncated = _extract_text_file(path, limit)
            derived = document_root / "extracted.md"
            entry["status"] = "PARTIAL_TEXT" if truncated else "READY_TEXT"
            entry["derived_path"] = derived.relative_to(project).as_posix()
            entry["truncated"] = truncated
            derived.write_text(_derived_header(entry) + text, encoding="utf-8")
        elif kind in {"docx", "pptx", "xlsx"}:
            text, truncated = _extract_office(path, kind, limit)
            derived = document_root / "extracted.md"
            entry["status"] = "PARTIAL_TEXT" if truncated else "READY_TEXT"
            entry["derived_path"] = derived.relative_to(project).as_posix()
            entry["truncated"] = truncated
            derived.write_text(_derived_header(entry) + text, encoding="utf-8")
        elif kind == "pdf":
            entry["status"] = "READY_TOOL"
            guide = document_root / "tool.md"
            entry["derived_path"] = guide.relative_to(project).as_posix()
            guide.write_text(
                _derived_header(entry)
                + "Utiliser l'outil OpenClaw `pdf` sur le chemin original. Pour un document long, "
                "traiter toutes les pages par tranches conformes à la limite de l'outil. Le mode "
                "de secours OpenClaw extrait le texte et rend les pages pauvres en texte en images "
                "pour un modèle vision.\n",
                encoding="utf-8",
            )
        elif kind == "image":
            entry["status"] = "READY_TOOL"
            guide = document_root / "tool.md"
            entry["derived_path"] = guide.relative_to(project).as_posix()
            guide.write_text(
                _derived_header(entry)
                + "Utiliser l'outil OpenClaw `view_image` sur le chemin original. Décrire les "
                "éléments utiles au projet sans inventer le texte ou les détails illisibles.\n",
                encoding="utf-8",
            )
        else:
            guide = document_root / "tool.md"
            entry["derived_path"] = guide.relative_to(project).as_posix()
            guide.write_text(
                _derived_header(entry)
                + "Format non normalisé. Lire le fichier original avec un outil compatible si le "
                "rôle en dispose; sinon le déclarer UNREADABLE dans source_coverage.\n",
                encoding="utf-8",
            )

        _write_json(document_root / "metadata.json", entry)
        aggregate.update(f"{relative}\0{digest}\0{kind}\0{method}\n".encode())
        entries.append(entry)

    payload = {
        "schema_version": "1.0.0",
        "generated_at": _now(),
        "source_root": "intake",
        "originals_immutable": True,
        "entry_count": len(entries),
        "aggregate_sha256": aggregate.hexdigest(),
        "entries": entries,
    }
    _write_json(index_path, payload)
    summary = root / "README.md"
    summary.write_text(
        "# Document Ingestion\n\n"
        "Les originaux sous `intake/` sont immuables et restent la source de vérité. "
        "Cette couche indexe chaque fichier et fournit une représentation locale ou "
        "l'outil OpenClaw à utiliser.\n\n"
        f"- Documents indexés : **{len(entries)}**\n"
        f"- Digest agrégé : `{payload['aggregate_sha256']}`\n"
        "- PDF : outil `pdf` (texte + fallback vision pour pages scannées)\n"
        "- Images : outil `view_image`\n"
        "- DOCX/PPTX/XLSX/texte : extraction locale déterministe\n",
        encoding="utf-8",
    )
    return index_path


def load_ingestion_index(project: Path) -> dict[str, Any]:
    policy = _policy()
    path = project / str(policy.get("index_path", "context/ingestion/index.json"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError("index d'ingestion invalide")
    return payload


def validate_ingestion_index(project: Path) -> dict[str, Any]:
    payload = load_ingestion_index(project)
    indexed: dict[str, str] = {}
    for raw in payload["entries"]:
        if not isinstance(raw, dict):
            raise ValueError("index d'ingestion: entrée invalide")
        relative = str(raw.get("relative_path", ""))
        digest = str(raw.get("sha256", ""))
        if not relative or not digest or relative in indexed:
            raise ValueError("index d'ingestion: chemin/digest invalide ou dupliqué")
        indexed[relative] = digest

    intake_root = project / "intake"
    observed = {
        path.relative_to(intake_root).as_posix(): _sha256(path)
        for path in _iter_intake_files(project)
    }
    if indexed != observed:
        raise ValueError("index d'ingestion périmé: intake modifié ou représentation incomplète")
    return payload


def _expected_coverage_method(entry: dict[str, Any]) -> str:
    kind = str(entry.get("kind", ""))
    return {
        "pdf": "pdf",
        "image": "view_image",
        "docx": "local_zip_xml_extract",
        "pptx": "local_zip_xml_extract",
        "xlsx": "local_zip_xml_extract",
        "text": "local_text_extract",
        "unknown": "raw_file",
    }.get(kind, "raw_file")


def validate_source_coverage(
    project: Path,
    coverage: list[Any],
    missing_information: list[Any],
) -> list[dict[str, str]]:
    index = validate_ingestion_index(project)
    expected = {
        str(entry["document_id"]): entry
        for entry in index["entries"]
        if isinstance(entry, dict)
    }
    normalized: dict[str, dict[str, str]] = {}
    allowed_statuses = {str(value) for value in _policy().get("coverage_statuses", [])}
    allowed_methods = {str(value) for value in _policy().get("coverage_methods", [])}

    for raw in coverage:
        if not isinstance(raw, dict):
            raise ValueError("source_coverage: chaque entrée doit être un objet")
        document_id = str(raw.get("document_id", "")).strip()
        status = str(raw.get("status", "")).strip().upper()
        method = str(raw.get("method", "")).strip()
        notes = str(raw.get("notes", "")).strip()
        if document_id not in expected:
            raise ValueError(f"source_coverage: document inconnu: {document_id}")
        if document_id in normalized:
            raise ValueError(f"source_coverage: document dupliqué: {document_id}")
        if status not in allowed_statuses:
            raise ValueError(f"source_coverage: statut invalide pour {document_id}: {status}")
        if method not in allowed_methods:
            raise ValueError(f"source_coverage: méthode invalide pour {document_id}: {method}")
        expected_method = _expected_coverage_method(expected[document_id])
        if method != expected_method:
            raise ValueError(
                f"source_coverage: méthode {method} incompatible avec {document_id}; "
                f"attendu: {expected_method}"
            )
        expected_path = str(expected[document_id].get("source_path", ""))
        normalized[document_id] = {
            "document_id": document_id,
            "path": expected_path,
            "status": status,
            "method": method,
            "notes": notes,
        }

    missing_ids = sorted(set(expected) - set(normalized))
    if missing_ids:
        raise ValueError("source_coverage incomplet: " + ", ".join(missing_ids))

    missing_text = "\n".join(str(value) for value in missing_information).casefold()
    for document_id, item in normalized.items():
        if item["status"] != "UNREADABLE":
            continue
        source_path = item["path"]
        document_missing = document_id.casefold() in missing_text
        path_missing = source_path.casefold() in missing_text
        if not document_missing and not path_missing:
            raise ValueError(
                f"source_coverage: {document_id} UNREADABLE doit aussi apparaître dans "
                "missing_information"
            )
    return [normalized[key] for key in sorted(normalized)]
