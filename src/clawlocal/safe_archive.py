from __future__ import annotations

import hashlib
import mimetypes
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

_MIB = 1024 * 1024
_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _safe_member_path(name: str, *, max_depth: int) -> PurePosixPath:
    if "\x00" in name:
        raise ValueError("archive ZIP: nom de membre contenant NUL")
    normalized = name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if member.is_absolute() or not member.parts or ".." in member.parts:
        raise ValueError(f"archive ZIP: chemin dangereux: {name}")
    parts = [part for part in member.parts if part not in {"", "."}]
    if len(parts) > max_depth:
        raise ValueError(f"archive ZIP: profondeur excessive: {name}")
    for part in parts:
        if ":" in part:
            raise ValueError(f"archive ZIP: composant Windows dangereux: {name}")
        trimmed = part.rstrip(" .")
        if not trimmed or trimmed != part:
            raise ValueError(f"archive ZIP: nom Windows ambigu: {name}")
        stem = trimmed.split(".", 1)[0].casefold()
        if stem in _WINDOWS_RESERVED:
            raise ValueError(f"archive ZIP: nom Windows réservé: {name}")
    return PurePosixPath(*parts)


def _is_link_or_special(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode == 0:
        return False
    file_type = stat.S_IFMT(mode)
    return file_type not in {0, stat.S_IFREG, stat.S_IFDIR}


def _member_kind(path: PurePosixPath) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}:
        return "image"
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return "office"
    if suffix in {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz"}:
        return "nested_archive"
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if mime.startswith("text/") or suffix in {
        ".md", ".rst", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".conf", ".py", ".ps1", ".sh", ".tf", ".tfvars", ".hcl", ".js", ".ts",
        ".tsx", ".jsx", ".java", ".go", ".rs", ".cs", ".sql", ".xml", ".csv", ".tsv",
    }:
        return "text"
    return "binary"


def safe_extract_zip(
    archive_path: Path,
    destination: Path,
    safety: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract one generic ZIP into a derived workspace under strict safety gates.

    Nested archives remain opaque members and are never recursively expanded here.
    Every extracted byte is hash-bound to the corresponding archive member.
    """
    max_archive = int(safety.get("max_archive_bytes_mb", 250)) * _MIB
    max_members = int(safety.get("max_members", 20000))
    max_total = int(safety.get("max_total_uncompressed_mb", 2048)) * _MIB
    max_member = int(safety.get("max_single_member_mb", 256)) * _MIB
    max_ratio = float(safety.get("max_compression_ratio", 200))
    max_depth = int(safety.get("max_depth", 12))
    reject_encrypted = bool(safety.get("reject_encrypted_members", True))

    if archive_path.stat().st_size > max_archive:
        raise ValueError(f"archive ZIP trop volumineuse: {archive_path.name}")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if len(infos) > max_members:
                raise ValueError(f"archive ZIP contient trop de membres: {archive_path.name}")
            for info in infos:
                member = _safe_member_path(info.filename, max_depth=max_depth)
                canonical = member.as_posix().casefold()
                if canonical in seen:
                    raise ValueError(f"archive ZIP: chemin dupliqué/ambigu: {info.filename}")
                seen.add(canonical)
                if reject_encrypted and (info.flag_bits & 0x1):
                    raise ValueError(f"archive ZIP chiffrée non supportée: {archive_path.name}")
                if _is_link_or_special(info):
                    raise ValueError(f"archive ZIP: lien ou fichier spécial refusé: {info.filename}")
                if info.is_dir():
                    (destination / Path(*member.parts)).mkdir(parents=True, exist_ok=True)
                    continue
                total_uncompressed += int(info.file_size)
                if info.file_size > max_member:
                    raise ValueError(f"archive ZIP: membre trop volumineux: {info.filename}")
                if total_uncompressed > max_total:
                    raise ValueError(f"archive ZIP décompressée trop volumineuse: {archive_path.name}")
                if info.file_size:
                    ratio = info.file_size / max(1, info.compress_size)
                    if ratio > max_ratio:
                        raise ValueError(
                            f"archive ZIP: ratio de compression suspect: {info.filename} ({ratio:.1f}x)"
                        )

                target = destination / Path(*member.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                observed = 0
                with archive.open(info, "r") as source, target.open("xb") as sink:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        observed += len(chunk)
                        if observed > max_member or observed > info.file_size:
                            raise ValueError(f"archive ZIP: taille réelle incohérente: {info.filename}")
                        digest.update(chunk)
                        sink.write(chunk)
                if observed != info.file_size:
                    raise ValueError(f"archive ZIP: membre tronqué: {info.filename}")
                mime = mimetypes.guess_type(member.name)[0] or "application/octet-stream"
                kind = _member_kind(member)
                records.append(
                    {
                        "member_path": member.as_posix(),
                        "sha256": digest.hexdigest(),
                        "size": observed,
                        "mime": mime,
                        "kind": kind,
                        "nested_archive": kind == "nested_archive",
                    }
                )
    except Exception:
        import shutil

        shutil.rmtree(destination, ignore_errors=True)
        raise
    return sorted(records, key=lambda item: str(item["member_path"]))
