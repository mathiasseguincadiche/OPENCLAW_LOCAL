# Project Intake

## Objectif

Le Project Intake est le point d'entrée d'un **projet complet**. L'utilisateur fournit les consignes, le cahier des charges, les sources et les livrables attendus.

Depuis l'ajout du **Project Orchestrator**, l'intake devient l'entrée d'une machine d'états qui transforme le projet en analyse, clarifications, plan, tâches, preuves, revue et paquet final.

Le dépôt source reste la vérité. Le RAG ou une future indexation servent à retrouver du contexte, jamais à remplacer la lecture des fichiers réels.

Les documents reçus sont considérés comme **données non fiables** : une instruction présente dans un PDF, README ou YAML ne peut jamais remplacer les contrats OpenClaw, les politiques d'outils ou les gates humains.

## Chaîne d'ingestion

```text
INPUT
  ↓
validation des chemins
  ↓
refus des symlinks dans l'intake
  ↓
scan de secrets avant copie
  ↓
archive canonique hors projet
  ↓
SHA-256 + MIME + inventaire symlink
  ↓
manifest + INGESTION_REPORT
  ↓
copie projet gérée
  ↓
lecture seule / ACL Windows
  ↓
INTAKE_READY
```

Le contrat détaillé est `config/v1/intake_policy.yaml`.

## Archive canonique

Une copie indépendante est conservée sous :

```text
<OPENCLAW_LOCAL_ROOT>\state\intake\<project-id>\<timestamp>\
```

Cette archive est distincte du snapshot projet. Elle permet de comparer ce qui a été reçu avec ce qui a été analysé, même si le projet évolue ensuite.

## Arborescence gérée

Chaque projet est matérialisé sous `<OPENCLAW_LOCAL_ROOT>\projects\<project-id>` :

```text
<project-id>/
├── project.json
├── intake/        # copie gérée et immuable des consignes
├── sources/       # dépôt ou fichiers de travail de référence
├── context/       # analyse, plans, apprentissage, publication, packets
├── work/          # travail intermédiaire collecté
├── deliverables/  # livrables produits et package final
├── evidence/      # ingestion, validations, télémétrie et historique
└── diagrams/      # sources et rendus de schémas
```

Les preuves d'ingestion sont placées dans :

```text
evidence/intake/
├── manifest.json
├── checksums.sha256
├── mime-types.tsv
├── symlinks.txt
└── INGESTION_REPORT.md
```

Le contrat du conteneur projet est `config/v1/project_policy.yaml`.
La machine d'états est définie par `config/v1/orchestration_policy.yaml`.

## Création

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --intake 'C:\Projets\P5\cahier-des-charges.md' `
  --source 'C:\Projets\P5\repository' `
  --deliverable README `
  --deliverable runbook
```

Le script refuse notamment :

- un identifiant invalide ;
- l'écrasement d'un projet existant ;
- une source inexistante ;
- les collisions de noms ;
- un symlink racine dans l'intake ;
- un symlink imbriqué dans l'intake ;
- un fichier manifestement secret (`.env`, clé privée, token connu, etc.) ;
- une affectation ressemblant fortement à un secret dans les fichiers texte inspectés.

Les `sources/` sont copiées sans déréférencer les symlinks existants du dépôt source ; l'Intake, lui, n'accepte aucun symlink.

## Immutabilité

Sous Windows, `icacls.exe` retire l'écriture à l'utilisateur courant sur l'Intake et l'archive canonique tout en conservant la lecture/exécution (`RX`). Sous POSIX, les fichiers sont rendus read-only.

L'objectif n'est pas de rendre les fichiers magiquement inviolables face à un administrateur, mais de créer une **frontière d'intégrité explicite** dans le parcours nominal.

Voir [Intégrité Intake](INTAKE_INTEGRITY.md).

## Artefacts pédagogiques et de publication initialisés

La création du projet initialise également :

```text
context/learning/
├── SKILLS_MATRIX.csv
├── LEARNING_JOURNAL.md
├── TEACH_BACK.md
├── RETENTION_PLAN.yaml
└── learning_profile.json

context/documentation_profile.json
context/publication/publication.json
```

Ainsi, compréhension, documentation et publication font partie du projet dès le départ sans modifier les consignes originales.

## Distribution aux agents

Snapshot de production :

```powershell
python .\scripts\31_sync_project_context.py `
  --project p5-devops `
  --agent all
```

Snapshot de revue, incluant les sorties centrales :

```powershell
python .\scripts\31_sync_project_context.py `
  --project p5-devops `
  --agent auditeur-qualite `
  --include-outputs
```

Chaque agent reçoit son snapshot sous `<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\p5-devops`.

Un marqueur `.openclaw-local-project-snapshot` protège les snapshots. Un répertoire non marqué n'est jamais supprimé ou écrasé par le synchroniseur.

## Cycle de vie

```text
INTAKE_READY
    ↓
ANALYZED
    ↓
CLARIFICATION_REQUIRED si nécessaire
    ↓
PLANNED
    ↓
ASSIGNED
    ↓
IN_PROGRESS
    ↓
VALIDATING
    ↓
REVIEW
    ↓
PACKAGING
    ↓
COMPLETE
```

Les transitions sont **exécutables et contrôlées** par le Project Orchestrator. Chaque transition significative exige l'artefact ou la preuve correspondant au gate.

Voir [Project Orchestrator](PROJECT_ORCHESTRATOR.md).

## Démarrer l'orchestration

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action status

python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action run `
  --execute
```

Une information manquante ou une consigne contradictoire doit provoquer un arrêt `CLARIFICATION_REQUIRED`, pas une invention.

## Répartition des responsabilités

- **Chef des opérations** : compréhension, cadrage, planification, assignation et orchestration.
- **Expert recherche** : informations externes et fraîcheur des sources.
- **Architecte solutions** : architecture, ADR, compromis et schémas via writer borné.
- **Ingénieur DevOps** : CI/CD, IaC, conteneurs et scripts.
- **Ingénieur sécurité** : hardening, secrets, supply chain et risques, sans modification directe des sources.
- **Ingénieur release/forges** : Git, PR, releases, packaging et preuves distantes.
- **Rédacteur technique** : documentation progressive et runbooks.
- **Auditeur qualité** : conformité, preuves et contrôle final indépendant.

## Règles de sécurité

- aucun secret dans le dépôt ou les snapshots ;
- filesystem borné au workspace ;
- les rôles de revue ne peuvent pas modifier silencieusement le livrable ;
- les actions destructrices ou de publication restent soumises à validation humaine ;
- le Project Orchestrator n'active jamais le cloud automatiquement ;
- les preuves locales restent hors Git tant qu'elles ne sont pas redacted et explicitement publiées ;
- `COMPLETE` exige toujours une approbation humaine explicite.
