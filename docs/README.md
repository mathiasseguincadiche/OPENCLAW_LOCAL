# Portail documentaire

La documentation est organisée pour que **chaque profil sache immédiatement où commencer, quoi vérifier et où aller ensuite**.

Le point d'entrée recommandé est : **[Parcours de lecture](PARCOURS_LECTURE.md)**.

## Choisir par profil

| Profil | Besoin principal | Point d'entrée |
|---|---|---|
| **Débutant** | comprendre OPENCLAW_LOCAL et ses repères sans connaissances implicites | [Premiers pas](PREMIERS_PAS_OPENCLAW_LOCAL.md), puis [Parcours de lecture](PARCOURS_LECTURE.md#parcours-a--débutant) |
| **Opérateur** | installer, vérifier, exploiter, diagnostiquer et reprendre | [Opérations](OPERATIONS.md), puis [Parcours opérateur](PARCOURS_LECTURE.md#parcours-b--opérateur) |
| **Mainteneur** | modifier le dépôt sans casser les contrats | [Architecture](ARCHITECTURE.md), [Sécurité](SECURITY.md), puis [Parcours mainteneur](PARCOURS_LECTURE.md#parcours-c--mainteneur) |
| **Expert / auditeur** | retrouver contrats, preuves, qualification et readiness | [Parcours expert](PARCOURS_LECTURE.md#parcours-d--expert--auditeur), [Qualification](QUALIFICATION.md), [État du projet](../STATUS.md) |

Chaque parcours explicite : **prérequis → action/lecture → résultat attendu → validation/preuve → STOP/GO → à lire ensuite**.

## Niveau 1 — Découvrir

Si vous utilisez pour la première fois une IA locale ou OpenClaw :

1. **[Premiers pas avec OPENCLAW_LOCAL et OpenClaw](PREMIERS_PAS_OPENCLAW_LOCAL.md)** ;
2. **[Parcours de lecture](PARCOURS_LECTURE.md)** ;
3. **[Guide utilisateur opérationnel](GUIDE_UTILISATEUR/README.md)** lorsque vous avez un objectif concret.

Objectif de sortie : savoir ce que fait la plateforme, où se trouvent les commandes, comment distinguer agent direct et projet orchestré, et où aller en cas d'échec.

## Niveau 2 — Utiliser au quotidien

Pour savoir **comment accomplir un travail de bout en bout**, utilisez :

**[Guide utilisateur opérationnel](GUIDE_UTILISATEUR/README.md)**

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

**Critère STOP opérateur :** ne poursuivez pas une étape critique si une commande retourne `FAIL`, `NON CONFORME`, si une preuve attendue manque ou si le résultat observé diffère du résultat attendu. Passez au diagnostic avant de continuer.

## Niveau 3 — Approfondir techniquement

Ces documents sont les références d'architecture, de contrats, d'exploitation et de preuves :

| Besoin | Document |
|---|---|
| filiation avec `openclaw_openrouter` | [Filiation V7 / Parity Plus](V7_PARITY_PLUS.md) |
| architecture et invariants | [Architecture](ARCHITECTURE.md) |
| installer/reproduire le runtime Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| fournir consignes, sources et livrables | [Project Intake](PROJECT_INTAKE.md) |
| vérifier l'intégrité/immutabilité des entrées | [Intégrité Intake](INTAKE_INTEGRITY.md) |
| comprendre la machine d'états projet | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| comprendre la pédagogie | [Pédagogie](PEDAGOGY.md) |
| lire à plusieurs profondeurs | [Accessibilité](ACCESSIBILITY.md) |
| publier un projet GitHub/GitLab avec gates | [Publication projet](PROJECT_PUBLICATION.md) |
| mesurer les agents/backends en usage réel | [Télémétrie](TELEMETRY.md) |
| comprendre la flotte OpenClaw et le routage | [Intégration OpenClaw](OPENCLAW_INTEGRATION.md) |
| utiliser Internet en local-first | [Recherche Web Local-First](WEB_LOCAL_FIRST.md) |
| comprendre Ollama/Vulkan et llama.cpp/Vulkan | [Backends locaux](RUNTIME_BACKENDS.md) |
| exploiter et vérifier l'Intel Arc B580 via Vulkan | [Intel Arc B580](INTEL_ARC_B580.md) |
| comprendre/qualifier les modèles | [Modèles locaux](MODELES_LOCAUX.md) |
| comprendre le routage local multi-backends | [Routage hybride](ROUTAGE_HYBRIDE.md) |
| contrôler les dépenses cloud historiques/compatibilité | [FinOps](FINOPS.md) |
| produire des schémas techniques | [Diagrammes](DIAGRAMMES.md) |
| mesurer machine et modèles | [Benchmark](BENCHMARK.md) |
| exécuter la qualification réelle | [Qualification](QUALIFICATION.md) |
| exploiter au quotidien | [Opérations](OPERATIONS.md) |
| comprendre les frontières de sécurité | [Sécurité](SECURITY.md) |
| dépanner, sauvegarder, restaurer, rollback | [Troubleshooting](TROUBLESHOOTING.md) |
| gouvernance, protection de `main`, releases | [Gouvernance GitHub](GITHUB_GOVERNANCE.md) |
| décisions structurantes | [ADR](ADR/README.md) |

## Lecture rapide par intention

```text
Je découvre        → PREMiERS_PAS → PARCOURS_LECTURE → GUIDE_UTILISATEUR
J'exploite         → OPERATIONS → GUIDE_UTILISATEUR → TROUBLESHOOTING si STOP
Je maintiens       → ARCHITECTURE → SECURITY → contrats/configs → CI → ADR
J'audite           → PARCOURS_LECTURE → QUALIFICATION → STATUS → release_readiness
```

## Parcours recommandé pour un travail complexe

```text
DÉFINIR le résultat
→ PRÉPARER les entrées
→ CHOISIR agent direct ou projet
→ ANALYSER
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

## Contrat de preuve

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**. Les résultats matériels et E2E réels restent des preuves locales tant qu'ils n'ont pas été redacted et explicitement publiés.

La readiness n'est jamais déduite d'une documentation complète ou d'une CI verte seule : elle dépend des preuves requises par la qualification et de l'approbation humaine correspondante.

## Contrat CI documentaire

Le portail et ses parcours sont protégés par `scripts/48_validate_documentation_portal.py`. Le gate vérifie notamment :

- les quatre profils **Débutant / Opérateur / Mainteneur / Expert / auditeur** ;
- les prérequis, résultats attendus, critères STOP et suites ;
- les principaux liens relatifs du portail ;
- l'exécution du gate dans CI et Release.

Ainsi, une future modification de documentation ne peut pas supprimer silencieusement le parcours de lecture attendu.
