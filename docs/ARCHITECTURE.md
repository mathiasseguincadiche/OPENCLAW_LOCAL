# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` est une plateforme IA **LLM local-only, multi-agents et project-first** pour Windows 11 Pro x64. Le runtime IA nominal reste natif Windows ; WSL2 peut héberger des outils DevOps/Linux mais n'est pas le runtime LLM nominal.

Architecture V2 sépare explicitement :

- le **control plane déterministe** `clawlocal` ;
- les **huit rôles OpenClaw** ;
- la **flotte locale fermée de trois modèles routés** ;
- le **challenger local de benchmark**, hors routage ;
- les **backends d'inférence locaux** ;
- le **projet central**, source de vérité ;
- les **workspaces agents**, vues contrôlées ;
- les **outils Web**, qui apportent de l'information sans devenir un backend LLM.

Il n'existe **aucune route vers un modèle LLM cloud**. Toute demande de routage cloud est refusée fail-closed.

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
+-- Flotte locale routée — exactement 3 modèles
|    +-- qwen-max        -> qwen3.5:9b-q4_K_M
|    +-- gemma-deep      -> gemma4:12b-it-q4_K_M
|    +-- devstral-devops -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
|
+-- Challenger local hors routage
|    +-- granite-devops  -> granite4.2:8b-q4_K_M
|
+-- Backends locaux
     +-- ollama-vulkan
     +-- llama-cpp-sycl
     +-- llama-cpp-vulkan
     +-- profil candidat b580-hybrid
```

Les modèles opérationnels sont quantifiés **Q4_K_M**. Le challenger Granite est également Q4_K_M, mais n'est jamais compté comme quatrième modèle routé.

## Modèles et rôles

### `qwen-max`

`qwen3.5:9b-q4_K_M` couvre :

- orchestration ;
- recherche avec outils Web ;
- sécurité ;
- release/forges ;
- raisonnement transversal ;
- multimodalité locale PDF/image.

### `gemma-deep`

`gemma4:12b-it-q4_K_M` couvre :

- architecture ;
- rédaction ;
- audit ;
- contre-revue ;
- multimodalité locale alternative.

### `devstral-devops`

L'alias historique est conservé afin de ne pas casser les contrats persistés. En Architecture V2 il pointe vers :

```text
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Ce spécialiste couvre :

- DevOps ;
- software engineering ;
- scripts ;
- CI/CD ;
- conteneurs ;
- Kubernetes/IaC ;
- outils dépôt et édition multi-fichiers ;
- tool-calling et réparation après retour d'outil.

Il est text-only dans le contrat nominal. Pour un PDF ou une image, Qwen 3.5 ou Gemma 4 produit un contexte traçable puis l'Artifact Exchange effectue le handoff au spécialiste.

### `granite-devops`

`granite4.2:8b-q4_K_M` est un challenger local consacré au benchmark DevOps/tool-calling. Il possède `routing_active: false` et `automatic_promotion: false`. Une éventuelle promotion exige une décision humaine après preuves matérielles B580.

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

L'Auditeur peut basculer vers `qwen-max` lorsque le producteur est `gemma-deep` afin de préserver une séparation de famille lorsque cela est praticable.

Les fallbacks du contrat sont **uniquement locaux** et restent dans l'ensemble `{qwen-max, gemma-deep, devstral-devops}`.

## Web != LLM cloud

L'Expert recherche peut utiliser des outils Web pour récupérer des sources publiques fraîches. Ces outils ne sont pas un fournisseur de modèle : le contenu récupéré est traité et raisonné par la flotte locale. Cette séparation permet de conserver l'accès à l'information Internet sans introduire d'inférence LLM cloud.

## Modèle et backend sont indépendants

Le choix d'un modèle ne vaut pas sélection définitive du backend. Les candidats locaux sont évalués séparément :

```text
ollama-vulkan
llama-cpp-sycl
llama-cpp-vulkan
b580-hybrid
```

Le profil candidat hybride peut répartir les trois modèles entre Ollama/Vulkan et llama.cpp/Vulkan selon les contrats runtime. Cette configuration reste un **candidat de qualification**, jamais un backend promu par simple configuration.

Toute promotion exige des mesures B580, E2E, tool-calling, stabilité et revue humaine.

## Contexte et mémoire

La B580 dispose de 12 Go de VRAM. Architecture V2 n'utilise donc pas les fenêtres maximales théoriques comme réglage opérationnel par défaut.

Deux contrats sont séparés :

```text
8192  -> benchmark nominal / HARD-40M
16384 -> orchestration OpenClaw nominale
>16K  -> non promu sans qualification dédiée
```

Le contexte OpenClaw 16384 sert à absorber système, outils et réserve de l'orchestrateur. Il ne constitue pas une promotion du benchmark. **Aucune promotion automatique à 32768 n'est autorisée.**

Les preuves recherchées restent : `size_vram`, VRAM/RAM, TTFT, tokens/s, temps de chargement, stabilité, contexte et tool-calling.

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
 -> analyse agent local
```

PDF/images passent par les modèles multimodaux locaux Qwen/Gemma. DOCX/PPTX/XLSX utilisent l'extraction locale déterministe. Les originaux restent immuables.

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

## Politique local-only

Architecture V2 impose :

```text
local_first: true
local_only: true
cloud_models_supported: false
```

Le catalogue ne contient aucun catalogue de modèles cloud. Le routeur refuse une demande `request_cloud`. Les variables de configuration nominales ne contiennent aucune clé de fournisseur LLM en ligne.

Cette règle ne signifie pas « machine hors ligne » : bootstrap, téléchargement de modèles et outils Web peuvent utiliser Internet lorsqu'ils sont explicitement nécessaires. Elle signifie que **l'inférence et le raisonnement LLM de la plateforme restent locaux**.

## V1

La conformité logicielle de cette architecture peut être prouvée par CI. La qualification V1 reste cependant matérielle et humaine : HARD-40M, E2E, backends, Golden Projects, multimodalité, télémétrie, projet représentatif et attestation SHA-256 doivent tous être validés avant `1.0.0`.
