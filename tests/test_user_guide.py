from pathlib import Path

GUIDE = Path("docs/GUIDE_UTILISATEUR")

REQUIRED_SECTIONS = {
    "00_DEMARRER",
    "01_METHODE_DE_TRAVAIL",
    "02_AGENTS",
    "03_PARCOURS_PRATIQUES",
    "04_WORKFLOW_PROJET",
    "05_GERER_UN_PROJET",
    "06_RECETTES_ET_MODELES",
    "07_DIAGNOSTIC",
    "08_REFERENCE_RAPIDE",
}

REQUIRED_FILES = {
    "README.md",
    "00_DEMARRER/00_LIRE_EN_PREMIER.md",
    "01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md",
    "02_AGENTS/01_CHEF_OPERATIONS.md",
    "02_AGENTS/08_AUDITEUR_QUALITE.md",
    "03_PARCOURS_PRATIQUES/05_MODIFIER_UN_PROJET_EXISTANT.md",
    "03_PARCOURS_PRATIQUES/13_EDITER_UN_FICHIER_OU_UNE_CONFIGURATION.md",
    "03_PARCOURS_PRATIQUES/14_TRAVAILLER_AVEC_DIFFERENTS_LANGAGES.md",
    "04_WORKFLOW_PROJET/00_VUE_ENSEMBLE.md",
    "04_WORKFLOW_PROJET/11_BOUCLES_DE_CORRECTION.md",
    "05_GERER_UN_PROJET/09_CLOTURER_UN_PROJET.md",
    "06_RECETTES_ET_MODELES/01_MODELE_DE_DEMANDE.md",
    "07_DIAGNOSTIC/02_LIRE_LES_LOGS.md",
    "08_REFERENCE_RAPIDE/COMMANDES.md",
    "08_REFERENCE_RAPIDE/CHECKLISTS.md",
}


def test_user_guide_has_the_expected_operational_structure() -> None:
    assert GUIDE.is_dir()
    sections = {path.name for path in GUIDE.iterdir() if path.is_dir()}
    assert REQUIRED_SECTIONS <= sections
    for relative in REQUIRED_FILES:
        path = GUIDE / relative
        assert path.is_file(), relative
        assert path.read_text(encoding="utf-8").strip(), relative


def test_user_guide_exposes_method_agents_workflow_and_diagnostics() -> None:
    index = (GUIDE / "README.md").read_text(encoding="utf-8")
    assert "qu'est-ce que je veux obtenir" in index
    assert "01_METHODE_DE_TRAVAIL" in index
    assert "02_AGENTS" in index
    assert "04_WORKFLOW_PROJET" in index
    assert "07_DIAGNOSTIC" in index

    method = (GUIDE / "01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md").read_text(
        encoding="utf-8"
    ).casefold()
    for concept in ("définir", "préparer", "planifier", "valider", "approuver"):
        assert concept in method

    statuses = (GUIDE / "08_REFERENCE_RAPIDE/STATUTS.md").read_text(
        encoding="utf-8"
    )
    for state in (
        "INTAKE_READY",
        "ANALYZED",
        "PLANNED",
        "IN_PROGRESS",
        "VALIDATING",
        "REVIEW",
        "PACKAGING",
        "COMPLETE",
    ):
        assert state in statuses
