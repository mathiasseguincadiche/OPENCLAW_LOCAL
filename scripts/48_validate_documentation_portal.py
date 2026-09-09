from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

PORTAL = DOCS / "README.md"
READING_PATH = DOCS / "PARCOURS_LECTURE.md"
USER_GUIDE = DOCS / "GUIDE_UTILISATEUR" / "README.md"
ACCESSIBILITY = DOCS / "ACCESSIBILITY.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"

VALIDATOR_COMMAND = "python scripts/48_validate_documentation_portal.py"

REQUIRED_PORTAL_MARKERS = (
    "une seule documentation",
    "un seul parcours",
    "Parcours de lecture unique",
    "COMPRENDRE LE PROJET",
    "INSTALLER ET VÉRIFIER",
    "UTILISER POUR UN VRAI TRAVAIL",
    "COMPRENDRE LE FONCTIONNEMENT INTERNE",
    "COMPRENDRE LES CONTRATS ET LA QUALITÉ",
    "COMPRENDRE LA QUALIFICATION ET LES PREUVES",
    "DIAGNOSTIQUER, MAINTENIR ET FAIRE ÉVOLUER",
)

REQUIRED_READING_PATH_MARKERS = (
    "# Parcours de lecture unique",
    "une seule documentation, un seul parcours",
    "## Étape 1 — Comprendre ce qu'est le projet",
    "## Étape 2 — Installer et vérifier la plateforme",
    "## Étape 3 — Utiliser OPENCLAW_LOCAL pour un vrai travail",
    "## Étape 4 — Comprendre comment le système fonctionne",
    "## Étape 5 — Comprendre les contrats et la qualité",
    "## Étape 6 — Comprendre la qualification et la readiness",
    "## Étape 7 — Diagnostiquer, maintenir et faire évoluer",
    "### Prérequis",
    "### Résultat attendu",
    "### STOP",
    "contrat",
    "état observé",
    "preuve",
    "hypothèse",
)

REQUIRED_GUIDE_MARKERS = (
    "même parcours documentaire",
    "aucune partie n'est réservée",
    "COMPRENDRE L'OBJECTIF",
    "VÉRIFIER LES PRÉREQUIS",
    "RÉSULTAT ATTENDU",
    "STOP + DIAGNOSTIC",
    "Parcours de lecture unique",
)

REQUIRED_ACCESSIBILITY_MARKERS = (
    "un seul parcours partagé",
    "Ces quatre profondeurs ne correspondent pas à quatre publics",
    "une seule documentation pour tous",
    "aucune zone réservée à un niveau de compétence",
    "vraie compréhension du fonctionnement DevOps",
)

FORBIDDEN_SEGMENTATION_MARKERS = (
    "## Choisir par profil",
    "## Choisir son profil",
    "## Parcours A — Débutant",
    "## Parcours B — Opérateur",
    "## Parcours C — Mainteneur",
    "## Parcours D — Expert / auditeur",
    "parcours par profil",
    "Parcours expert",
    "Parcours opérateur",
    "Parcours mainteneur",
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


def _reject_segmentation(label: str, text: str, failures: list[str]) -> None:
    for marker in FORBIDDEN_SEGMENTATION_MARKERS:
        if marker in text:
            failures.append(
                f"{label}: segmentation documentaire par profil interdite: {marker}"
            )


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
            failures.append(f"{path.relative_to(ROOT)}: lien relatif cassé: {target}")


def main() -> int:
    failures: list[str] = []

    portal_text = _read(PORTAL, failures)
    reading_text = _read(READING_PATH, failures)
    guide_text = _read(USER_GUIDE, failures)
    accessibility_text = _read(ACCESSIBILITY, failures)
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
    _require_markers(
        "docs/ACCESSIBILITY.md",
        accessibility_text,
        REQUIRED_ACCESSIBILITY_MARKERS,
        failures,
    )

    for path, text in (
        (PORTAL, portal_text),
        (READING_PATH, reading_text),
        (USER_GUIDE, guide_text),
        (ACCESSIBILITY, accessibility_text),
    ):
        _reject_segmentation(str(path.relative_to(ROOT)), text, failures)
        _validate_relative_links(path, text, failures)

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
    print("- un seul parcours documentaire partagé")
    print("- progression: bases -> usage -> architecture -> contrats -> preuves -> diagnostic")
    print("- aucune zone réservée à un niveau de compétence")
    print("- prérequis, résultats attendus et STOP/GO explicités")
    print("- liens relatifs essentiels vérifiés")
    print("- gate actif en CI et en release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
