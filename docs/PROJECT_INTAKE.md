# Project Intake

## Objectif

Le Project Intake est le point d'entrée d'un **projet complet**. L'utilisateur fournit les consignes, le cahier des charges, les sources et les livrables attendus.

Depuis l'ajout du **Project Orchestrator**, l'intake n'est plus seulement distribué aux agents : il devient l'entrée d'une machine d'états qui transforme le projet en analyse, clarifications, plan, tâches, preuves, revue et paquet final.

Le dépôt source reste la vérité. Le RAG ou une future indexation servent à retrouver du contexte, jamais à remplacer la lecture des fichiers réels.

## Arborescence gérée

Chaque projet est matérialisé sous `<OPENCLAW_LOCAL_ROOT>\projects\<project-id>` :

```text
<project-id>/
├── project.json
├── intake/        # consignes, cahier des charges, grille, sujet
├── sources/       # dépôt ou fichiers de travail de référence
├── context/       # analyse, clarifications, plan et packets de tâches
├── work/          # travail intermédiaire collecté
├── deliverables/  # livrables produits et package final
├── evidence/      # preuves, validations et historique d'exécution
└── diagrams/      # sources et rendus de schémas
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

Le script refuse un identifiant invalide, l'écrasement d'un projet existant, une source inexistante et les collisions de noms.

Les secrets ne doivent jamais être déposés dans `intake/` ni `sources/`.

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

Les transitions sont désormais **exécutables et contrôlées** par le Project Orchestrator. Chaque transition significative exige l'artefact ou la preuve correspondant au gate.

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
- **Architecte solutions** : architecture, ADR, compromis et schémas.
- **Ingénieur DevOps** : CI/CD, IaC, conteneurs et scripts.
- **Ingénieur sécurité** : hardening, secrets, supply chain et risques.
- **Ingénieur release/forges** : Git, PR, releases, packaging et preuves distantes.
- **Rédacteur technique** : documentation et runbooks.
- **Auditeur qualité** : conformité, preuves et contrôle final indépendant.

## Règles de sécurité

- aucun secret dans le dépôt ou les snapshots ;
- filesystem borné au workspace ;
- les rôles de revue ne peuvent pas modifier silencieusement le livrable ;
- les actions destructrices ou de publication restent soumises à validation humaine ;
- le Project Orchestrator n'active jamais le cloud automatiquement ;
- les preuves locales restent hors Git tant qu'elles ne sont pas redacted et explicitement publiées ;
- `COMPLETE` exige toujours une approbation humaine explicite.
