# État du projet

## Version courante

**0.2.0 — Local-First Project Workflow + Project Orchestrator**

La version publiée reste `0.2.0`. La branche `Unreleased` ajoute maintenant un ensemble de capacités héritées de `openclaw_openrouter` et renforcées pour le fonctionnement local : Intake Integrity, pédagogie, accessibilité documentaire, publication de projets et télémétrie opérationnelle.

Le code, les contrats et la CI décrivent l'état logiciel attendu ; les performances Intel Arc B580 et la qualité réelle des modèles restent des preuves à produire sur la workstation cible.

## Implémenté

### Project Intake + Intake Integrity

- `project.json` et arborescence projet gérée ;
- séparation `intake/` / `sources/` ;
- scan de secrets avant matérialisation du projet ;
- refus des symlinks dans l'intake ;
- SHA-256 par fichier ;
- inventaire MIME ;
- `MANIFEST.json`, `checksums.sha256`, `mime-types.tsv`, `symlinks.txt` et `INGESTION_REPORT.md` ;
- intake verrouillé en lecture seule après ingestion ;
- ACL Windows via `icacls` et mode read-only POSIX pour les tests/CI ;
- documents entrants traités comme données non fiables ;
- dépôt/source réelle conservé comme vérité ;
- synchronisation contrôlée vers les huit agents ;
- snapshots protégés contre l'écrasement d'un répertoire non géré.

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
- clarifications explicites et arrêt humain sur ambiguïté bloquante ;
- plan validé : rôles connus, IDs uniques, dépendances existantes, absence de cycle ;
- packets de tâches dans `context/tasks/` ;
- assignation aux huit rôles OpenClaw ;
- exécution locale séquentielle par défaut ;
- tentatives bornées ;
- collecte des sorties par tâche/agent/tentative sans écrasement ;
- validation indépendante `PASS/FAIL` ;
- revue finale repartant des consignes originales ;
- remediation avec réouverture ciblée et dépendants transitifs ;
- packaging ZIP avec SHA-256 ;
- `COMPLETE` impossible sans approbation humaine ;
- cloud automatique interdit dans l'orchestrateur.

### Learning / pédagogie

Profils :

- `efficient` : 90 % exécution / 10 % apprentissage ;
- `balanced` : 70 % / 30 %, profil par défaut ;
- `intensive` : 60 % / 40 %.

Artefacts :

- `context/PROJECT_GUIDANCE.md` ;
- `context/learning/profile.json` ;
- `SKILLS_MATRIX.csv` ;
- `LEARNING_JOURNAL.md` ;
- `TEACH_BACK.md` ;
- `RETENTION_PLAN.yaml`.

Une compétence ne devient jamais `ACQUIRED` par simple exposition : une preuve d'évaluation ou validation humaine est exigée.

### Accessibilité documentaire progressive

Les documents explicatifs peuvent suivre quatre profondeurs :

1. Comprendre ;
2. Utiliser ;
3. Approfondir ;
4. Diagnostiquer.

L'exactitude technique et le format de livrable imposé restent prioritaires ; aucune simplification ne doit masquer un risque ou prérequis critique.

### Publication des projets utilisateurs

Machine d'états séparée du cycle local :

```text
LOCAL_IN_PROGRESS
 -> LOCAL_VALIDATED
 -> READY_TO_PUBLISH
 -> REMOTE_CREATED
 -> BRANCH_PUSHED
 -> PR_MR_OPEN
 -> CI_GREEN
 -> REMOTE_CLONE_VALIDATED
 -> RELEASE_CREATED (optionnel)
 -> PUBLISHED_AND_VERIFIED
```

Gates : tests, documentation, secret scan, dependency scan, état Git, ignore rules, chemins locaux, rollback, audit indépendant, PR/MR, CI distante, clean clone, SHA publié et approbations humaines. GitHub et GitLab sont déclarés comme forges supportées.

### Télémétrie opérationnelle locale

- ledger JSONL hors Git ;
- événements de routage enregistrables automatiquement quand la racine plateforme est disponible ;
- agrégation par agent, modèle, backend et projet ;
- champs : route, TTFT, durée, prompt/generated tokens, tokens/s, VRAM, RAM, tool calls, retries, LOCAL_DEEP, cloud et coût ;
- prompts, réponses, documents source et secrets interdits ;
- métriques matérielles inventées interdites ;
- export projet vers `evidence/telemetry_summary.json`.

### Permissions agents corrigées

- Architecte solutions : peut produire ADR/schémas, mais `exec`/`process` restent interdits ;
- Ingénieur sécurité : peut analyser mais `write/edit/apply_patch` sont interdits ;
- Chef, Recherche et Auditeur restent read-only sur les livrables audités ;
- elevated reste désactivé et exec global reste `ask`.

### Modèles et routage

- `qwen-general` -> `qwen3.5:9b` ;
- `gemma-review` -> `gemma4:12b` ;
- `qwen-deep` -> `qwen3.5:27b` comme candidat LOCAL_DEEP ;
- `sera-devops` comme candidat spécialisé ;
- cloud désactivé par défaut et escalade contrôlée.

### Recherche Web Local-First

- `web_search` et `web_fetch` sur le parcours nominal ;
- navigateur par défaut uniquement pour `expert-recherche` ;
- source récente -> recherche Web -> raisonnement local ;
- `web_freshness_only` interdit comme justification cloud.

### Backends Intel Arc

- `ollama-vulkan` nominal ;
- `llama-cpp-sycl` candidat ;
- `llama-cpp-vulkan` candidat ;
- aucune promotion automatique depuis la CI.

### FinOps

- cloud désactivé par défaut ;
- limites quotidiennes, mensuelles et par projet ;
- réservation conservatrice avant appel cloud ;
- ledger cloud hors Git.

### Benchmark et qualification

- suite active `devops-v2` ;
- runner chargé dynamiquement depuis `qualification_policy.yaml` ;
- gate automatique puis qualification manuelle ;
- E2E OpenClaw réel requis avant promotion.

### Qualité, sécurité et gouvernance

- validateurs dépôt/configuration/version ;
- validateur de parité V7 dédié ;
- Python 3.12/3.13, Ruff, mypy, pytest + coverage ;
- PowerShell 7, PSScriptAnalyzer et Pester ;
- CodeQL et Dependency Review ;
- SBOM et attestations sur release ;
- secrets hors Git, provider local loopback, exec `ask`, elevated désactivé.

## À exécuter sur matériel réel

Les points suivants ne peuvent pas être validés par GitHub Actions :

1. installation complète sur Windows 11 Pro de la workstation cible ;
2. validation réelle des ACL intake sur le compte utilisateur cible ;
3. E2E OpenClaw avec les modèles chargés ;
4. parcours Project Orchestrator sur un vrai projet multi-documents ;
5. qualité pédagogique et documentaire des sorties locales ;
6. publication réelle d'un projet test GitHub/GitLab avec clean clone ;
7. benchmark Intel Arc B580 pour Ollama/Vulkan ;
8. comparaison Ollama/Vulkan vs llama.cpp/SYCL vs llama.cpp/Vulkan ;
9. qualification 8K/16K et éventuellement 32K ;
10. mesure TTFT, tokens/s, VRAM, RAM, stabilité et tool-calling ;
11. validation de la multimodalité avant usage de production ;
12. qualification séparée de SERA 14B ;
13. validation du coût réel des rares escalades OpenRouter.

## Non prétendu

- équivalence systématique d'un modèle local avec un modèle frontier cloud ;
- débit garanti sur Intel Arc B580 avant benchmark réel ;
- compréhension parfaite d'un projet flou avant E2E réel ;
- capacité à résoudre automatiquement une consigne contradictoire ;
- fiabilité du tool-calling avant E2E sur la machine cible ;
- activation automatique d'un gros modèle LOCAL_DEEP ;
- escalade cloud automatique par le Project Orchestrator ;
- auto-approbation d'un projet ou d'une publication ;
- métriques matérielles inventées par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours nominal réellement qualifié sur la workstation Windows 11 + Intel Arc B580, avec au moins un projet complet exécuté de l'intake jusqu'au package et, pour un scénario de publication, jusqu'à la validation distante, avec preuves reproductibles, limites documentées et validation humaine.
