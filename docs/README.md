# Portail documentaire

La documentation est organisée en **trois niveaux** afin de ne pas mélanger découverte, utilisation quotidienne et détails d'implémentation.

## Niveau 1 — Découvrir

Si vous utilisez pour la première fois une IA locale ou OpenClaw :

**[Premiers pas avec OPENCLAW_LOCAL et OpenClaw](PREMIERS_PAS_OPENCLAW_LOCAL.md)**

Ce document explique les concepts de base et permet de faire les premiers contrôles et premiers appels.

## Niveau 2 — Utiliser au quotidien

Pour savoir **comment accomplir un travail de bout en bout**, utilisez :

**[Guide utilisateur opérationnel](GUIDE_UTILISATEUR/README.md)**

C'est le mode d'emploi principal. Il est organisé par besoin :

```text
GUIDE_UTILISATEUR/
├── 00_DEMARRER/              comprendre les repères
├── 01_METHODE_DE_TRAVAIL/    méthode universelle
├── 02_AGENTS/                choisir et utiliser les 8 rôles
├── 03_PARCOURS_PRATIQUES/    « je veux faire… »
├── 04_WORKFLOW_PROJET/       suivre chaque état de l'orchestrateur
├── 05_GERER_UN_PROJET/       créer, reprendre, modifier, clôturer
├── 06_RECETTES_ET_MODELES/   modèles à copier/adopter
├── 07_DIAGNOSTIC/            comprendre STOP/FAIL, logs et reprise
└── 08_REFERENCE_RAPIDE/      commandes, statuts, artefacts, checklists
```

Commencez par **[Méthode générale de travail](GUIDE_UTILISATEUR/01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md)** si vous avez un objectif mais ne savez pas comment organiser le chemin jusqu'au résultat.

## Niveau 3 — Approfondir techniquement

Ces documents sont les références d'architecture, de contrats et d'exploitation détaillée :

| Besoin | Document |
|---|---|
| comprendre la filiation avec `openclaw_openrouter` | [Filiation V7 / Parity Plus](V7_PARITY_PLUS.md) |
| comprendre l'architecture | [Architecture](ARCHITECTURE.md) |
| installer/reproduire le runtime Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| fournir consignes, sources et livrables | [Project Intake](PROJECT_INTAKE.md) |
| vérifier l'intégrité/immutabilité des entrées | [Intégrité Intake](INTAKE_INTEGRITY.md) |
| comprendre la machine d'états projet | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| comprendre la pédagogie | [Pédagogie](PEDAGOGY.md) |
| lire la documentation à plusieurs profondeurs | [Accessibilité](ACCESSIBILITY.md) |
| publier un projet GitHub/GitLab avec gates | [Publication projet](PROJECT_PUBLICATION.md) |
| mesurer les agents/backends en usage réel | [Télémétrie](TELEMETRY.md) |
| comprendre la flotte OpenClaw et le routage | [Intégration OpenClaw](OPENCLAW_INTEGRATION.md) |
| utiliser Internet en local-first | [Recherche Web Local-First](WEB_LOCAL_FIRST.md) |
| comprendre Ollama/Vulkan et llama.cpp | [Backends locaux](RUNTIME_BACKENDS.md) |
| comprendre/qualifier les modèles | [Modèles locaux](MODELES_LOCAUX.md) |
| comprendre l'escalade | [Routage hybride](ROUTAGE_HYBRIDE.md) |
| contrôler les dépenses cloud | [FinOps](FINOPS.md) |
| produire des schémas techniques | [Diagrammes](DIAGRAMMES.md) |
| mesurer machine et modèles | [Benchmark](BENCHMARK.md) |
| exécuter la qualification réelle | [Qualification](QUALIFICATION.md) |
| exploiter au quotidien | [Opérations](OPERATIONS.md) |
| comprendre les frontières de sécurité | [Sécurité](SECURITY.md) |
| dépanner, sauvegarder, restaurer, rollback | [Troubleshooting](TROUBLESHOOTING.md) |
| gouvernance, protection de `main`, releases | [Gouvernance GitHub](GITHUB_GOVERNANCE.md) |
| décisions structurantes | [ADR](ADR/README.md) |

## Parcours recommandé pour un travail complexe

```text
DÉFINIR le résultat
→ PRÉPARER les entrées
→ CHOISIR agent direct ou projet
→ ANALYZER
→ CLARIFIER si nécessaire
→ PLANIFIER + ASSIGNER
→ EXÉCUTER
→ SUIVRE le status et les preuves
→ VALIDER
→ CORRIGER les tâches affectées
→ REVIEW indépendante
→ PACKAGE
→ APPROBATION humaine
→ PUBLICATION éventuelle dans son workflow dédié
```

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**. Les résultats matériels et E2E réels restent des preuves locales tant qu'ils n'ont pas été redacted et explicitement publiés.