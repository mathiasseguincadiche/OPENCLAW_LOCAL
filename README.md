# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

`OPENCLAW_LOCAL` est l'évolution locale de `openclaw_openrouter` : la même philosophie OpenClaw + huit rôles + contrats + preuves + audit, mais le parcours nominal ne dépend plus d'un LLM cloud payant. Le système utilise d'abord les modèles locaux, enrichit les faits récents par le Web puis raisonne localement, passe éventuellement en LOCAL_DEEP et ne sollicite OpenRouter qu'après une escalade explicite, autorisée, budgétée et traçable.

L'objectif est aussi d'être **fonctionnellement supérieur** au projet d'origine : Project Orchestrator, intake immuable, pédagogie, documentation progressive, publication gouvernée, télémétrie locale et qualification matérielle sont traités comme des contrats exécutables.

## Architecture

```text
Projet utilisateur
(consignes / cahier des charges / sources / livrables attendus)
           |
           v
     Project Intake
  secrets / symlinks
  SHA-256 / MIME / manifest
  lecture seule / ACL
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

`(*)` Les modèles LOCAL_DEEP restent des candidats jusqu'à qualification réelle.

## Principes de conception

- **Windows natif** : OpenClaw, Gateway, runtime IA et modèles tournent sous Windows 11 Pro ; WSL2 reste un backend DevOps/Linux externe et facultatif.
- **Project-first** : le système prend en charge un projet structuré, pas seulement une conversation.
- **Intake immuable** : les entrées sont non fiables, scannées, inventoriées, hashées puis verrouillées en lecture seule.
- **Orchestration fail-closed** : une phase ne progresse que si ses artefacts et gates existent réellement.
- **Clarification humaine** : une ambiguïté bloquante n'est jamais tranchée arbitrairement par un agent.
- **Local-first** : aucune dépendance LLM cloud n'est requise pour le parcours nominal.
- **Web local-first** : recherche/fetch Web puis raisonnement local avant toute recherche premium.
- **LOCAL_DEEP contrôlé** : un modèle plus lourd n'est utilisé que s'il est disponible et qualifié.
- **Cloud-on-demand** : activation, motif autorisé, préconditions, budget et approbation humaine lorsque requise.
- **Fail closed** : aucun fallback cloud silencieux, aucune promotion automatique de modèle/backend.
- **Huit rôles distincts** : orchestration, recherche, architecture, DevOps, sécurité, release, documentation, audit.
- **Séparation producteur/auditeur** : les rôles de revue ne corrigent pas silencieusement leur propre objet d'audit.
- **Pédagogie sans bloquer la livraison** : profils efficient/balanced/intensive et preuves d'acquisition.
- **Documentation progressive** : Comprendre → Utiliser → Approfondir → Diagnostiquer lorsque pertinent.
- **Publication gouvernée** : PR/MR, CI distante, clean clone, audit indépendant et validation humaine.
- **Télémétrie privacy-first** : métriques opérationnelles hors Git, sans prompts, réponses ni secrets.
- **Preuves avant promesses** : aucune performance Intel Arc B580 n'est déclarée sans mesure réelle.

## Les huit rôles

1. **Chef des opérations** — cadrage, orchestration, risques, priorités et verdict global ;
2. **Expert recherche** — sources, veille, benchmark, vérification des faits et Web récent ;
3. **Architecte solutions** — architecture, ADR, interfaces, compromis et schémas ;
4. **Ingénieur DevOps** — automatisation, IaC, conteneurs, CI/CD, tests et preuves ;
5. **Ingénieur sécurité** — threat model, secrets, hardening, supply chain et scans, sans modification directe des sources ;
6. **Ingénieur release/forges** — Git, GitHub/GitLab, PR/MR, releases et preuves distantes ;
7. **Rédacteur technique** — README, runbooks, vulgarisation et structure pédagogique ;
8. **Auditeur qualité** — conformité, contrôle des preuves et revue finale indépendante.

L'Architecte peut produire des ADR et schémas dans son workspace mais ne peut pas exécuter de commandes. L'Ingénieur sécurité peut analyser et lancer les contrôles autorisés mais ne peut pas `write/edit/apply_patch` sur les sources.

## Project Intake renforcé

La création d'un projet suit désormais :

```text
INPUT
  ↓
scan secrets
  ↓
refus des symlinks
  ↓
copie contrôlée
  ↓
SHA-256 par fichier
  ↓
inventaire MIME
  ↓
MANIFEST.json
  ↓
INGESTION_REPORT.md
  ↓
lecture seule / ACL Windows
  ↓
INTAKE_READY
```

Artefacts créés sous `intake/` :

```text
MANIFEST.json
checksums.sha256
mime-types.tsv
symlinks.txt
INGESTION_REPORT.md
```

Les documents entrants sont explicitement considérés comme **données non fiables**. Une instruction trouvée dans un PDF ou un README ne peut jamais redéfinir les règles de sécurité ou le contrat d'un agent.

Voir [Intake Integrity](docs/INTAKE_INTEGRITY.md).

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

Les retours `VALIDATING -> IN_PROGRESS` et `REVIEW -> IN_PROGRESS` rouvrent réellement les tâches concernées et leurs dépendants transitifs, sans perdre les tentatives antérieures.

## Pédagogie et soutenance

Chaque projet dispose d'un profil :

| Profil | Exécution | Apprentissage | Usage |
|---|---:|---:|---|
| `efficient` | 90 % | 10 % | tâche connue, priorité à la livraison |
| `balanced` | 70 % | 30 % | profil par défaut |
| `intensive` | 60 % | 40 % | formation, soutenance ou évaluation |

Le contexte contient :

```text
context/PROJECT_GUIDANCE.md
context/learning/profile.json
context/learning/SKILLS_MATRIX.csv
context/learning/LEARNING_JOURNAL.md
context/learning/TEACH_BACK.md
context/learning/RETENTION_PLAN.yaml
```

Une compétence ne peut pas devenir `ACQUIRED` sur simple exposition : une validation humaine ou une preuve d'évaluation explicite est nécessaire.

Voir [Learning & Accessibility](docs/LEARNING_AND_ACCESSIBILITY.md).

## Documentation progressive

Pour les contenus explicatifs, les agents utilisent lorsque pertinent quatre profondeurs :

```text
COMPRENDRE
   ↓
UTILISER
   ↓
APPROFONDIR
   ↓
DIAGNOSTIQUER
```

Un format de livrable imposé reste prioritaire, et l'accessibilité ne doit jamais masquer un prérequis critique ou simplifier faussement un risque.

## Publication d'un projet utilisateur

La fin locale du projet et sa publication sont deux choses différentes. La publication suit une machine d'états séparée :

```text
LOCAL_IN_PROGRESS
       ↓
LOCAL_VALIDATED
       ↓
READY_TO_PUBLISH
       ↓
REMOTE_CREATED
       ↓
BRANCH_PUSHED
       ↓
PR_MR_OPEN
       ↓
CI_GREEN
       ↓
REMOTE_CLONE_VALIDATED
       ↓
RELEASE_CREATED (si pertinente)
       ↓
PUBLISHED_AND_VERIFIED
```

GitHub et GitLab sont supportés par contrat. Les transitions sensibles exigent une décision humaine explicite. Une transition enregistrée ne prétend jamais qu'une action distante a été réellement exécutée sans preuve.

Voir [Publication projet](docs/PROJECT_PUBLICATION.md).

## Télémétrie locale

Les événements opérationnels sont conservés hors Git dans :

```text
<OPENCLAW_LOCAL_ROOT>/state/telemetry/events.jsonl
```

Le système peut mesurer ou agréger : agent, modèle, backend, route, TTFT, durée, tokens, tokens/s, VRAM, RAM, tool calls, retries, LOCAL_FAST → LOCAL_DEEP, escalades cloud et coût cloud.

Les champs de prompt/réponse, documents source et secrets sont interdits. Une mesure matérielle absente vaut mieux qu'une mesure inventée.

Voir [Télémétrie](docs/TELEMETRY.md).

## Modèles candidats

| Alias | Runtime | Classe | Usage |
|---|---|---|---|
| `qwen-general` | `qwen3.5:9b` | LOCAL_FAST | généraliste, orchestration, DevOps courant |
| `gemma-review` | `gemma4:12b` | LOCAL_FAST | rédaction, architecture, revue |
| `qwen-deep` | `qwen3.5:27b` | LOCAL_DEEP | raisonnement plus lourd, optionnel |
| `sera-devops` | `sera-14b` | LOCAL_DEEP | software engineering/DevOps spécialisé, import séparé |

Le catalogue `config/v1/model_catalog.yaml` est la source de vérité.

## Backends locaux

La qualification comparative cible :

- `ollama-vulkan` — chemin nominal ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat.

Le backend retenu sera déterminé par mesures réelles : TTFT, tokens/s, VRAM, RAM, stabilité et tool calling.

## Démarrage rapide

Prérequis : Windows 11 Pro x64, PowerShell 7 et WinGet.

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
  --deliverable documentation `
  --learning-profile balanced `
  --classification internal `
  --criticality standard
```

### 2. Lancer l'orchestrateur

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action run `
  --execute
```

Le parcours s'arrête automatiquement lorsqu'une clarification, correction ou approbation humaine est nécessaire.

### 3. Adapter le profil d'apprentissage

```powershell
python .\scripts\33_project_learning.py `
  --project p5-devops `
  --profile intensive
```

### 4. Inspecter la télémétrie

```powershell
python .\scripts\35_telemetry.py --project p5-devops --export-project-summary
```

### 5. Publier seulement si nécessaire

```powershell
python .\scripts\34_project_publication.py `
  --project p5-devops `
  --evidence-key local_tests_green `
  --evidence-value true
```

Les étapes distantes restent sous contrôle humain.

## Recherche Internet récente

```text
LLM local -> web_search/web_fetch -> sources récentes -> synthèse locale
```

Le navigateur est autorisé par défaut uniquement à l'Expert recherche. `web_freshness_only` est interdit comme justification cloud.

## Routage et cloud

Le Project Orchestrator ne déclenche jamais OpenRouter automatiquement. Toute escalade réelle doit respecter `escalation_policy.yaml`, FinOps et les gates humains applicables.

## FinOps

Garde-fous actuels :

- 1 EUR / jour ;
- 5 EUR / mois ;
- 2 EUR / projet et par mois ;
- réservation conservatrice de 0,25 EUR lorsque le coût exact est inconnu.

Le ledger reste hors Git.

## Qualité et sécurité

La CI couvre :

```text
Python 3.12 + 3.13
validate_repository
validate_configs
validate_v7_parity
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

Le validateur de parité empêche notamment la disparition silencieuse des capacités reprises de `openclaw_openrouter` : intake robuste, pédagogie, accessibilité, publication, télémétrie et séparation des permissions.

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Intake](docs/PROJECT_INTAKE.md)
- [Intake Integrity](docs/INTAKE_INTEGRITY.md)
- [Project Orchestrator](docs/PROJECT_ORCHESTRATOR.md)
- [Learning & Accessibility](docs/LEARNING_AND_ACCESSIBILITY.md)
- [Publication projet](docs/PROJECT_PUBLICATION.md)
- [Télémétrie](docs/TELEMETRY.md)
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

La version publiée reste `0.2.0`. Les capacités de parité V7 décrites ici sont ajoutées sous `Unreleased` et constituent la base de la future V0.3 ; elles ne modifient pas la règle selon laquelle la qualification matérielle Intel Arc B580 doit être réalisée sur la workstation cible.

La version `1.0.0` reste réservée à un parcours local réellement qualifié de bout en bout.

## Licence

MIT — voir [LICENSE](LICENSE).
