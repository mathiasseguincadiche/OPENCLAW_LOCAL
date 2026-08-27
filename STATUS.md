# État du projet

## Version courante

**0.2.0 — Local-First Project Workflow + Project Orchestrator + V7 Parity Plus**

La V0.2 ne se limite plus au Project Intake. Le dépôt contient maintenant une machine d'états fail-closed capable de transformer un projet fourni en analyse, clarifications, plan, tâches assignées, exécution, preuves, validation, revue et package final.

La filiation avec `openclaw_openrouter` est explicitement conservée : les huit rôles, les projets, les preuves, la séparation producteur/auditeur, la pédagogie, la publication gouvernée et les garde-fous d'ingestion sont présents, mais le chemin IA nominal est désormais local-first.

Le code, les contrats et la CI décrivent l'état attendu ; les performances Intel Arc B580 et la qualité réelle des modèles restent des preuves à produire sur la workstation cible.

## Implémenté

### Project Intake renforcé

- `project.json` et arborescence projet gérée ;
- consignes, sources, contexte, travail, livrables, preuves et diagrammes ;
- archive canonique indépendante sous `state/intake/<project>/<timestamp>/` ;
- scan de secrets avant copie ;
- refus des symlinks dans l'Intake ;
- SHA-256 de chaque fichier ingéré ;
- inventaire MIME et symlink ;
- `manifest.json` et `INGESTION_REPORT.md` ;
- copie projet + archive canonique rendues en lecture seule ;
- ACL Windows RX obligatoire pour l'utilisateur courant ;
- documents entrants traités comme données non fiables ;
- synchronisation contrôlée vers les huit agents ;
- snapshots protégés contre l'écrasement d'un répertoire non géré ;
- dépôt/source réelle conservé comme vérité.

### Project Orchestrator

Machine d'états :

```text
INTAKE_READY
  -> ANALYZED
  -> CLARIFICATION_REQUIRED si nécessaire
  -> PLANNED
  -> ASSIGNED
  -> IN_PROGRESS
  -> VALIDATING
  -> REVIEW
  -> PACKAGING
  -> COMPLETE
```

Implémenté :

- analyse structurée par le Chef des opérations ;
- génération de clarifications explicites ;
- arrêt humain sur clarification bloquante ;
- plan de tâches validé : rôles connus, IDs uniques, dépendances existantes, absence de cycle ;
- packets de tâches versionnables dans `context/tasks/` ;
- assignation aux huit rôles OpenClaw ;
- exécution locale séquentielle par défaut ;
- maximum de tentatives contrôlé par contrat ;
- collecte des sorties par tâche/agent/tentative sans écrasement ;
- snapshots de revue incluant les sorties centrales ;
- validation indépendante `PASS/FAIL` ;
- review finale repartant des consignes originales ;
- remediation avec réouverture ciblée + dépendants transitifs ;
- historique des tentatives conservé ;
- packaging ZIP avec SHA-256 ;
- `package_manifest.json` et `final_report.json` ;
- `COMPLETE` impossible sans approbation humaine ;
- cloud automatique explicitement interdit dans l'orchestrateur.

### Pédagogie et compréhension

- profils `efficient` 90/10, `balanced` 70/30 et `intensive` 60/40 ;
- modes guided/assisted/autonomous/evaluation ;
- priorité à la livraison et à la sécurité ;
- `SKILLS_MATRIX.csv` ;
- `LEARNING_JOURNAL.md` ;
- `TEACH_BACK.md` ;
- `RETENTION_PLAN.yaml` ;
- changement de profil sans effacer l'historique pédagogique ;
- spécialisation Ops/DevOps : Linux, Git, Bash/Python Ops, Terraform/OpenTofu, Ansible, CI/CD, conteneurs, Kubernetes/Helm, sécurité, observabilité et rollback.

### Accessibilité documentaire

- quatre profondeurs : Comprendre, Utiliser, Approfondir, Diagnostiquer ;
- exactitude technique prioritaire ;
- simplification fausse interdite ;
- jargon explicité ;
- sécurité jamais affaiblie pour simplifier ;
- `context/documentation_profile.json` distribué aux agents.

### Publication des projets utilisateur

Machine d'états distincte du cycle d'orchestration :

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

- checks locaux obligatoires avant publication ;
- GitHub et GitLab supportés ;
- CI distante, clone propre, audit indépendant et SHA publié comme preuves ;
- gates humains pour création distante, PR/MR, release et verdict final ;
- CLI `33_project_publication.py`.

### Permissions et séparation des rôles

- Ingénieur sécurité read-only pour les modifications directes de sources ;
- corrections sécurité renvoyées au producteur puis ré-auditées ;
- Architecte sans droits génériques `write/edit/apply_patch/exec/process` ;
- writer `architecture_scoped` limité à `context/architecture/` et `diagrams/` ;
- Auditeur qualité toujours interdit de correction silencieuse.

### Télémétrie opérationnelle

- stockage local append-only dans `evidence/telemetry/runs.jsonl` ;
- agent, modèle, backend, route, durée ;
- TTFT, tokens/s, tokens, VRAM/RAM lorsque réellement observés ;
- tool calls, retries, LOCAL_DEEP, cloud escalation et coût connu ;
- prompts, réponses, secrets et documents privés interdits ;
- métriques inconnues jamais fabriquées ;
- CLI `34_record_telemetry.py` et synthèse projet.

### Modèles et routage

- `qwen-general` -> `qwen3.5:9b` ;
- `gemma-review` -> `gemma4:12b` ;
- `qwen-deep` -> `qwen3.5:27b` comme candidat LOCAL_DEEP ;
- `sera-devops` comme candidat spécialisé ;
- cloud désactivé par défaut et escalade contrôlée par `clawlocal`.

### Recherche Web Local-First

- `web_search` et `web_fetch` sur le parcours nominal ;
- navigateur autorisé par défaut uniquement à `expert-recherche` ;
- fait actuel -> recherche de sources récentes -> raisonnement local ;
- `web_freshness_only` interdit comme justification cloud.

### Backends Intel Arc

- `ollama-vulkan` comme backend nominal ;
- `llama-cpp-sycl` candidat ;
- `llama-cpp-vulkan` candidat ;
- comparaison requise sur B580 avant promotion ;
- aucune promotion automatique depuis la CI.

### FinOps

- cloud désactivé par défaut ;
- limites quotidiennes, mensuelles et par projet ;
- réservation conservatrice avant appel cloud ;
- ledger JSONL hors Git.

### Benchmark et qualification

- suite active `devops-v2` ;
- runner chargé dynamiquement depuis `qualification_policy.yaml` ;
- gate automatique puis qualification manuelle obligatoire ;
- E2E OpenClaw réel requis avant promotion.

### Diagrammes

- politique diagram-as-code ;
- D2, PlantUML et Graphviz ;
- rendu local vers SVG/PNG ;
- renderer distant interdit par défaut.

### Qualité, sécurité et gouvernance

- validateurs dépôt/configuration/version ;
- validateur dédié `35_validate_v7_parity.py` ;
- validations dédiées à la machine d'états du Project Orchestrator ;
- Python 3.12/3.13, Ruff, mypy, pytest + coverage ;
- PowerShell 7, PSScriptAnalyzer et Pester ;
- CodeQL et Dependency Review ;
- secrets hors Git, provider local loopback, exec `ask`, elevated désactivé.

## À exécuter sur matériel réel

Les points suivants **ne peuvent pas être validés par GitHub Actions** :

1. installation complète sur Windows 11 Pro de la workstation cible ;
2. ACL d'Intake dans l'environnement Windows final ;
3. E2E OpenClaw réel avec les modèles chargés ;
4. parcours Project Orchestrator sur un vrai projet multi-documents ;
5. qualité de l'analyse et du plan produits par les modèles locaux ;
6. parcours pédagogique réel et qualité du teach-back ;
7. publication d'un vrai projet jusqu'au clone propre et audit distant ;
8. télémétrie réelle en usage projet ;
9. benchmark Intel Arc B580 pour Ollama/Vulkan ;
10. comparaison Ollama/Vulkan vs llama.cpp/SYCL vs llama.cpp/Vulkan ;
11. qualification 8K/16K et éventuellement 32K ;
12. mesure TTFT, tokens/s, VRAM, RAM, stabilité et tool-calling ;
13. validation de la multimodalité avant usage de production ;
14. qualification séparée de SERA 14B ;
15. validation du coût réel des rares escalades OpenRouter.

## Non prétendu

- équivalence systématique d'un modèle local avec un modèle frontier cloud ;
- débit garanti sur Intel Arc B580 avant benchmark réel ;
- compréhension parfaite d'un projet flou avant E2E réel ;
- capacité à résoudre automatiquement une consigne contradictoire ;
- fiabilité du tool-calling avant E2E sur la machine cible ;
- activation automatique d'un gros modèle LOCAL_DEEP ;
- escalade cloud automatique par le Project Orchestrator ;
- auto-approbation d'un projet ;
- publication distante sans preuve ;
- résultats matériels inventés par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours nominal réellement qualifié sur la workstation Windows 11 + Intel Arc B580, avec au moins un projet complet exécuté de `INTAKE_READY` jusqu'au package final, preuves reproductibles, télémétrie réelle, limites documentées et validation humaine.
