# Project Orchestrator

## Objectif

Le **Project Orchestrator** transforme un Project Intake encore flou en parcours de travail contrôlé.

Le système ne considère pas qu'un projet est "terminé" parce qu'un modèle a produit une réponse. Il impose des états, des artefacts, des preuves, des revues indépendantes et une validation humaine finale.

```text
INTAKE_READY
    ↓
ANALYZE PROJECT
    ↓
ANALYZED
    ↓
CLARIFY si nécessaire
    ↓
PLANNED
    ↓
ASSIGN TASKS
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

Le contrat est `config/v1/orchestration_policy.yaml`.

## Pourquoi cette couche existe

Un utilisateur peut fournir :

- un sujet ;
- plusieurs PDF de consignes ;
- un cahier des charges ;
- une grille d'évaluation ;
- un starter-kit ou un dépôt Git ;
- des livrables attendus ;
- des documents contradictoires ou incomplets.

Le rôle de l'orchestrateur est de convertir cet ensemble en :

1. compréhension structurée ;
2. ambiguïtés explicites ;
3. questions à faire trancher par l'humain lorsque nécessaire ;
4. plan de travail ;
5. tâches attribuées aux rôles OpenClaw ;
6. exécution locale ;
7. preuves ;
8. validation ;
9. revue indépendante ;
10. paquet final traçable.

## Principe fail-closed

L'orchestrateur refuse d'avancer lorsqu'un gate n'est pas satisfait.

Exemples :

- pas de `project_analysis.json` → impossible de passer à `ANALYZED` ;
- clarification bloquante ouverte → impossible de passer à `PLANNED` ;
- tâche en échec → impossible de passer à `VALIDATING` ;
- validation `FAIL` → réouverture de tâches puis retour à `IN_PROGRESS` ;
- review `FAIL` → réouverture de tâches puis retour à `IN_PROGRESS` ;
- limite de tentatives atteinte → arrêt et intervention humaine ;
- pas de livrables → packaging refusé ;
- pas d'approbation humaine → `COMPLETE` refusé.

Le cloud n'est jamais activé automatiquement par le Project Orchestrator. Une escalade éventuelle reste soumise au routeur, à la politique d'escalade et au budget FinOps existants.

## Artefacts canoniques

```text
context/
├── project_analysis.json
├── clarifications.json
├── project_plan.json
├── task_assignments.json
└── tasks/
    └── <task-id>.json

evidence/
├── orchestration/
├── task_results.json
├── remediation_history.json
├── validation_report.json
├── review_report.json
└── final_report.json

deliverables/
├── tasks/
├── package_manifest.json
└── <project-id>.zip
```

Les changements d'état restent aussi inscrits dans `project.json` sous `orchestration.history`.

## Phase ANALYZE

Le Chef des opérations lit :

- `project.json` ;
- `intake/` ;
- `sources/`.

Il doit retourner une analyse structurée avec :

```json
{
  "summary": "...",
  "objectives": [],
  "constraints": [],
  "deliverables": [],
  "ambiguities": [],
  "missing_information": [],
  "risks": [],
  "decisions_required": []
}
```

L'orchestrateur écrit `context/project_analysis.json`.

Les ambiguïtés, informations manquantes et décisions nécessaires deviennent des entrées de `context/clarifications.json`.

## Phase CLARIFY

Une ambiguïté bloquante n'est jamais résolue arbitrairement par le système.

Exemple :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action resolve `
  --clarification-id clarification-001 `
  --answer 'Utiliser l option Docker locale.'
```

Lorsque toutes les clarifications bloquantes sont résolues, le projet revient à `ANALYZED` et peut être planifié.

## Phase PLAN

Le Chef des opérations produit un plan structuré.

Chaque tâche contient au minimum :

- `id` ;
- `title` ;
- `role` ;
- `objective` ;
- `depends_on` ;
- `expected_outputs` ;
- `acceptance_criteria` ;
- `needs_web` ;
- `security_sensitive`.

L'orchestrateur contrôle :

- l'existence du rôle ;
- l'unicité des IDs ;
- l'existence des dépendances ;
- l'absence de cycle de dépendances.

## Phase ASSIGN

L'assignation est déterministe.

Chaque tâche du plan devient un packet :

```text
context/tasks/<task-id>.json
```

Le packet indique également les racines de sortie autorisées :

```text
work/<task-id>
deliverables/<task-id>
evidence/<task-id>
diagrams/<task-id>
```

Le contexte est ensuite synchronisé vers les huit workspaces.

## Phase EXECUTE

Les tâches sont exécutées séquentiellement par défaut.

Cette décision est volontaire pour la workstation locale :

- évite de charger plusieurs gros modèles simultanément ;
- limite la contention VRAM/RAM ;
- facilite la traçabilité ;
- respecte les dépendances du plan.

Le nombre maximal de tentatives est défini par contrat.

Une tâche peut utiliser les outils autorisés à son rôle. Une tâche `needs_web=true` confiée à l'Expert recherche reste sur le parcours Web local-first.

Les sorties de chaque tâche sont collectées de façon namespacée :

```text
deliverables/tasks/<task-id>/<agent-id>/run-001/
```

Un nouvel essai produit `run-002`, etc., sans écraser la preuve précédente.

## Phase VALIDATE

Lorsque toutes les tâches sont `PASS`, le projet passe à `VALIDATING`.

L'Auditeur qualité reçoit un snapshot incluant :

- consignes originales ;
- sources ;
- contexte ;
- travail collecté ;
- livrables ;
- preuves ;
- diagrammes.

Il ne corrige pas silencieusement le travail. Il produit un verdict `PASS` ou `FAIL` et des findings. Lors d'un `FAIL`, il est invité à fournir `retry_task_ids[]` avec les tâches qui doivent être reprises.

L'orchestrateur applique alors une vraie remediation :

1. vérifie que les IDs existent dans le plan ;
2. rouvre les tâches demandées ;
3. rouvre aussi leurs dépendants transitifs pour éviter un livrable incohérent après correction amont ;
4. conserve le compteur de tentatives et toutes les preuves `run-001`, `run-002`, etc. ;
5. écrit `evidence/remediation_history.json` ;
6. revient à `IN_PROGRESS`.

Si le rapport `FAIL` ne permet pas d'identifier précisément les tâches, le mode fail-closed rouvre toutes les tâches plutôt que de prétendre savoir lesquelles sont sûres.

Si une tâche a déjà atteint `max_task_attempts`, la remediation est refusée et une intervention humaine est requise.

## Phase REVIEW

La revue finale indépendante repart des **consignes originales**, pas seulement du résumé produit par les agents.

Elle vérifie notamment :

- couverture des exigences ;
- livrables manquants ;
- preuves ;
- cohérence ;
- sécurité ;
- ambiguïtés résiduelles ;
- conformité aux critères fournis.

Un `FAIL` utilise la même boucle de remediation que la validation : tâches ciblées, dépendants transitifs, historique conservé, puis retour à `IN_PROGRESS`.

## Phase PACKAGE

Après une review `PASS`, le projet entre en `PACKAGING`.

Le packaging :

1. refuse un dossier de livrables vide ;
2. calcule le SHA-256 de chaque fichier ;
3. crée `<project-id>.zip` ;
4. écrit `deliverables/package_manifest.json` ;
5. écrit `evidence/final_report.json`.

Le ZIP n'est pas une preuve de conformité à lui seul : il est produit uniquement après les gates de validation et de review.

## Phase COMPLETE

`COMPLETE` exige une approbation humaine explicite :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action complete `
  --human-approved
```

L'IA ne s'auto-approuve donc jamais.

## Exécution guidée

Voir l'état :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action status
```

Prévisualiser l'appel d'analyse sans exécuter OpenClaw :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action analyze
```

Lancer réellement une phase agent :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action analyze `
  --execute
```

Exécuter automatiquement les phases possibles jusqu'au prochain gate humain ou à une erreur :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action run `
  --execute
```

Le mode `run` s'arrête volontairement sur :

- clarification humaine requise ;
- échec d'une tâche ;
- validation/review ayant rouvert des tâches ;
- limite de tentatives atteinte ;
- attente d'approbation finale.

Après correction, relancer `--action run --execute` reprend le projet depuis son état persistant et crée une nouvelle tentative sans effacer les preuves précédentes.

## Sécurité

- aucune publication distante automatique ;
- aucune escalade cloud automatique ;
- aucun secret ajouté au prompt depuis les fichiers ;
- les prompts demandent aux agents de lire le snapshot au lieu de recopier les documents en arguments de commande ;
- les reviewers reçoivent les sorties par snapshot contrôlé ;
- les sorties d'agents ne peuvent pas écraser les preuves des exécutions précédentes ;
- une remediation ne remet jamais le compteur de tentatives à zéro ;
- `COMPLETE` reste un gate humain.

## Ce que la CI peut vérifier

La CI peut valider :

- machine d'états ;
- contrats YAML ;
- validation des plans ;
- dépendances de tâches ;
- gates ;
- collecte des sorties ;
- boucle de remediation et dépendants transitifs ;
- conservation des compteurs de tentatives ;
- arrêt à la limite de tentatives ;
- packaging et SHA-256 ;
- obligation de validation humaine ;
- dry-run Python.

La CI ne peut pas prouver que les modèles locaux comprennent correctement un vrai projet. Cette preuve reste à produire par l'E2E et les benchmarks sur la workstation réelle.
