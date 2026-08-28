# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

`OPENCLAW_LOCAL` reprend l'idée fondatrice de `openclaw_openrouter` — OpenClaw + huit rôles spécialisés + contrats/projets/preuves — mais déplace le parcours nominal vers les modèles locaux afin de réduire fortement la dépendance payante au cloud. OpenRouter reste disponible uniquement comme escalade explicite, budgétée et traçable.

La V0.2 fournit un vrai parcours projet : l'utilisateur dépose consignes, cahier des charges, sources et livrables ; le **Project Orchestrator** transforme ce matériau en analyse, clarifications, plan, tâches attribuées, exécution, preuves, validation, revue indépendante et package final. Les informations récentes sont récupérées sur le Web puis raisonnées localement.

Voir [Filiation V7 / Parity Plus](docs/V7_PARITY_PLUS.md).

## Démarrer en 5 minutes

### Prérequis utilisateur

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap et le téléchargement des trois modèles locaux ;
- espace disque suffisant pour trois modèles 24–27B et le runtime local. La taille réelle dépend des artefacts servis par Ollama : ne pas déduire un volume précis du nombre de paramètres.

Python, Node.js, OpenClaw et Ollama sont contrôlés/installés par le bootstrap à partir du runtime lock du dépôt.

### 1. Cloner et entrer dans le dépôt

```powershell
git clone https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL.git
cd OPENCLAW_LOCAL
```

### 2. Prévisualiser sans modifier la machine

```powershell
.\menu.ps1 -Action install-full -DryRun
```

Le dry-run ne télécharge rien, n'installe rien et ne modifie aucune variable persistante.

### 3. Installer le parcours local complet

```powershell
.\menu.ps1 -Action install-full
```

Par défaut, le runtime géré est placé sous `E:\AI\OpenClawLocal` si `E:` existe, sinon sous `%LOCALAPPDATA%\OpenClawLocal`. `OPENCLAW_LOCAL_ROOT` permet de choisir explicitement un autre emplacement.

Après une première installation, **fermer puis rouvrir PowerShell** afin que le nouveau shell récupère le PATH utilisateur.

### 4. Vérifier l'installation

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

Résultat attendu :

```text
- runtime verrouillé présent
- Ollama accessible uniquement en local
- exactement 3 modèles supportés présents
- 8 agents OpenClaw configurés
- Gateway local joignable
- inférence locale fonctionnelle
- vrai tool-calling E2E fonctionnel
- réparation après erreur d'outil fonctionnelle
- aucune escalade cloud sur le parcours nominal
```

`e2e` produit une preuve locale hors Git. Un succès E2E ne constitue pas encore une qualification de performance de la workstation.

### 5. Qualifier la workstation

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

La qualification benchmarke **Qwen 3.8 27B, Gemma 4 26B et Devstral Small 2 24B**. Les trois sont obligatoires ; l'échec de l'un d'eux fait échouer le gate global. La réussite automatique mène au maximum à `READY_FOR_MANUAL_QUALIFICATION` : les performances B580 et le backend final restent soumis aux preuves réelles et à la revue humaine.

Pour l'exploitation et le dépannage, utiliser [Opérations](docs/OPERATIONS.md) et [Troubleshooting](docs/TROUBLESHOOTING.md).

## Architecture V0.2

```text
Projet utilisateur
(PDF / images / Office / code / sources / livrables)
           |
           v
 Project Intake durci + Document Ingestion
 secrets/liens/SHA-256/MIME/ACL/source_coverage
           |
           v
   Project Orchestrator
           |
     +-----+----------------------------------------------------+
     | ANALYZE -> CLARIFY -> PLAN -> ASSIGN -> EXECUTE          |
     |                    -> VALIDATE -> REVIEW -> PACKAGE       |
     +----------------------------------------------------------+
           |
     Artifact Exchange versionné entre tâches dépendantes
           |
           v
 OpenClaw / Gateway loopback
           |
     8 rôles spécialisés
           |
     +----------------------+----------------------+----------------------+
     |                      |                      |                      |
     v                      v                      v                      |
 Qwen 3.8 27B        Gemma 4 26B       Devstral Small 2 24B            |
 orchestration       architecture       DevOps / code agentique         |
 recherche           rédaction                                         |
 sécurité            audit                                             |
 release             multimodal review                                 |
     |                      |                      |                      |
     +----------------------+----------------------+----------------------+
                            |
                      LOCAL + WEB
                    web_search/fetch
                            |
                      insuffisant ?
                   non /            \ oui démontré
                      v              v
                 livrables       OpenRouter
                                 sous politique
                                 + budget FinOps
                            |
                            v
                 télémétrie locale / preuves
```

La flotte locale est **performance-only** : exactement trois modèles sont déclarés, installables et routables. Il n'existe aucun fallback nominal vers un petit modèle local. La qualification matérielle détermine les performances réelles de ces trois modèles et des backends sur la workstation ; elle ne change pas la liste des modèles supportés.

## Principes de conception

- **Windows natif** : OpenClaw, Gateway, runtime IA et modèles tournent sous Windows 11 Pro ; WSL2 Ubuntu reste un environnement DevOps/Linux externe.
- **Project-first** : le système prend en charge un projet structuré, pas seulement une conversation.
- **Intake immuable** : archive canonique, SHA-256, MIME, refus des symlinks/junctions/reparse points, secrets bloquants et ACL Windows.
- **Entrées non fiables** : un document reçu ne peut jamais redéfinir la politique des agents.
- **Orchestration fail-closed** : une phase ne progresse que si son artefact/gate existe réellement.
- **Clarification humaine** : une ambiguïté bloquante n'est jamais résolue arbitrairement par un agent.
- **Local-first** : aucune dépendance LLM cloud n'est requise pour le parcours nominal.
- **Performance-only local** : seuls Qwen 3.8 27B, Gemma 4 26B et Devstral Small 2 24B sont supportés localement.
- **Web local-first** : une donnée récente déclenche d'abord recherche/fetch Web + raisonnement local.
- **Cloud-on-demand** : activation, motif autorisé, préconditions, réservation FinOps atomique et éventuellement validation humaine.
- **Fail closed** : aucun fallback cloud silencieux, aucune promotion automatique de modèle/backend.
- **Huit rôles distincts** : orchestration, recherche, architecture, DevOps, sécurité, release, documentation, audit.
- **Séparation producteur/auditeur** lorsque cela est praticable, avec changement de famille de modèle lorsque le producteur et le reviewer seraient sinon identiques.
- **Architecture bornée** : l'Architecte produit ADR/schémas via un writer spécialisé, sans droits d'écriture génériques.
- **Sécurité read-only** : l'Ingénieur sécurité audite et propose ; il ne corrige pas directement les sources.
- **Pédagogie utile** : efficient/balanced/intensive sans bloquer la livraison.
- **Documentation progressive** : Comprendre, Utiliser, Approfondir, Diagnostiquer.
- **Publication gouvernée** : GitHub/GitLab avec checks, preuves distantes, clone propre et gates humains.
- **Télémétrie locale** : métriques observées sans prompts, réponses, secrets ni documents privés.
- **Workspaces confinés** : filesystem limité au workspace ; symlinks/junctions/reparse points refusés sur les frontières gérées ; exec soumis à approbation ; elevated désactivé.
- **FinOps** : limites quotidiennes, mensuelles et par projet ; réservation atomique avant appel cloud ; ledger hors Git.
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

Les retours `VALIDATING -> IN_PROGRESS` et `REVIEW -> IN_PROGRESS` sont utilisés lorsque des corrections sont nécessaires. Les tâches concernées et leurs dépendants transitifs sont rouverts sans effacer les tentatives précédentes.

## Flotte modèles — performance-only

| Alias | Runtime | Classe | Usage nominal |
|---|---|---|---|
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX | Chef, recherche, sécurité, release et raisonnement transversal |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP | architecture, rédaction, audit et contre-revue multimodale |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST | DevOps, code agentique, outils dépôt et éditions multi-fichiers |

Le catalogue `config/v1/model_catalog.yaml` est la source de vérité et contient **exactement ces trois modèles locaux**. Aucun quatrième modèle local, modèle fast ou modèle legacy n'est un fallback supporté.

La qualification matérielle est obligatoire avant toute affirmation de débit, latence, VRAM/RAM, stabilité ou contexte soutenable sur Intel Arc B580. Elle benchmarke les trois modèles supportés ; elle ne sert pas à promouvoir un modèle non supporté dans le routage.

## Backends locaux

La V0.2 prépare une qualification comparative sur Intel Arc B580 :

- `ollama-vulkan` — chemin nominal V0.2 ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat.

Le vainqueur ne sera déterminé qu'après mesures réelles : TTFT, tokens/s, VRAM, RAM, stabilité et tool calling.

## Parcours de contrôle rapide

Après une installation déjà réalisée :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Pour télécharger et qualifier explicitement la flotte supportée :

```powershell
.\scripts\windows\03_pull_models.ps1
.\scripts\windows\07_run_qualification.ps1
```

Ces commandes couvrent les trois modèles requis ; aucune option n'est nécessaire pour activer un modèle local supplémentaire.

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

Avant `INTAKE_READY`, le système vérifie les secrets évidents et les symlinks/junctions/reparse points, crée une archive canonique sous `state/intake/`, calcule SHA-256/MIME, écrit les preuves d'ingestion puis rend l'intake en lecture seule.

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

Voir [Project Intake](docs/PROJECT_INTAKE.md), [Intégrité Intake](docs/INTAKE_INTEGRITY.md) et [Project Orchestrator](docs/PROJECT_ORCHESTRATOR.md).

## Artefacts projet enrichis

```text
context/
├── project_analysis.json
├── clarifications.json
├── project_plan.json
├── task_assignments.json
├── documentation_profile.json
├── architecture/
├── learning/
│   ├── SKILLS_MATRIX.csv
│   ├── LEARNING_JOURNAL.md
│   ├── TEACH_BACK.md
│   ├── RETENTION_PLAN.yaml
│   └── learning_profile.json
├── publication/
│   └── publication.json
└── tasks/

evidence/
├── intake/
│   ├── manifest.json
│   ├── checksums.sha256
│   ├── mime-types.tsv
│   ├── symlinks.txt
│   └── INGESTION_REPORT.md
├── orchestration/
├── telemetry/
│   └── runs.jsonl
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

## Comprendre et apprendre

Le profil par défaut est `balanced` (70 % exécution / 30 % apprentissage). Il peut être changé sans effacer le journal ou la matrice de compétences :

```powershell
python .\scripts\36_project_learning.py `
  --project p5-devops `
  --action profile `
  --profile intensive `
  --mode evaluation
```

Les profils disponibles sont `efficient`, `balanced` et `intensive`. Une compétence n'est jamais déclarée acquise uniquement parce qu'elle a été mentionnée par un agent.

Voir [Pédagogie](docs/PEDAGOGY.md) et [Accessibilité](docs/ACCESSIBILITY.md).

## Publication d'un projet utilisateur

Après validation locale, l'Ingénieur Release/Forge pilote une machine d'états distincte :

```text
LOCAL_IN_PROGRESS
→ LOCAL_VALIDATED
→ READY_TO_PUBLISH
→ REMOTE_CREATED
→ BRANCH_PUSHED
→ PR_MR_OPEN
→ CI_GREEN
→ REMOTE_CLONE_VALIDATED
→ RELEASE_CREATED (optionnel)
→ PUBLISHED_AND_VERIFIED
```

Exemple :

```powershell
python .\scripts\33_project_publication.py `
  --project p5-devops `
  --action status
```

Les transitions distantes importantes restent soumises à approbation humaine et à des preuves observées.

Voir [Publication projet](docs/PROJECT_PUBLICATION.md).

## Télémétrie opérationnelle

Les métriques réellement observées peuvent être enregistrées localement :

```powershell
python .\scripts\34_record_telemetry.py `
  --project p5-devops `
  --agent ingenieur-devops `
  --model devstral-devops `
  --backend ollama-vulkan `
  --route-kind local_specialist `
  --duration-ms 8120 `
  --tokens-per-second 18.7 `
  --generated-tokens 380 `
  --success
```

La télémétrie interdit prompts, réponses, secrets et documents privés. Une métrique non mesurée reste absente ; elle n'est jamais fabriquée.

Voir [Télémétrie](docs/TELEMETRY.md).

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

Cette route utilise **Devstral Small 2 24B** pour l'Ingénieur DevOps. Les autres rôles utilisent Qwen 3.8 27B ou Gemma 4 26B selon leur spécialité ; aucun petit modèle local n'est utilisé comme fallback.

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
- réservation conservatrice par défaut : 0,25 EUR lorsque le coût exact est inconnu ;
- réservation écrite atomiquement sous verrou avant l'exécution cloud réelle ;
- règlement de la réservation par le coût observé via `scripts/30_record_cloud_cost.py --reservation-id ...`.

Le ledger append-only reste sous `<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl` et n'est jamais commité. Une réservation active est prise en compte dans les limites afin que deux agents concurrents ne puissent pas consommer le même budget disponible.

Voir [FinOps](docs/FINOPS.md).

## Benchmark et qualification

La suite active est **`devops-v2`**. Elle couvre notamment analyse de projet, GitLab CI, Kubernetes, Terraform multi-fichiers, Ansible, sécurité, documentation, diagrammes, Web, discipline agentique et contexte long.

Un gate automatique réussi signifie au mieux `READY_FOR_MANUAL_QUALIFICATION`. **Qwen 3.8 27B, Gemma 4 26B et Devstral Small 2 24B sont tous les trois requis** : l'échec de l'un des trois fait échouer le gate de qualification de la flotte. La promotion matérielle exige toujours E2E OpenClaw, stabilité, qualification B580 et revue humaine.

## Qualité et sécurité

La CI couvre :

```text
Python 3.12 + 3.13
validate_repository
validate_configs
validate_v7_parity
validate_v7_superset
validate_document_flow
validate_model_fleet
validate_release
Ruff
mypy
pytest + coverage >= 75 %
PowerShell 7
PSScriptAnalyzer
Pester
Tests de confinement Windows (symlink/junction/reparse)
CodeQL
Dependency Review / pip-audit fallback
```

Les GitHub Actions critiques sont référencées par SHA de commit immuable. Les validateurs vérifient notamment Project Intake / Project Orchestrator, machine d'états, gates humains, Web local-first, FinOps, backends, tags explicites des modèles Ollama, **flotte locale performance-only de trois modèles**, qualification obligatoire des trois modèles supportés, Intake immuable, pédagogie, accessibilité, publication, télémétrie et séparation Architecte/Sécurité/Auditeur.

## Documentation

- [Portail documentaire](docs/README.md)
- [Filiation V7 / Parity Plus](docs/V7_PARITY_PLUS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Intake](docs/PROJECT_INTAKE.md)
- [Intégrité Intake](docs/INTAKE_INTEGRITY.md)
- [Project Orchestrator](docs/PROJECT_ORCHESTRATOR.md)
- [Pédagogie](docs/PEDAGOGY.md)
- [Accessibilité](docs/ACCESSIBILITY.md)
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

La version courante reste `0.2.0`. Ces ajouts renforcent la V0.2 sans prétendre qu'un benchmark matériel ou un vrai projet a été exécuté automatiquement par la CI.

La **qualification matérielle Intel Arc B580 n'est pas déclarée tant qu'elle n'a pas été exécutée sur la workstation cible**. Voir [STATUS.md](STATUS.md).

La version `1.0.0` reste réservée à un parcours local réellement qualifié.

## Licence

MIT — voir [LICENSE](LICENSE).
