from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

PORTAL = DOCS / "README.md"
READING_PATH = DOCS / "PARCOURS_LECTURE.md"
USER_GUIDE = DOCS / "GUIDE_UTILISATEUR" / "README.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"

VALIDATOR_COMMAND = "python scripts/48_validate_documentation_portal.py"

REQUIRED_PORTAL_MARKERS = (
    "Débutant",
    "Opérateur",
    "Mainteneur",
    "Expert / auditeur",
    "PARCOURS_LECTURE.md",
    "Découvrir",
    "Utiliser au quotidien",
    "Approfondir techniquement",
)

REQUIRED_READING_PATH_MARKERS = (
    "## Parcours A — Débutant",
    "## Parcours B — Opérateur",
    "## Parcours C — Mainteneur",
    "## Parcours D — Expert / auditeur",
    "### Prérequis",
    "### Résultat attendu",
    "### Critère STOP",
    "### À lire ensuite",
    "découverte / exploitation / maintenance / audit",
    "contrat",
    "état observé",
    "preuve",
    "hypothèse",
)

REQUIRED_GUIDE_MARKERS = (
    "Choisir son chemin",
    "Débutant",
    "Opérateur",
    "Mainteneur",
    "Expert / auditeur",
    "Résultat attendu",
    "Critère STOP",
    "À lire ensuite",
)

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _read(path: Path, failures: list[str]) -> str:
    if not path.is_file():
        failures.append(f"fichier requis absent: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def _require_markers(
    label: str,
    text: str,
    markers: tuple[str, ...],
    failures: list[str],
) -> None:
    for marker in markers:
        if marker not in text:
            failures.append(f"{label}: marqueur requis absent: {marker}")


def _validate_relative_links(path: Path, text: str, failures: list[str]) -> None:
    for target in LINK_RE.findall(text):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        resolved = (path.parent / clean).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            failures.append(
                f"{path.relative_to(ROOT)}: lien sortant du dépôt interdit: {target}"
            )
            continue
        if not resolved.exists():
            failures.append(
                f"{path.relative_to(ROOT)}: lien relatif cassé: {target}"
            )


def main() -> int:
    failures: list[str] = []

    portal_text = _read(PORTAL, failures)
    reading_text = _read(READING_PATH, failures)
    guide_text = _read(USER_GUIDE, failures)
    ci_text = _read(CI, failures)
    release_text = _read(RELEASE, failures)

    _require_markers("docs/README.md", portal_text, REQUIRED_PORTAL_MARKERS, failures)
    _require_markers(
        "docs/PARCOURS_LECTURE.md",
        reading_text,
        REQUIRED_READING_PATH_MARKERS,
        failures,
    )
    _require_markers(
        "docs/GUIDE_UTILISATEUR/README.md",
        guide_text,
        REQUIRED_GUIDE_MARKERS,
        failures,
    )

    _validate_relative_links(PORTAL, portal_text, failures)
    _validate_relative_links(READING_PATH, reading_text, failures)
    _validate_relative_links(USER_GUIDE, guide_text, failures)

    if VALIDATOR_COMMAND not in ci_text:
        failures.append("CI: gate portail documentaire absent")
    if VALIDATOR_COMMAND not in release_text:
        failures.append("Release: gate portail documentaire absent")

    if failures:
        print("Documentation Portal Gate: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Documentation Portal Gate: CONFORME")
    print("- 4 profils: débutant, opérateur, mainteneur, expert/auditeur")
    print("- parcours: prérequis -> action -> résultat -> STOP/GO -> suite")
    print("- liens relatifs essentiels du portail vérifiés")
    print("- gate actif en CI et en release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
