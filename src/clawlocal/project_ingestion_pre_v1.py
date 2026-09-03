from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from clawlocal.config import load_contract
from clawlocal.project_ingestion import load_ingestion_index, validate_ingestion_index
from clawlocal.safe_archive import safe_extract_zip


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _archive_extensions() -> set[str]:
    policy = load_contract("document_ingestion_policy.yaml")
    values = policy.get("formats", {}).get("archive", {}).get("extensions", [".zip"])
    return {str(value).casefold() for value in values}


def _archive_safety() -> dict[str, Any]:
    policy = load_contract("document_ingestion_policy.yaml")
    value = policy.get("extraction", {}).get("generic_archive_safety", {})
    if not isinstance(value, dict):
        raise ValueError("document_ingestion_policy: generic_archive_safety invalide")
    return value


def _member_manifest_digest(members: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for member in members:
        digest.update(
            (
                f"{member['member_path']}\0{member['sha256']}\0{member['size']}\0"
                f"{member['kind']}\n"
            ).encode()
        )
    return digest.hexdigest()


def ensure_secure_generic_zip_ingestion(project: Path) -> Path:
    """Upgrade top-level generic ZIP entries into safe derived archive manifests.

    The immutable ZIP stays under intake/. Extracted members live only in context/ingestion/.
    Existing non-ZIP ingestion behavior remains untouched.
    """
    validate_ingestion_index(project)
    index_path = project / "context" / "ingestion" / "index.json"
    payload = load_ingestion_index(project)
    extensions = _archive_extensions()
    changed = False

    for raw in payload.get("entries", []):
        if not isinstance(raw, dict):
            continue
        relative = str(raw.get("relative_path", ""))
        if Path(relative).suffix.casefold() not in extensions:
            continue
        source = project / "intake" / relative
        document_id = str(raw.get("document_id", ""))
        if not document_id:
            raise ValueError(f"ZIP sans document_id dans l'index: {relative}")
        document_root = project / "context" / "ingestion" / document_id
        extraction_root = document_root / "archive"
        manifest_path = document_root / "archive_manifest.json"
        guide_path = document_root / "archive.md"

        if (
            raw.get("kind") == "zip"
            and manifest_path.is_file()
            and extraction_root.is_dir()
        ):
            continue
        if extraction_root.exists():
            import shutil

            shutil.rmtree(extraction_root)
        members = safe_extract_zip(source, extraction_root, _archive_safety())
        enriched: list[dict[str, Any]] = []
        for member in members:
            item = dict(member)
            member_path = extraction_root / Path(
                *str(member["member_path"]).split("/")
            )
            item["derived_path"] = member_path.relative_to(project).as_posix()
            enriched.append(item)

        manifest = {
            "schema_version": "1.0.0",
            "document_id": document_id,
            "source_path": str(raw.get("source_path", f"intake/{relative}")),
            "source_sha256": str(raw.get("sha256", "")),
            "member_count": len(enriched),
            "members_sha256": _member_manifest_digest(enriched),
            "nested_archives_recursive": False,
            "members": enriched,
        }
        _write_json(manifest_path, manifest)
        lines = [
            "# Archive ZIP dérivée sécurisée",
            "",
            f"- Original immuable : `{manifest['source_path']}`",
            f"- SHA-256 original : `{manifest['source_sha256']}`",
            f"- Membres extraits : **{len(enriched)}**",
            f"- Digest du manifeste membres : `{manifest['members_sha256']}`",
            "- Archives imbriquées : inventoriées mais jamais extraites récursivement.",
            "",
            (
                "Les membres sont des représentations dérivées. "
                "L'archive originale reste la source de vérité."
            ),
            "",
            "| Membre | Type | Taille | SHA-256 |",
            "|---|---|---:|---|",
        ]
        for member in enriched:
            lines.append(
                "| `{path}` | {kind} | {size} | `{digest}` |".format(
                    path=member["member_path"],
                    kind=member["kind"],
                    size=member["size"],
                    digest=member["sha256"],
                )
            )
        guide_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        raw["kind"] = "zip"
        raw["method"] = "local_safe_archive_extract"
        raw["tool"] = None
        raw["status"] = "READY_ARCHIVE"
        raw["derived_path"] = guide_path.relative_to(project).as_posix()
        raw["archive_manifest_path"] = manifest_path.relative_to(project).as_posix()
        raw["member_count"] = len(enriched)
        changed = True

    if changed:
        payload["schema_version"] = "1.1.0"
        _write_json(index_path, payload)
    return index_path


def _expected_method(entry: dict[str, Any]) -> str:
    kind = str(entry.get("kind", ""))
    return {
        "pdf": "pdf",
        "image": "view_image",
        "docx": "local_zip_xml_extract",
        "pptx": "local_zip_xml_extract",
        "xlsx": "local_zip_xml_extract",
        "zip": "local_safe_archive_extract",
        "text": "local_text_extract",
        "unknown": "raw_file",
    }.get(kind, "raw_file")


def validate_source_coverage_pre_v1(
    project: Path,
    coverage: list[Any],
    missing_information: list[Any],
) -> list[dict[str, str]]:
    ensure_secure_generic_zip_ingestion(project)
    index = validate_ingestion_index(project)
    expected = {
        str(entry["document_id"]): entry
        for entry in index["entries"]
        if isinstance(entry, dict)
    }
    policy = load_contract("document_ingestion_policy.yaml")
    allowed_statuses = {str(value) for value in policy.get("coverage_statuses", [])}
    allowed_methods = {str(value) for value in policy.get("coverage_methods", [])}
    normalized: dict[str, dict[str, str]] = {}

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
            raise ValueError(
                f"source_coverage: statut invalide pour {document_id}: {status}"
            )
        if method not in allowed_methods:
            raise ValueError(
                f"source_coverage: méthode invalide pour {document_id}: {method}"
            )
        expected_method = _expected_method(expected[document_id])
        if method != expected_method:
            raise ValueError(
                f"source_coverage: méthode {method} incompatible avec {document_id}; "
                f"attendu: {expected_method}"
            )
        normalized[document_id] = {
            "document_id": document_id,
            "path": str(expected[document_id].get("source_path", "")),
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
        source_missing = source_path.casefold() in missing_text
        if not document_missing and not source_missing:
            raise ValueError(
                f"source_coverage: {document_id} UNREADABLE doit aussi apparaître "
                "dans missing_information"
            )
    return [normalized[key] for key in sorted(normalized)]
