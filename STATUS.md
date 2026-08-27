# État du projet

## Version courante

**0.2.0 — Local-First Project Workflow**

La V0.2 étend le socle V0.1 sans déclarer de qualification matérielle fictive. Le code, les contrats et la CI décrivent l'état attendu ; les performances Intel Arc B580 et la qualité réelle des modèles restent des preuves à produire sur la workstation cible.

## Implémenté dans V0.2

### Orchestration et projets

- huit rôles OpenClaw matérialisés avec workspaces séparés ;
- séparation producteur/auditeur et politiques d'outils par rôle ;
- **Project Intake** avec `project.json`, consignes, sources, contexte, travail, livrables, preuves et diagrammes ;
- synchronisation contrôlée du contexte vers les huit agents ;
- snapshots protégés contre l'écrasement d'un répertoire non géré ;
- dépôt/source réelle conservé comme vérité, le RAG ne remplaçant pas la lecture des fichiers.

### Modèles et routage

- `qwen-general` -> `qwen3.5:9b` ;
- `gemma-review` -> `gemma4:12b` avec tag explicite ;
- `qwen-deep` -> `qwen3.5:27b` comme candidat LOCAL_DEEP ;
- `sera-devops` comme candidat spécialisé nécessitant import/backend/qualification ;
- scripts Windows alimentés par `model_catalog.yaml` plutôt que par des identifiants recopiés ;
- fallback persistant OpenClaw uniquement local ;
- cloud désactivé par défaut et escalade contrôlée par `clawlocal`.

### Recherche Web Local-First

- `web_search` et `web_fetch` sur le parcours nominal ;
- navigateur autorisé par défaut uniquement à `expert-recherche` ;
- fait actuel -> recherche de sources récentes -> raisonnement local ;
- `web_freshness_only` explicitement interdit comme justification cloud ;
- recherche cloud premium uniquement après tentative Web locale ou conflit de sources démontré.

### Backends Intel Arc

- `ollama-vulkan` comme backend nominal V0.2 ;
- `llama-cpp-sycl` candidat ;
- `llama-cpp-vulkan` candidat ;
- comparaison requise sur B580 avant promotion d'un backend ;
- aucune promotion automatique depuis la CI.

### FinOps

- cloud désactivé par défaut ;
- limites quotidiennes, mensuelles et par projet ;
- réservation conservatrice avant appel cloud lorsque le coût exact est inconnu ;
- ledger JSONL hors Git ;
- motif d'escalade et projet traçables.

### Benchmark et qualification

- suite active `devops-v2` ;
- scénarios projet, GitLab CI, Kubernetes, Terraform multi-fichiers, Ansible, sécurité, documentation, diagrammes, Web, discipline agentique et contexte long ;
- runner chargé dynamiquement depuis `qualification_policy.yaml` ;
- contrôles JSON/YAML/contains/not-contains exécutables ;
- contextes requis 8K et 16K, 32K optionnel ;
- gate automatique puis qualification manuelle obligatoire ;
- E2E OpenClaw : huit agents, provider local, tool-calling, réparation après erreur et stabilité.

### Diagrammes

- politique diagram-as-code ;
- D2, PlantUML et Graphviz ;
- rendu local vers SVG/PNG ;
- renderer distant interdit par défaut.

### Qualité, sécurité et gouvernance

- validateurs dépôt/configuration/version ;
- cohérence SemVer `VERSION` / `pyproject.toml` / `clawlocal.__version__` / `CHANGELOG.md` ;
- Python 3.12/3.13, Ruff, mypy, pytest + coverage ;
- PowerShell 7, PSScriptAnalyzer et Pester ;
- CodeQL et Dependency Review ;
- secrets hors Git, provider local loopback, exec `ask`, elevated désactivé ;
- SBOM et attestations pour les releases.

## À exécuter sur matériel réel

Les points suivants **ne peuvent pas être validés par GitHub Actions** :

1. installation complète sur Windows 11 Pro de la workstation cible ;
2. E2E OpenClaw réel avec les modèles chargés ;
3. benchmark Intel Arc B580 pour Ollama/Vulkan ;
4. comparaison Ollama/Vulkan vs llama.cpp/SYCL vs llama.cpp/Vulkan lorsque les backends candidats sont préparés ;
5. qualification 8K/16K et éventuellement 32K ;
6. mesure TTFT, tokens/s, VRAM, RAM, stabilité et tool-calling ;
7. décision `PROMOTE`, `KEEP_CANDIDATE` ou `REJECT` par modèle/backend ;
8. validation de la multimodalité avant usage de production ;
9. qualification séparée de SERA 14B ;
10. validation du coût réel des rares escalades OpenRouter.

## Non prétendu

- équivalence systématique d'un modèle local avec un modèle frontier cloud ;
- débit garanti sur Intel Arc B580 avant benchmark réel ;
- fiabilité du tool-calling avant E2E sur la machine cible ;
- absence de risque d'injection de prompt parce que le modèle est local ;
- capacité de contexte maximale simplement parce qu'un modèle l'annonce ;
- activation automatique d'un gros modèle LOCAL_DEEP ;
- déploiement automatique d'une clé cloud ;
- promotion automatique d'un modèle, backend ou runtime ;
- résultats matériels inventés par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours nominal réellement qualifié sur la workstation Windows 11 + Intel Arc B580, avec preuves reproductibles, limites documentées et validation humaine.
