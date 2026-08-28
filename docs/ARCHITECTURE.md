# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` est une plateforme IA **local-first, multi-agents et project-first** pour Windows 11 Pro x64. Le runtime IA nominal reste natif Windows. WSL2 peut héberger des outils et projets DevOps/Linux, mais il n'est pas l'hôte du runtime IA nominal.

Le système sépare explicitement :

- le **control plane déterministe** `clawlocal` ;
- les **huit rôles OpenClaw** ;
- la **flotte locale fermée de trois modèles** ;
- les **backends d'inférence** ;
- le **projet central**, source de vérité ;
- les **workspaces agents**, snapshots jetables ;
- l'**escalade cloud**, facultative, explicite et budgétée.

## Architecture de référence

```text
HOST Windows 11 Pro x64
|
+-- <OPENCLAW_LOCAL_ROOT>
|    +-- runtime/
|    |    +-- node/
|    |    +-- npm-global/          -> OpenClaw
|    |    +-- venv/                -> clawlocal
|    +-- models/
|    |    +-- ollama/              -> OLLAMA_MODELS
|    +-- projects/                 -> source de vérité des projets
|    +-- workspaces/               -> snapshots gérés des 8 agents
|    +-- state/                    -> état local, FinOps, intake canonique
|    +-- proofs/                   -> preuves E2E/runtime locales
|
+-- Ollama loopback 127.0.0.1:11434
|
+-- OpenClaw Gateway loopback
|    +-- chef-operations
|    +-- expert-recherche
|    +-- architecte-solutions
|    +-- ingenieur-devops
|    +-- ingenieur-securite
|    +-- ingenieur-release-forges
|    +-- redacteur-technique
|    +-- auditeur-qualite
|
+-- Flotte locale supportée — exactement 3 modèles
|    +-- qwen-max          -> qwen3.8:27b              [LOCAL_MAX]
|    +-- gemma-deep        -> gemma4:26b               [LOCAL_DEEP]
|    +-- devstral-devops   -> devstral-small-2:24b     [LOCAL_SPECIALIST]
|
+-- Backends
|    +-- ollama-vulkan     -> nominal pré-qualification
|    +-- llama-cpp-sycl    -> candidat
|    +-- llama-cpp-vulkan  -> candidat
|
+-- OpenRouter
     +-- escalade explicite uniquement
     +-- préconditions + approbation éventuelle + FinOps
```

Il n'existe **aucun modèle LOCAL_FAST, petit fallback ou quatrième candidat local** dans la flotte supportée. Le catalogue `config/v1/model_catalog.yaml` est la source de vérité des trois modèles locaux.

## Stockage

Le bootstrap choisit par défaut :

```text
E:\AI\OpenClawLocal
```

si `E:` existe ; sinon `%LOCALAPPDATA%\OpenClawLocal`. `OPENCLAW_LOCAL_ROOT` permet de choisir explicitement une autre racine.

Les modèles Ollama sont confinés sous :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

via `OLLAMA_MODELS`. Les projets centraux sont conservés sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>
```

`runtime/` et `workspaces/` sont reconstruisibles. `projects/`, `state/` et les preuves utiles sont des données opérationnelles à protéger.

## Flux projet principal

```text
consignes + PDF + images + Office + code + sources
                         |
                         v
                Project Intake durci
                         |
                         v
               Document Ingestion
                         |
                         v
                 Project Orchestrator
                         |
      ANALYZE -> CLARIFY -> PLAN -> ASSIGN
                         |
                      EXECUTE
                         |
              Artifact Exchange versionné
                         |
                      VALIDATE
                         |
                       REVIEW
                         |
                      PACKAGE
                         |
                APPROBATION HUMAINE
                         |
                      COMPLETE
```

Le cloud n'est pas une étape automatique de ce flux.

## Control plane et modèles

Le Project Orchestrator et les modules `clawlocal` constituent un **control plane déterministe**. Ils :

- contrôlent les états et transitions ;
- valident les contrats et dépendances ;
- construisent et synchronisent les snapshots ;
- collectent les sorties ;
- maintiennent l'Artifact Exchange ;
- calculent les hashes et preuves ;
- imposent les gates ;
- gouvernent FinOps, publication et télémétrie ;
- refusent les transitions incohérentes.

Les modèles produisent le contenu sémantique : analyse, plan, rédaction, code, diagnostic, revue et explication. Un modèle ne peut pas promouvoir l'état canonique d'un projet par simple affirmation.

## Rôles et séparation des responsabilités

| Rôle | Responsabilité principale |
|---|---|
| Chef des opérations | cadrage, plan, délégation, consolidation |
| Expert recherche | recherche Web, sources, synthèse factuelle |
| Architecte solutions | architecture, ADR, compromis, schémas |
| Ingénieur DevOps | implémentation, automatisation, CI/CD, IaC, conteneurs |
| Ingénieur sécurité | audit et findings, sans correction silencieuse |
| Ingénieur Release/Forges | Git, PR/MR, CI distante, release et publication |
| Rédacteur technique | documentation progressive et fidèle |
| Auditeur qualité | validation indépendante et verdict |

L'Architecte écrit uniquement via un writer borné à `context/architecture/` et `diagrams/`. Sécurité et Audit restent non-mutants vis-à-vis des sources auditées.

## Flotte locale et routage nominal

| Agent | Modèle nominal |
|---|---|
| Chef des opérations | Qwen 3.8 27B |
| Expert recherche | Qwen 3.8 27B + Web |
| Architecte solutions | Gemma 4 26B |
| Ingénieur DevOps | Devstral Small 2 24B |
| Ingénieur sécurité | Qwen 3.8 27B |
| Release/Forges | Qwen 3.8 27B |
| Rédacteur technique | Gemma 4 26B |
| Auditeur qualité | Gemma 4 26B, ou Qwen si le producteur est Gemma |

Les fallbacks locaux restent strictement dans ces trois modèles. Une indisponibilité locale ne déclenche jamais automatiquement OpenRouter.

## Modèle et backend sont indépendants

Une classe de modèle n'est pas un backend :

```text
Modèles
  +-- LOCAL_MAX        -> Qwen 3.8 27B
  +-- LOCAL_DEEP       -> Gemma 4 26B
  +-- LOCAL_SPECIALIST -> Devstral Small 2 24B

Backends
  +-- Ollama/Vulkan
  +-- llama.cpp/SYCL
  +-- llama.cpp/Vulkan
```

Le backend final est choisi uniquement après qualification réelle sur la workstation cible.

## Intake et documents

Le Project Intake crée une archive canonique sous `state/intake/<project>/<timestamp>/`, puis une copie gérée sous `projects/<id>/intake/`.

Les entrées sont considérées comme non fiables :

- scan de secrets ;
- refus des symlinks, junctions et reparse points ;
- SHA-256 et MIME ;
- ACL/lecture seule ;
- limites sur PDF et conteneurs Office ;
- aucune exécution de document entrant.

La Document Ingestion produit `context/ingestion/` sans remplacer les originaux.

## Artifact Exchange et cohérence entre agents

Le projet central reste la source de vérité. Chaque tentative de tâche conserve une version immuable :

```text
context/exchange/<task-id>/self/run-001/
context/exchange/<task-id>/self/run-002/
```

Après `PASS`, les artefacts sont propagés aux dépendants directs et transitifs :

```text
context/exchange/<consumer>/dependencies/<producer>/run-NNN/
```

Les agents impactés sont resynchronisés avant leur prochaine tâche. Une correction amont peut rouvrir les dépendants transitifs afin d'éviter des livrables construits sur une version obsolète.

## Pédagogie

La pédagogie est transversale aux huit rôles et aux trois modèles. Trois profils existent :

- `efficient` : 90 % exécution / 10 % apprentissage ;
- `balanced` : 70 % / 30 % ;
- `intensive` : 60 % / 40 %.

La documentation progressive suit quatre profondeurs : **Comprendre, Utiliser, Approfondir, Diagnostiquer**.

## Web et cloud

Une donnée récente suit d'abord :

```text
agent local
  -> web_search / web_fetch / browser si autorisé
  -> sources récentes
  -> raisonnement local
```

Une escalade cloud exige un motif versionné, ses préconditions, le budget disponible, une réservation FinOps atomique juste avant l'appel réel et une approbation humaine lorsque le motif l'exige.

## Sources de vérité

- `config/v1/model_catalog.yaml` : trois modèles supportés ;
- `config/v1/model_routing.yaml` : routage par rôle ;
- `config/v1/runtime_backends.yaml` : backends ;
- `config/v1/orchestration_policy.yaml` : états et gates ;
- `config/v1/document_ingestion_policy.yaml` : documents ;
- `config/v1/artifact_exchange_policy.yaml` : propagation ;
- `config/v1/pedagogy_policy.yaml` : pédagogie ;
- `config/v1/tool_policy.yaml` : permissions ;
- `config/v1/budget_policy.yaml` : FinOps ;
- `config/v1/qualification_policy.yaml` : qualification ;
- `agents/*` : contrats humains des rôles ;
- `config/v1/runtime_versions.json` : versions runtime.

Les contrats Git décrivent l'état attendu. Les performances GPU, la qualité multimodale et la stabilité sont des **états observés** qui doivent être prouvés sur la workstation réelle.

## Invariants V1

- Windows natif pour le runtime IA nominal ;
- exactement trois modèles locaux supportés ;
- aucun fallback cloud silencieux ;
- projet central source de vérité ;
- workspaces jetables ;
- provenance et historique conservés ;
- gates fail-closed ;
- séparation producteur/reviewer lorsque praticable ;
- sécurité et audit sans correction silencieuse ;
- cloud désactivé par défaut ;
- approbation humaine pour `COMPLETE` ;
- aucune affirmation de performance sans preuve matérielle.
