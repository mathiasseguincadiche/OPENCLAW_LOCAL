# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

La V0.2 transforme le socle OpenClaw en workflow projet complet : l'utilisateur fournit consignes, cahier des charges, sources et livrables ; les huit agents travaillent principalement avec des modèles locaux ; les informations récentes sont récupérées sur le Web puis raisonnées localement ; OpenRouter reste une escalade explicite, budgétée et traçable.

## Architecture V0.2

```text
Projet utilisateur
(consignes / sources / livrables)
           |
           v
     Project Intake
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
# Prévisualiser l'installation complète
.\menu.ps1 -Action install-full -DryRun

# Installer runtime, modèles requis, OpenClaw et les 8 agents
.\menu.ps1 -Action install-full

# Vérifier le parcours local
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify

# E2E OpenClaw réel
.\menu.ps1 -Action e2e

# Qualification matérielle locale (aucun cloud)
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

## Prendre en charge un projet

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --source 'C:\Projets\P5\repository' `
  --deliverable README `
  --deliverable runbook

python .\scripts\31_sync_project_context.py `
  --project p5-devops `
  --agent all
```

Le projet géré contient `intake/`, `sources/`, `context/`, `work/`, `deliverables/`, `evidence/` et `diagrams/`. Les snapshots agents refusent d'écraser un répertoire non géré.

Voir [Project Intake](docs/PROJECT_INTAKE.md).

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

Une exécution cloud réelle nécessite aussi `OPENROUTER_API_KEY` local. Aucun secret n'est écrit dans Git.

## FinOps

Garde-fous V0.2 :

- 1 EUR / jour ;
- 5 EUR / mois ;
- 2 EUR / projet et par mois ;
- réservation conservatrice par défaut : 0,25 EUR avant appel lorsque le coût exact est inconnu.

Le ledger reste sous `<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl` et n'est jamais commité.

Voir [FinOps](docs/FINOPS.md).

## Benchmark et qualification

La suite active est **`devops-v2`**. Elle couvre notamment :

- analyse de projet ;
- GitLab CI ;
- diagnostic Kubernetes ;
- Terraform multi-fichiers ;
- idempotence Ansible ;
- sécurité CI ;
- runbook/rollback ;
- diagramme D2 ;
- discipline Web ;
- structure d'intention outil ;
- réparation après erreur outil ;
- contexte synthétique long.

Le runner charge dynamiquement la suite définie dans `qualification_policy.yaml`.

Un gate automatique réussi signifie au mieux `READY_FOR_MANUAL_QUALIFICATION`. La promotion exige toujours E2E OpenClaw, stabilité, qualification matérielle B580 et revue humaine.

## Qualité et sécurité

La CI couvre :

```text
Python 3.12 + 3.13
validate_repository
validate_configs V0.2
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

Les validateurs vérifient également la cohérence Project/Web/FinOps/backends, le tag explicite des modèles Ollama et l'absence de `runtime_id` recopiés dans les scripts Windows.

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Intake](docs/PROJECT_INTAKE.md)
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

La version V0.2 est cohérente entre `VERSION`, `pyproject.toml`, `clawlocal.__version__`, les contrats `platform_version` et `CHANGELOG.md`.

La **qualification matérielle Intel Arc B580 n'est pas déclarée tant qu'elle n'a pas été exécutée sur la workstation cible**. Voir [STATUS.md](STATUS.md).

La version `1.0.0` reste réservée à un parcours local réellement qualifié.

## Licence

MIT — voir [LICENSE](LICENSE).
