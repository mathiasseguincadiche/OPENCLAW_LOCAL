# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

La V0.2 fournit maintenant un vrai parcours projet : l'utilisateur dépose consignes, cahier des charges, sources et livrables ; le **Project Orchestrator** transforme ce matériau en analyse, clarifications, plan, tâches attribuées, exécution, preuves, validation, revue indépendante et package final. Les huit agents travaillent principalement avec des modèles locaux ; les informations récentes sont récupérées sur le Web puis raisonnées localement ; OpenRouter reste une escalade explicite, budgétée et traçable.

## Architecture V0.2

```text
Projet utilisateur
(consignes / sources / livrables)
           |
           v
     Project Intake
           |
           v
   Project Orchestrator
           |
     +-----+----------------------------------------------------+
     | ANALYZE -> CLARIFY -> PLAN -> ASSIGN -> EXECUTE          |
     |                    -> VALIDATE -> REVIEW -> PACKAGE       |
     +----------------------------------------------------------+
           |
           v
 OpenClaw / Gateway loopback
           |
     8 rôles spécialisés
           |
   +-------+----------------------+------------------+
   |                              |                  |
   v                              v                  v
LOCAL_FAST                  LOCAL + WEB        LOCAL_DEEP
Qwen 3.5 9B                web_search/fetch   Qwen 3.5 27B (*)
Gemma 4 12B                browser recherche  SERA 14B (*)
   |                              |                  |
   +------------------------------+------------------+
                                  |
                            insuffisant ?
                           non /        \ oui
                              v          v
                         livrables   OpenRouter
                                      sous politique
                                      + budget FinOps
```

`(*)` Les modèles `LOCAL_DEEP` sont des **candidats**. Ils ne deviennent actifs qu'après import/backend et qualification réelle.

## Principes de conception

- **Windows natif** : OpenClaw, Gateway, runtime IA et modèles tournent sous Windows 11 Pro ; WSL2 Ubuntu reste un environnement DevOps/Linux externe.
- **Project-first** : le système prend en charge un projet structuré, pas seulement une conversation.
- **Orchestration fail-closed** : une phase ne progresse que si son artefact/gate existe réellement.
- **Clarification humaine** : une ambiguïté bloquante n'est jamais résolue arbitrairement par un agent.
- **Local-first** : aucune dépendance LLM cloud n'est requise pour le parcours nominal.
- **Web local-first** : une donnée récente déclenche d'abord recherche/fetch Web + raisonnement local.
- **Cloud-on-demand** : activation, motif autorisé, préconditions, budget et éventuellement validation humaine.
- **Fail closed** : aucun fallback cloud silencieux, aucune promotion automatique de modèle/backend.
- **Huit rôles distincts** : orchestration, recherche, architecture, DevOps, sécurité, release, documentation, audit.
- **Séparation producteur/auditeur** lorsque cela est praticable.
- **Workspaces confinés** : filesystem limité au workspace ; exec soumis à approbation ; elevated désactivé.
- **FinOps** : limites quotidiennes, mensuelles et par projet ; ledger hors Git.
- **Diagram-as-code** : D2, PlantUML et Graphviz pour les schémas techniques locaux.
- **Preuves avant promesses** : les performances Intel Arc B580 restent à mesurer sur la machine réelle.
- **Approbation finale humaine** : un projet ne peut pas s'auto-déclarer `COMPLETE`.

## Machine d'états projet

```text
INTAKE_READY
    ↓
ANALYZED
    ↓
CLARIFICATION_REQUIRED (si nécessaire)
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

Les retours `VALIDATING -> IN_PROGRESS` et `REVIEW -> IN_PROGRESS` sont prévus lorsque des corrections sont nécessaires.

## Modèles candidats V0.2

| Alias | Runtime | Classe | Usage |
|---|---|---|---|
| `qwen-general` | `qwen3.5:9b` | LOCAL_FAST | généraliste, orchestration, DevOps courant |
| `gemma-review` | `gemma4:12b` | LOCAL_FAST | rédaction, architecture, revue |
| `qwen-deep` | `qwen3.5:27b` | LOCAL_DEEP | raisonnement plus lourd, optionnel |
| `sera-devops` | `sera-14b` | LOCAL_DEEP | software engineering/DevOps spécialisé, import séparé |

Le catalogue `config/v1/model_catalog.yaml` est la source de vérité. Les scripts Windows lisent le catalogue au lieu de recopier les identifiants de modèles.

## Backends locaux

La V0.2 prépare une qualification comparative sur Intel Arc B580 :

- `ollama-vulkan` — chemin nominal V0.2 ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat.

Le vainqueur ne sera déterminé qu'après mesures réelles : TTFT, tokens/s, VRAM, RAM, stabilité et tool calling.

## Démarrage rapide

Prérequis utilisateur : **Windows 11 Pro x64, PowerShell 7 et WinGet**.

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

## Prendre en charge un projet

### 1. Créer l'intake

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --intake 'C:\Projets\P5\cahier-des-charges.pdf' `
  --source 'C:\Projets\P5\repository' `
  --deliverable terraform `
  --deliverable ansible `
  --deliverable documentation
```

Le projet géré contient `intake/`, `sources/`, `context/`, `work/`, `deliverables/`, `evidence/` et `diagrams/`.

### 2. Voir l'état

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action status
```

### 3. Prévisualiser une phase sans appeler le modèle

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action analyze
```

### 4. Lancer le parcours local

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action run `
  --execute
```

Le parcours s'arrête automatiquement si :

- une clarification humaine est requise ;
- une tâche échoue ;
- la validation échoue ;
- la revue finale échoue ;
- l'approbation humaine finale est attendue.

### 5. Résoudre une ambiguïté

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action resolve `
  --clarification-id clarification-001 `
  --answer 'Utiliser le mode Docker local.'
```

### 6. Valider la fin du projet

Après `PACKAGING` et vérification humaine :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action complete `
  --human-approved
```

Voir [Project Intake](docs/PROJECT_INTAKE.md) et [Project Orchestrator](docs/PROJECT_ORCHESTRATOR.md).

## Artefacts d'orchestration

```text
context/
├── project_analysis.json
├── clarifications.json
├── project_plan.json
├── task_assignments.json
└── tasks/

evidence/
├── orchestration/
├── task_results.json
├── validation_report.json
├── review_report.json
└── final_report.json

deliverables/
├── tasks/
├── package_manifest.json
└── <project-id>.zip
```

Les sorties de tâches sont historisées par tâche, agent et tentative (`run-001`, `run-002`, etc.) afin de ne pas écraser les preuves précédentes.

## Recherche Internet récente

Une information récente suit d'abord :

```text
LLM local -> web_search/web_fetch -> sources récentes -> synthèse locale
```

Le navigateur est autorisé par défaut uniquement à l'Expert recherche pour les sites nécessitant une navigation complexe.

`web_freshness_only` est explicitement interdit comme raison de cloud. Une recherche premium n'est autorisée qu'après une tentative locale ou en cas de conflit de sources démontré selon la politique.

Voir [Recherche Web Local-First](docs/WEB_LOCAL_FIRST.md).

## Routage et cloud

Plan local :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce problème Kubernetes.'
```

Escalade de recherche après tentative Web locale :

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis cette recherche.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops
```

Le **Project Orchestrator n'effectue jamais cette escalade automatiquement**. Une exécution cloud réelle nécessite aussi `OPENROUTER_API_KEY` local.

## FinOps

Garde-fous V0.2 :

- 1 EUR / jour ;
- 5 EUR / mois ;
- 2 EUR / projet et par mois ;
- réservation conservatrice par défaut : 0,25 EUR avant appel lorsque le coût exact est inconnu.

Le ledger reste sous `<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl` et n'est jamais commité.

Voir [FinOps](docs/FINOPS.md).

## Benchmark et qualification

La suite active est **`devops-v2`**. Elle couvre notamment analyse de projet, GitLab CI, Kubernetes, Terraform multi-fichiers, Ansible, sécurité, documentation, diagrammes, Web, discipline agentique et contexte long.

Un gate automatique réussi signifie au mieux `READY_FOR_MANUAL_QUALIFICATION`. La promotion exige toujours E2E OpenClaw, stabilité, qualification matérielle B580 et revue humaine.

## Qualité et sécurité

La CI couvre :

```text
Python 3.12 + 3.13
validate_repository
validate_configs
validate_release
Ruff
mypy
pytest + coverage >= 75 %
PowerShell 7
PSScriptAnalyzer
Pester
CodeQL
Dependency Review / pip-audit fallback
```

Les validateurs vérifient également la cohérence Project Intake / Project Orchestrator, la machine d'états, les gates humains, Web local-first, FinOps, les backends, le tag explicite des modèles Ollama et l'absence de `runtime_id` recopiés dans les scripts Windows.

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Intake](docs/PROJECT_INTAKE.md)
- [Project Orchestrator](docs/PROJECT_ORCHESTRATOR.md)
- [Recherche Web Local-First](docs/WEB_LOCAL_FIRST.md)
- [Backends locaux](docs/RUNTIME_BACKENDS.md)
- [Modèles locaux](docs/MODELES_LOCAUX.md)
- [Routage hybride](docs/ROUTAGE_HYBRIDE.md)
- [FinOps](docs/FINOPS.md)
- [Diagrammes](docs/DIAGRAMMES.md)
- [Intégration OpenClaw](docs/OPENCLAW_INTEGRATION.md)
- [Benchmark](docs/BENCHMARK.md)
- [Qualification](docs/QUALIFICATION.md)
- [Opérations](docs/OPERATIONS.md)
- [Sécurité](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Gouvernance GitHub](docs/GITHUB_GOVERNANCE.md)

## Version et état

La version courante reste `0.2.0`. Le Project Orchestrator complète la promesse V0.2 de **workflow projet complet** sans créer artificiellement une nouvelle génération de fichiers ou de contrats.

La **qualification matérielle Intel Arc B580 n'est pas déclarée tant qu'elle n'a pas été exécutée sur la workstation cible**. Voir [STATUS.md](STATUS.md).

La version `1.0.0` reste réservée à un parcours local réellement qualifié.

## Licence

MIT — voir [LICENSE](LICENSE).
