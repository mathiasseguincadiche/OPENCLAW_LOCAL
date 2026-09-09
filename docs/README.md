# Portail documentaire

OPENCLAW_LOCAL utilise **une seule documentation et un seul parcours de lecture**, conçu pour être suivi depuis zéro jusqu'aux contrats, preuves et mécanismes DevOps du projet.

Le point d'entrée recommandé est : **[Parcours de lecture unique](PARCOURS_LECTURE.md)**.

Il n'existe pas de zone réservée à un niveau de compétence. La profondeur augmente progressivement dans le même parcours.

## Ordre recommandé

```text
1. COMPRENDRE LE PROJET
   ↓
2. INSTALLER ET VÉRIFIER
   ↓
3. UTILISER POUR UN VRAI TRAVAIL
   ↓
4. COMPRENDRE LE FONCTIONNEMENT INTERNE
   ↓
5. COMPRENDRE LES CONTRATS ET LA QUALITÉ
   ↓
6. COMPRENDRE LA QUALIFICATION ET LES PREUVES
   ↓
7. DIAGNOSTIQUER, MAINTENIR ET FAIRE ÉVOLUER
```

Commencez par [Parcours de lecture unique](PARCOURS_LECTURE.md) et suivez simplement l'ordre indiqué.

## Mode d'emploi opérationnel

Le [Guide utilisateur](GUIDE_UTILISATEUR/README.md) accompagne ce parcours pour les actions concrètes :

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

Chaque action importante doit indiquer, directement ou via son document associé : **prérequis → action → résultat attendu → validation/preuve → STOP/GO → suite**.

## Références du parcours

| Sujet | Document |
|---|---|
| commencer sans connaissance préalable | [Premiers pas](PREMIERS_PAS_OPENCLAW_LOCAL.md) |
| parcours complet de zéro à la maîtrise du projet | [Parcours de lecture unique](PARCOURS_LECTURE.md) |
| travailler avec la plateforme | [Guide utilisateur](GUIDE_UTILISATEUR/README.md) |
| installation Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| exploitation quotidienne | [Opérations](OPERATIONS.md) |
| architecture | [Architecture](ARCHITECTURE.md) |
| Project Intake | [Project Intake](PROJECT_INTAKE.md) |
| intégrité des entrées | [Intégrité Intake](INTAKE_INTEGRITY.md) |
| machine d'états | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| pédagogie | [Pédagogie](PEDAGOGY.md) |
| accessibilité progressive | [Accessibilité](ACCESSIBILITY.md) |
| publication projet | [Publication projet](PROJECT_PUBLICATION.md) |
| télémétrie | [Télémétrie](TELEMETRY.md) |
| OpenClaw et routage | [Intégration OpenClaw](OPENCLAW_INTEGRATION.md) |
| recherche Web local-first | [Recherche Web Local-First](WEB_LOCAL_FIRST.md) |
| runtimes Vulkan | [Backends locaux](RUNTIME_BACKENDS.md) |
| Intel Arc B580 | [Intel Arc B580](INTEL_ARC_B580.md) |
| modèles locaux | [Modèles locaux](MODELES_LOCAUX.md) |
| routage hybride | [Routage hybride](ROUTAGE_HYBRIDE.md) |
| diagrammes | [Diagrammes](DIAGRAMMES.md) |
| benchmark | [Benchmark](BENCHMARK.md) |
| qualification réelle | [Qualification](QUALIFICATION.md) |
| sécurité | [Sécurité](SECURITY.md) |
| dépannage / rollback | [Troubleshooting](TROUBLESHOOTING.md) |
| gouvernance GitHub | [Gouvernance GitHub](GITHUB_GOVERNANCE.md) |
| décisions structurantes | [ADR](ADR/README.md) |
| état actuel | [État du projet](../STATUS.md) |

## Principe pédagogique

Le projet doit pouvoir être ouvert par quelqu'un qui ne connaît rien au contexte et lui permettre, en suivant simplement l'ordre indiqué, d'arriver progressivement jusqu'à une vraie compréhension DevOps du projet.

Cela implique :

- aucun prérequis critique implicite ;
- jargon défini lorsque nécessaire ;
- aucune simplification fausse ;
- profondeur technique conservée ;
- aucune séparation « débutant » / « expert » ;
- les mêmes documents restent accessibles à tous ;
- le diagnostic et les preuves sont introduits progressivement.

## Contrat de preuve

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**.

La readiness n'est jamais déduite d'une documentation complète ou d'une CI verte seule : elle dépend des preuves requises par la qualification réelle et de l'approbation humaine correspondante.

## Contrat CI documentaire

Le portail est protégé par `scripts/48_validate_documentation_portal.py`.

Le gate vérifie notamment :

- l'existence d'un seul parcours principal ;
- la progression depuis les bases jusqu'aux contrats et preuves ;
- l'absence de segmentation documentaire par niveau de compétence ;
- la présence des prérequis, résultats attendus, critères STOP/GO et suites ;
- les principaux liens relatifs ;
- l'exécution du gate dans CI et Release.
