# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` est une plateforme IA **local-first, multi-agents et project-first** pour Windows 11 Pro x64. Le runtime IA nominal reste natif Windows ; WSL2 peut héberger des outils DevOps/Linux mais n'est pas le runtime LLM nominal.

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
Windows 11 Pro x64
|
+-- Control plane clawlocal
|    +-- contrats YAML/JSON
|    +-- Project Intake / Ingestion
|    +-- Project Orchestrator
|    +-- Artifact Exchange
|    +-- Workspace Guard
|    +-- preuves / télémétrie / release gates
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
|    +-- qwen-max        -> qwen3.5:9b-q4_K_M
|    +-- gemma-deep      -> gemma3:12b-it-q4_K_M
|    +-- devstral-devops -> qwen2.5-coder:14b-instruct-q4_K_M
|
+-- Backends
     +-- ollama-vulkan
     +-- llama-cpp-sycl
     +-- llama-cpp-vulkan
     +-- profil candidat b580-hybrid
```

Les trois runtimes sont quantifiés **Q4_K_M** et ciblent un contexte nominal de **8192 tokens**. Le 16384 reste un contexte de qualification.

## Modèles et rôles

### `qwen-max`

`qwen3.5:9b-q4_K_M` couvre :

- orchestration ;
- recherche avec outils Web ;
- sécurité ;
- release/forges ;
- raisonnement transversal ;
- multimodalité nominale PDF/image.

### `gemma-deep`

`gemma3:12b-it-q4_K_M` couvre :

- architecture ;
- rédaction ;
- audit ;
- contre-revue ;
- multimodalité locale alternative.

### `devstral-devops`

L'alias historique est conservé pour ne pas casser les contrats persistés, mais il pointe désormais vers `qwen2.5-coder:14b-instruct-q4_K_M`.

Ce spécialiste couvre :

- DevOps ;
- software engineering ;
- scripts ;
- CI/CD ;
- Kubernetes/IaC ;
- outils dépôt et édition multi-fichiers.

Il est text-only dans le contrat. Pour un PDF ou une image, Qwen/Gemma produisent un contexte traçable puis l'Artifact Exchange effectue le handoff au spécialiste.

## Routage par rôle

```text
chef-operations          -> qwen-max
expert-recherche         -> qwen-max
architecte-solutions     -> gemma-deep
ingenieur-devops         -> devstral-devops
ingenieur-securite       -> qwen-max
ingenieur-release-forges -> qwen-max
redacteur-technique      -> gemma-deep
auditeur-qualite         -> gemma-deep
```

L'Auditeur peut basculer vers `qwen-max` lorsque le producteur est Gemma afin de préserver une séparation de famille lorsque cela est praticable.

## Modèle et backend sont indépendants

Le choix d'un modèle ne vaut pas sélection définitive du backend. Les candidats sont évalués séparément :

```text
ollama-vulkan
llama-cpp-sycl
llama-cpp-vulkan
b580-hybrid
```

Le profil candidat hybride encode actuellement :

```text
qwen-max        -> Ollama/Vulkan
gemma-deep      -> llama.cpp/Vulkan
devstral-devops -> llama.cpp/Vulkan
```

Cette configuration est un **candidat de qualification**, pas un backend promu. Toute promotion exige des mesures B580, E2E, tool-calling, stabilité et revue humaine.

## Contexte et mémoire

La B580 dispose de 12 Go de VRAM. L'architecture évite donc d'utiliser la fenêtre maximale théorique des modèles comme réglage opérationnel.

Politique :

```text
8192  -> nominal
16384 -> qualification/stress
>16K  -> interdit comme nominal sans nouvelle preuve
```

Les preuves recherchées sont : `size_vram`, VRAM/RAM, TTFT, tokens/s, temps de chargement, stabilité et tool-calling.

## Projet central et workspaces

Le projet central reste source de vérité :

```text
projects/<project-id>/
├── intake/
├── sources/
├── context/
├── work/
├── deliverables/
├── evidence/
└── diagrams/
```

Les workspaces agents sont des vues contrôlées. Le Workspace Guard applique les scopes de lecture/écriture et les frontières gérées refusent symlinks, junctions et reparse points.

## Project Intake et Document Ingestion

Le parcours document :

```text
entrée non fiable
 -> validation sécurité
 -> archive/source canonique
 -> SHA-256 + MIME
 -> extraction/indexation locale
 -> source_coverage
 -> analyse agent
```

PDF/images passent par les modèles multimodaux Qwen/Gemma. DOCX/PPTX/XLSX utilisent l'extraction locale déterministe. Les originaux restent immuables.

## Project Orchestrator

Machine principale :

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

Chaque phase exige ses artefacts et preuves. Une ambiguïté bloquante provoque une clarification humaine ; elle n'est jamais inventée par le modèle.

## Artifact Exchange

Les sorties valides sont versionnées, hashées et propagées uniquement après PASS. Les sorties en échec restent dans l'historique mais ne deviennent pas des dépendances valides.

La chaîne de traçabilité reste :

```text
REQ -> tâche -> sortie -> preuve -> verdict
```

## Local-first et cloud

Le parcours nominal ne nécessite aucun LLM cloud. Le Web peut être interrogé via les outils locaux OpenClaw, puis raisonné par les modèles locaux.

Une escalade OpenRouter exige :

- motif autorisé ;
- activation explicite ;
- budget FinOps disponible ;
- préconditions de politique ;
- journalisation ;
- approbation humaine lorsque requise.

Aucun fallback cloud silencieux n'est accepté.

## V1

La conformité logicielle de cette architecture peut être prouvée par CI. En revanche, la qualification V1 reste strictement matérielle et humaine : HARD-40M, E2E, backends, Golden Projects, multimodalité, télémétrie, projet représentatif et attestation SHA-256 doivent tous être validés avant `1.0.0`.
