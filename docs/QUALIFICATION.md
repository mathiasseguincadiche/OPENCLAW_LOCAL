# Qualification de la workstation

## But

La qualification transforme les choix déclarés dans Git en décisions fondées sur des **preuves réelles** produites sur Windows 11 + Intel Arc B580. GitHub Actions valide les contrats logiciels ; elle ne fabrique jamais une qualification matérielle.

Architecture V2 est **LLM local-only**. Aucun modèle LLM cloud n'est autorisé pendant la qualification ni comme fallback.

## Flotte opérationnelle candidate — exactement trois modèles

| Alias logique | Runtime | Quantification | Rôle principal |
|---|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | Q4_K_M | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma4:12b-it-q4_K_M` | Q4_K_M | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M` | Q4_K_M | DevOps, code, outils dépôt, tool-calling |

Les trois modèles sont `required: true` et constituent l'intégralité du routage nominal. L'alias `devstral-devops` reste un alias logique de compatibilité ; son runtime V2 est Ministral 3 14B Reasoning et reste text-only dans le contrat nominal.

## Challenger local du spécialiste DevOps

La sélection du spécialiste doit être confrontée à :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite est un **challenger de benchmark**, pas un quatrième modèle routé. Il reste `routing_active: false`, ne sert jamais de fallback et ne peut pas être promu automatiquement.

La comparaison est obligatoire avant une décision humaine finale sur le spécialiste DevOps. Elle cible notamment :

- coding ;
- tool-calling natif ;
- réparation après erreur d'outil ;
- erreurs de protocole ;
- latence et débit ;
- adéquation VRAM B580.

## Invariants

- aucun appel LLM cloud pendant la qualification ;
- aucun téléchargement implicite pendant les benchmarks ;
- exactement trois modèles routés dans le HARD-40M ;
- Granite est évalué séparément comme challenger local ;
- quantification attendue Q4_K_M ;
- contexte benchmark nominal : **8192 tokens** ;
- contexte HARD-40M 16384 : stress ciblé ;
- contexte OpenClaw full-agent nominal : **16384 tokens**, contrat distinct du benchmark ;
- aucune promotion automatique à 32768 ;
- aucun seuil modifié pour fabriquer un PASS ;
- aucune promotion automatique de modèle, backend, catalogue ou V1 ;
- toute décision Ministral/Granite est humaine et fondée sur preuve ;
- preuves brutes conservées hors Git ;
- toute dérive modèle/backend/runtime/pilote invalide la réutilisation automatique d'une preuve ;
- HARD-40M complet : **2400 s maximum**.

## 1. Installation de la flotte routée

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Pour une workstation déjà installée :

```powershell
.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
```

Ce parcours installe les trois modèles routés du catalogue. Granite n'est pas téléchargé automatiquement.

## 2. Installation explicite du challenger

Uniquement pour la comparaison de sélection :

```powershell
ollama pull granite4.2:8b-q4_K_M
```

Sa présence locale ne modifie ni OpenClaw ni le routage.

## 3. Vérification du runtime

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le smoke Ollama vérifie la disponibilité et l'identité runtime. `/api/ps` expose lorsque disponible taille chargée, `size_vram` et contexte réellement alloué. Une résidence GPU complète n'est jamais supposée sans mesure.

Sous Windows, les chemins sensibles utilisent le runtime Python géré OPENCLAW_LOCAL.

## 4. Gate OpenClaw E2E

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le gate doit prouver notamment :

1. les huit agents via le Gateway ;
2. le routage local attendu ;
3. un vrai appel d'outil avec le spécialiste DevOps ;
4. une erreur d'outil contrôlée suivie d'une réparation ;
5. trois exécutions stables ;
6. aucune dépendance LLM cloud nominale.

## 5. HARD-40M des trois modèles routés

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le launcher utilise `benchmark_qualification_40m_v2.py`.

La matrice contient **30 cas** :

- 24 cas à 8192 tokens ;
- 6 cas à 16384 tokens ;
- exactement trois modèles requis ;
- les scénarios sont définis par `devops-v2` et `qualification_policy.yaml`.

Granite **n'entre pas dans ces 30 cas**. Le challenger est une preuve de sélection distincte et ne peut pas remplacer un échec d'un modèle de la flotte active dans le gate principal.

### Qwen reasoning

Trois probes Qwen gardent le thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond HARD-40M reste **1024 tokens**. Atteindre cette borne reste une troncature et un échec.

### Seuils et budget temps

```text
max_error_rate               : 0.0
min_check_pass_rate          : 0.875
min_median_tokens_per_second : 6.0
max_p95_first_token_ms       : 12000
8K min check pass rate       : 0.875
16K min check pass rate      : 0.75

qualification complète : 2400 s maximum
réserve évaluation      :   60 s
benchmark direct        : 2100 s par défaut
cas individuel          :  210 s maximum
```

Un timeout, une erreur API ou une sortie tronquée ne sont jamais convertis en PASS.

## 6. Comparaison Ministral 3 Reasoning vs Granite 4.2

Le protocole de sélection est séparé du HARD-40M afin de ne pas transformer le challenger en quatrième modèle opérationnel.

Dry-run :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
```

Mesure réelle :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1
```

Contrat par défaut :

```text
incumbent   : devstral-devops / Ministral 3 14B Reasoning
challenger  : granite-devops / Granite 4.2 8B
contexte    : 8192
répétitions : 3
protocole   : native_tool_calling_v1
```

Chaque répétition exerce le protocole d'outils natif puis une réparation après erreur contrôlée. Les métriques contractuelles incluent :

- `tool_intent_pass_rate` ;
- `tool_repair_pass_rate` ;
- `protocol_error_count` ;
- `median_wall_ms` ;
- `median_tokens_per_second` ;
- `median_gpu_residency_ratio` lorsque mesurable.

Le contenu brut des réponses n'a pas besoin d'être persisté. Les preuves structurées doivent suffire pour l'audit et la décision humaine.

Preuve :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Le contrat impose :

```text
automatic_promotion: false
human_decision_required: true
evidence_required: true
```

Même si Granite domine les répétitions, aucun fichier de routage n'est modifié automatiquement.

## 7. Identité exacte des modèles

Avant le HARD-40M, la qualification capture l'identité des trois runtimes routés dans :

```text
state/qualification/candidate_model_identity.json
```

Après un gate complet PASS, cette identité peut être promue vers :

```text
state/qualification/qualified_model_identity.json
```

La promotion de cette identité est autorisée **uniquement après un gate complet PASS**. Si l'identité exacte, le digest, la quantification ou un autre verrou matériel/runtime dérive ensuite, `verify` doit considérer l'état comme `INVALIDATED` et exiger une nouvelle qualification complète.

Cette opération n'entraîne aucune promotion automatique de backend, de challenger ou de V1. Le mode `-Quick` ne promeut jamais l'identité modèle.

## 8. Diagnostic Quick

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Quick est un diagnostic et ne remplace ni HARD-40M ni la comparaison Ministral/Granite.

## 9. Comparaison des backends

Backends locaux candidats :

- `ollama-vulkan` ;
- `llama-cpp-sycl` ;
- `llama-cpp-vulkan` ;
- profil `b580-hybrid`.

Comparer autant que possible même modèle, même quantification, même contexte et mêmes prompts. Aucun backend n'est auto-promu.

La comparaison de **modèles** Ministral/Granite et la comparaison de **backends** sont deux décisions distinctes.

## 10. Golden Projects et projet représentatif

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

Les Golden Projects complètent les benchmarks mais ne remplacent pas un projet réel de `INTAKE_READY` à `COMPLETE` avec revue humaine, multimodalité réelle, Artifact Exchange, télémétrie et package final.

## Verdicts

### `NOT_READY`

Au moins un gate échoue. Conserver la preuve et corriger la cause ; ne pas abaisser le protocole.

### `HARD_TIMEOUT`

Le HARD-40M ne termine pas sous 2400 s : échec du protocole pour cette configuration.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques passent. Restent la revue humaine, les backends, la multimodalité, les Golden Projects, le projet représentatif et la décision Ministral/Granite.

### `MEASURED_FOR_MANUAL_SELECTION`

La comparaison Ministral/Granite est complète. Ce verdict signifie uniquement que les preuves nécessaires à une décision humaine sont disponibles.

## Preuves V1 minimales

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU et inventaire matériel ;
- identité/digest/quantification des trois modèles routés ;
- preuve HARD-40M ;
- preuve OpenClaw E2E ;
- preuve Ministral/Granite de sélection ;
- comparaison backend ;
- Golden Projects ;
- multimodalité réelle ;
- télémétrie réelle ;
- package du projet représentatif ;
- limites observées ;
- approbation humaine.

Les SHA-256 des preuves alimentent `config/v1/release_readiness.yaml`. V1 reste bloquée tant que les preuves matérielles réelles et l'approbation humaine ne sont pas complètes.
