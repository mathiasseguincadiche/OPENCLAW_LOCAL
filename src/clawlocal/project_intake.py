from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from clawlocal.project_contracts import build_project_manifest
from clawlocal.project_governance import initialize_governance
from clawlocal.project_integrity import snapshot_integrity
from clawlocal.project_learning import initialize_learning
from clawlocal.project_publication import initialize_publication

PROJECT_DIRS = (
    "intake",
    "sources",
    "context",
    "work",
    "deliverables",
    "evidence",
    "diagrams",
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
_SECRET_PATTERNS = (
    re.compile(r"sk-or-(?:v1-)?[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"glpat-[A-Za-z0-9_-]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:password|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*\S+"
    ),
)
_BLOCKED_SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
}
_BLOCKED_SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks"}


def validate_project_id(project_id: str) -> str:
    value = project_id.strip().lower()
    if not _SLUG_RE.fullmatch(value):
        raise ValueError(
            "project_id invalide: utiliser 3-64 caractères [a-z0-9-], "
            "sans tiret en début/fin"
        )
    return value


def _safe_destination(root: Path, project_id: str) -> Path:
    projects_root = (root / "projects").resolve()
    destination = (projects_root / project_id).resolve()
    if destination.parent != projects_root:
        raise ValueError("destination projet hors racine autorisée")
    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(item: Path) -> Iterable[Path]:
    if item.is_file() and not item.is_symlink():
        yield item
        return
    if item.is_dir():
        yield from (
            path
            for path in item.rglob("*")
            if path.is_file() and not path.is_symlink()
        )


def _iter_symlinks(item: Path) -> Iterable[Path]:
    if item.is_symlink():
        yield item
        return
    if item.is_dir():
        yield from (path for path in item.rglob("*") if path.is_symlink())


def _assert_no_symlinks(item: Path) -> None:
    links = list(_iter_symlinks(item))
    if links:
        names = ", ".join(str(path) for path in links[:5])
        raise ValueError(f"lien symbolique interdit dans l'intake: {names}")


def _looks_text(path: Path) -> bool:
    try:
        return b"\x00" not in path.read_bytes()[:4096]
    except OSError:
        return False


def _assert_no_obvious_secret(item: Path, *, label: str) -> None:
    for path in _iter_files(item):
        if (
            path.name.casefold() in _BLOCKED_SECRET_NAMES
            or path.suffix.casefold() in _BLOCKED_SECRET_SUFFIXES
        ):
            raise ValueError(f"secret potentiel interdit dans {label}: {path.name}")
        if not _looks_text(path):
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if any(pattern.search(line) for pattern in _SECRET_PATTERNS):
                        raise ValueError(
                            f"secret potentiel interdit dans {label}: {path.name}"
                        )
        except OSError:
            continue


def _validated_source(item: Path, *, intake: bool) -> Path:
    raw = item.expanduser()
    if raw.is_symlink():
        raise ValueError(f"source racine symbolique interdite: {item}")
    source = raw.resolve(strict=True)
    if intake:
        _assert_no_symlinks(source)
        _assert_no_obvious_secret(source, label="l'intake")
    else:
        _assert_no_obvious_secret(source, label="les sources")
    return source


def _copy_one(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    elif source.is_file():
        shutil.copy2(source, destination)
    else:
        raise ValueError(f"source non supportée: {source}")


def _copy_sources(items: Iterable[Path], destination: Path) -> list[str]:
    copied: list[str] = []
    for item in items:
        source = _validated_source(item, intake=False)
        _copy_one(source, destination / source.name)
        copied.append(source.name)
    return copied


def _inventory(root: Path) -> tuple[list[str], list[str], list[str]]:
    checksums: list[str] = []
    mime_types: list[str] = []
    symlinks: list[str] = []
    if not root.exists():
        return checksums, mime_types, symlinks
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            symlinks.append(f"{relative} -> {os.readlink(path)}")
            continue
        if not path.is_file():
            continue
        checksums.append(f"{_sha256(path)}  {relative}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        mime_types.append(f"{mime}\t{relative}")
    return checksums, mime_types, symlinks


def _write_inventory(
    root: Path,
    *,
    project_id: str,
    source_kind: str,
    canonical_archive: str | None,
    checksums: list[str],
    mime_types: list[str],
    symlinks: list[str],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "checksums.sha256").write_text(
        "\n".join(checksums) + ("\n" if checksums else ""), encoding="utf-8"
    )
    (root / "mime-types.tsv").write_text(
        "\n".join(mime_types) + ("\n" if mime_types else ""), encoding="utf-8"
    )
    (root / "symlinks.txt").write_text(
        "\n".join(symlinks) + ("\n" if symlinks else ""), encoding="utf-8"
    )
    aggregate = hashlib.sha256("\n".join(checksums).encode()).hexdigest()
    manifest = {
        "schema_version": "1.1.0",
        "project_id": project_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_kind": source_kind,
        "canonical_archive": canonical_archive,
        "file_count": len(checksums),
        "symlink_count": len(symlinks),
        "sha256_required": True,
        "aggregate_sha256": aggregate,
        "secret_scan_passed": True,
        "documents_are_untrusted_data": source_kind == "intake",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "INGESTION_REPORT.md").write_text(
        f"# Rapport {source_kind}\n\n"
        f"- Projet : `{project_id}`\n"
        f"- Fichiers : **{len(checksums)}**\n"
        f"- Liens symboliques : **{len(symlinks)}**\n"
        "- Secrets potentiels : **0** (sinon la création aurait été refusée)\n"
        "- Intégrité : **SHA-256 + digest agrégé enregistrés**\n"
        "- MIME : **inventaire enregistré**\n",
        encoding="utf-8",
    )


def _set_posix_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            continue
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def _set_windows_read_only(root: Path) -> None:
    identity_result = subprocess.run(
        ["whoami.exe"], capture_output=True, text=True, check=False
    )
    identity = identity_result.stdout.strip()
    if identity_result.returncode != 0 or not identity:
        raise RuntimeError("impossible de déterminer l'identité Windows pour l'ACL intake")
    result = subprocess.run(
        [
            "icacls.exe",
            str(root),
            "/inheritancelevel:r",
            "/grant:r",
            f"{identity}:(OI)(CI)RX",
            "*S-1-5-18:(OI)(CI)F",
            "/T",
            "/Q",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"protection ACL intake impossible: {detail}")


def _set_read_only(root: Path) -> None:
    if os.name == "nt":
        _set_windows_read_only(root)
    else:
        _set_posix_read_only(root)


def _restore_posix_writable(root: Path) -> None:
    if not root.exists():
        return
    root.chmod(0o755)
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            path.chmod(0o644)
        elif path.is_dir():
            path.chmod(0o755)


def _restore_windows_writable(root: Path) -> None:
    if not root.exists():
        return
    identity_result = subprocess.run(
        ["whoami.exe"], capture_output=True, text=True, check=False
    )
    identity = identity_result.stdout.strip()
    if identity_result.returncode != 0 or not identity:
        return
    subprocess.run(
        [
            "icacls.exe",
            str(root),
            "/inheritancelevel:e",
            "/grant:r",
            f"{identity}:(OI)(CI)F",
            "/T",
            "/Q",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _restore_writable(root: Path) -> None:
    if os.name == "nt":
        _restore_windows_writable(root)
    else:
        _restore_posix_writable(root)


def _archive_intake(
    platform_root: Path,
    project_id: str,
    items: Iterable[Path],
) -> tuple[Path, list[str]]:
    sources = [_validated_source(item, intake=True) for item in items]
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    archive = platform_root / "state" / "intake" / project_id / stamp
    original = archive / "original"
    original.mkdir(parents=True, exist_ok=False)
    copied: list[str] = []
    for source in sources:
        _copy_one(source, original / source.name)
        copied.append(source.name)
    checksums, mime_types, symlinks = _inventory(original)
    if symlinks:
        raise ValueError("intake canonique contient un lien symbolique inattendu")
    _write_inventory(
        archive,
        project_id=project_id,
        source_kind="intake",
        canonical_archive=str(archive),
        checksums=checksums,
        mime_types=mime_types,
        symlinks=symlinks,
    )
    return archive, copied


def create_project(
    platform_root: Path,
    project_id: str,
    title: str,
    *,
    intake_items: Iterable[Path] = (),
    source_items: Iterable[Path] = (),
    expected_deliverables: Iterable[str] = (),
    owner: str = "dirigeant-operateur",
    classification: str = "internal",
    criticality: str = "standard",
) -> Path:
    normalized_id = validate_project_id(project_id)
    destination = _safe_destination(platform_root, normalized_id)
    if destination.exists():
        raise FileExistsError(destination)

    intake_list = list(intake_items)
    source_list = list(source_items)
    archive, copied_intake = _archive_intake(platform_root, normalized_id, intake_list)

    try:
        for name in PROJECT_DIRS:
            (destination / name).mkdir(
                parents=True,
                exist_ok=False if name == PROJECT_DIRS[0] else True,
            )
        archived_original = archive / "original"
        for name in copied_intake:
            _copy_one(archived_original / name, destination / "intake" / name)
        copied_sources = _copy_sources(source_list, destination / "sources")
        deliverables = [value.strip() for value in expected_deliverables if value.strip()]

        checksums, mime_types, symlinks = _inventory(destination / "intake")
        _write_inventory(
            destination / "evidence" / "intake",
            project_id=normalized_id,
            source_kind="intake",
            canonical_archive=str(archive),
            checksums=checksums,
            mime_types=mime_types,
            symlinks=symlinks,
        )
        source_checksums, source_mime, source_symlinks = _inventory(destination / "sources")
        _write_inventory(
            destination / "evidence" / "sources",
            project_id=normalized_id,
            source_kind="sources",
            canonical_archive=None,
            checksums=source_checksums,
            mime_types=source_mime,
            symlinks=source_symlinks,
        )

        created_at = datetime.now(UTC).isoformat()
        manifest = build_project_manifest(
            project_id=normalized_id,
            title=title.strip() or normalized_id,
            created_at=created_at,
            expected_deliverables=deliverables,
            source_items=copied_sources,
            intake_items=copied_intake,
            intake_archive=str(archive),
            owner=owner,
            classification=classification,
            criticality=criticality,
        )
        (destination / "project.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        initialize_learning(destination)
        initialize_publication(destination)
        initialize_governance(destination)
        _set_read_only(destination / "intake")
        _set_read_only(archive)
        snapshot_integrity(
            destination,
            "INTAKE_READY",
            roots=["project.json", "intake", "sources", "context"],
        )
        return destination
    except Exception:
        _restore_writable(destination / "intake")
        _restore_writable(archive)
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        if archive.exists():
            shutil.rmtree(archive, ignore_errors=True)
        raise
