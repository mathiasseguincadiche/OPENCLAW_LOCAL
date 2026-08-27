from __future__ import annotations

import re
import zipfile
from pathlib import Path

_TOKEN_PATTERNS = (
    re.compile(r"sk-or-(?:v1-)?[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"glpat-[A-Za-z0-9_-]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)
_ASSIGNMENT = re.compile(
    r"(?i)\b(password|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*([^\s]+)"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----.*?"
    r"-----END (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
    re.DOTALL,
)


def redact_text(text: str) -> str:
    redacted = text
    for pattern in _TOKEN_PATTERNS:
        redacted = pattern.sub("<REDACTED_TOKEN>", redacted)
    redacted = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=<REDACTED>", redacted)
    redacted = _PRIVATE_KEY.sub("<REDACTED_PRIVATE_KEY>", redacted)
    return redacted


def contains_suspected_secret(text: str) -> bool:
    if any(pattern.search(text) for pattern in _TOKEN_PATTERNS):
        return True
    for match in _ASSIGNMENT.finditer(text):
        if match.group(2) not in {"<REDACTED>", "<REDACTED_TOKEN>", "<REDACTED_PRIVATE_KEY>"}:
            return True
    return _PRIVATE_KEY.search(text) is not None


def sanitize_exception(exc: BaseException) -> str:
    return redact_text(f"{type(exc).__name__}: {exc}")


def build_support_bundle(project: Path, output: Path) -> Path:
    candidates = [project / "project.json", project / "evidence" / "orchestration"]
    entries: list[tuple[str, str]] = []
    for candidate in candidates:
        if candidate.is_file():
            paths = [candidate]
        elif candidate.is_dir():
            paths = list(candidate.rglob("*"))
        else:
            paths = []
        for path in paths:
            if not path.is_file() or path.is_symlink():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            sanitized = redact_text(text)
            if contains_suspected_secret(sanitized):
                raise ValueError(f"secret potentiel après seconde passe: {path.name}")
            entries.append((path.relative_to(project).as_posix(), sanitized))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, text in entries:
            archive.writestr(relative, text)
    return output
