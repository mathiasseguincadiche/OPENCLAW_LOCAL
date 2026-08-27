# Project Intake

## Objectif

La V0.2 introduit un parcours **projet complet** : l'utilisateur fournit les consignes, le cahier des charges, les sources et les livrables attendus, puis OpenClaw distribue un contexte maîtrisé aux huit agents.

Le dépôt source reste la vérité. Le RAG ou une future indexation servent à retrouver du contexte, jamais à remplacer la lecture des fichiers réels.

## Arborescence gérée

Chaque projet est matérialisé sous `<OPENCLAW_LOCAL_ROOT>\projects\<project-id>` :

```text
<project-id>/
├── project.json
├── intake/        # consignes, cahier des charges, grille, sujet
├── sources/       # dépôt ou fichiers de travail de référence
├── context/       # contexte dérivé et explicitement géré
├── work/          # travail intermédiaire
├── deliverables/  # livrables produits
├── evidence/      # preuves et rapports
└── diagrams/      # sources et rendus de schémas
```

Le contrat est défini par `config/v1/project_policy.yaml`.

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

Le script refuse :

- un identifiant projet invalide ;
- l'écrasement d'un projet existant ;
- une source ou une consigne inexistante ;
- une collision de noms dans les éléments copiés.

Les secrets ne doivent jamais être déposés dans `intake/` ni `sources/`.

## Distribution aux agents

```powershell
python .\scripts\31_sync_project_context.py --project p5-devops --agent all
```

Chaque agent reçoit un snapshot sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\p5-devops
```

Seuls `intake/`, `sources/`, `context/` et `project.json` sont recopiés comme contexte commun. Les répertoires `work/`, `deliverables/`, `evidence/` et `diagrams/` sont recréés pour chaque workspace.

Un marqueur `.openclaw-local-project-snapshot` protège les snapshots. Un répertoire non marqué n'est jamais supprimé ou écrasé par le synchroniseur.

## Cycle de vie

Le contrat prévoit les états :

```text
INTAKE_READY
    ↓
ANALYZED
    ↓
PLANNED
    ↓
IN_PROGRESS
    ↓
REVIEW
    ↓
COMPLETE
```

La V0.2 matérialise l'intake et la distribution de contexte. Les transitions métier ultérieures doivent rester explicites et produire des preuves plutôt que modifier silencieusement `project.json`.

## Répartition des responsabilités

- **Chef des opérations** : cadrage, objectifs, contraintes, planification et orchestration.
- **Expert recherche** : informations externes et fraîcheur des sources.
- **Architecte solutions** : architecture, ADR, compromis et schémas.
- **Ingénieur DevOps** : CI/CD, IaC, conteneurs et scripts.
- **Ingénieur sécurité** : hardening, secrets, supply chain et risques.
- **Ingénieur release/forges** : Git, PR, releases et preuves distantes.
- **Rédacteur technique** : documentation et runbooks.
- **Auditeur qualité** : conformité, preuves et contrôle final indépendant.

## Règles de sécurité

- aucun secret dans le dépôt ou les snapshots ;
- filesystem borné au workspace ;
- les rôles de revue ne peuvent pas modifier silencieusement le livrable ;
- les actions destructrices ou de publication restent soumises à validation humaine ;
- les preuves locales restent hors Git tant qu'elles ne sont pas redacted et explicitement publiées.
