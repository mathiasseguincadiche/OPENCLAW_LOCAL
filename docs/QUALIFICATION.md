# Qualification de la workstation

## But

La qualification transforme les choix déclarés dans Git en décisions fondées sur des **preuves réelles** produites sur Windows 11 + Intel Arc B580. GitHub Actions valide les contrats logiciels ; elle ne fabrique jamais une qualification matérielle.

## Flotte opérationnelle candidate — exactement trois modèles

| Alias logique | Runtime | Quantification | Rôle principal |
|---|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | Q4_K_M | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | Q4_K_M | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | Q4_K_M | DevOps, code, outils dépôt |

Les trois modèles sont `required: true` et constituent l'intégralité du routage nominal. L'alias `devstral-devops` reste un alias logique de compatibilité ; son runtime est Qwen2.5 Coder 14B et reste text-only dans le contrat.

## Challenger obligatoire du modèle deep

`gemma-deep` est l'incumbent deep mais sa sélection définitive doit être confrontée à :

```text
ministral-tool-calling -> ministral-3:14b-instruct-2512-q4_K_M
```

Ministral est un **challenger de benchmark**, pas un quatrième modèle routé. Il reste `routing_active: false`, ne sert jamais de fallback silencieux et ne peut pas être promu automatiquement.

La comparaison est obligatoire avant une décision humaine finale sur le modèle deep. Elle cible en particulier :

- tool-calling natif ;
- réparation après erreur d'outil ;
- erreurs de protocole ;
- latence ;
- débit ;
- adéquation VRAM B580.

## Invariants

- aucun appel LLM cloud pendant la qualification ;
- aucun téléchargement implicite pendant les benchmarks ;
- exactement trois modèles routés dans le HARD-40M ;
- Ministral est évalué séparément comme challenger obligatoire ;
- quantification attendue Q4_K_M ;
- contexte nominal opérationnel : **8192 tokens** ;
- contexte 16384 : stress HARD-40M, jamais promotion nominale implicite ;
- aucun seuil modifié pour fabriquer un PASS ;
- aucune promotion automatique de modèle, backend, catalogue ou V1 ;
- toute décision Gemma/Ministral est humaine et fondée sur preuve ;
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

Ce parcours installe les trois modèles routés du catalogue. Le challenger Ministral n'est pas téléchargé automatiquement.

## 2. Installation explicite du challenger

Uniquement pour la comparaison de sélection :

```powershell
ollama pull ministral-3:14b-instruct-2512-q4_K_M
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
6. aucune dépendance cloud nominale.

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

Ministral **n'entre pas dans ces 30 cas**. Le challenger est une preuve de sélection distincte et ne peut pas remplacer un échec de Gemma, Qwen ou Qwen Coder dans le gate principal.

### Qwen reasoning

Trois probes Qwen gardent le thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond HARD-40M reste **1024 tokens**. Atteindre cette borne reste une troncature et un échec.

### Budget temps

```text
qualification complète : 2400 s maximum
réserve évaluation      :   60 s
benchmark direct        : 2100 s par défaut
cas individuel          :  210 s maximum
```

Un timeout, une erreur API ou une sortie tronquée avec `max_error_rate: 0.0` ne sont jamais convertis en PASS.

## 6. Comparaison obligatoire Gemma 3 12B vs Ministral 3 14B

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
incumbent   : gemma-deep / gemma3:12b-it-q4_K_M
challenger  : ministral-tool-calling / ministral-3:14b-instruct-2512-q4_K_M
contexte    : 8192
répétitions : 3
protocole   : native_tool_calling_v1
```

Chaque répétition demande au modèle d'utiliser un outil natif `read_file` sur `config/prod.yaml`. Le runner renvoie ensuite une erreur contrôlée `file_not_found`; le modèle doit se réparer en appelant `list_files` sur `config`.

Le runner mesure :

- `tool_intent_pass_rate` ;
- `tool_repair_pass_rate` ;
- erreurs de protocole ;
- durée murale ;
- tokens/s lorsque fournis ;
- taille et résidence VRAM via `/api/ps` lorsque disponibles.

Le contenu brut des réponses n'est pas persisté ; une empreinte SHA-256 et les appels d'outils structurés sont conservés pour l'audit.

Preuve :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Une comparaison complète produit au maximum :

```text
VERDICT=MEASURED_FOR_MANUAL_SELECTION
PROMOTION_ALLOWED=false
MANUAL_DECISION_REQUIRED=true
```

Même si Ministral domine les trois répétitions, aucun fichier de routage n'est modifié automatiquement.

## 7. Identité exacte des modèles

Avant le HARD-40M, la qualification capture l'identité des trois runtimes routés dans :

```text
state/qualification/candidate_model_identity.json
```

Après un gate complet PASS, cette identité peut être promue vers :

```text
state/qualification/qualified_model_identity.json
```

Cette promotion d'identité ne vaut ni sélection définitive du modèle deep, ni promotion de backend, ni approbation V1.

Le mode `-Quick` ne promeut jamais l'identité modèle.

## 8. Diagnostic Quick

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Quick conserve 36 cas à 8192 tokens avec thinking Qwen désactivé. Il ne remplace ni HARD-40M ni la comparaison Gemma/Ministral.

## 9. Comparaison des backends

Backends candidats :

- `ollama-vulkan` ;
- `llama-cpp-sycl` ;
- `llama-cpp-vulkan` ;
- profil `b580-hybrid`.

Comparer autant que possible même modèle, même quantification, même contexte et mêmes prompts. Aucun backend n'est auto-promu.

La comparaison de **modèles** Gemma/Ministral et la comparaison de **backends** sont deux décisions distinctes.

## 10. Golden Projects et projet représentatif

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

Les cinq Golden Projects complètent les benchmarks mais ne remplacent pas un projet réel de `INTAKE_READY` à `COMPLETE` avec revue humaine, multimodalité réelle, Artifact Exchange, télémétrie et package final.

## Verdicts

### `NOT_READY`

Au moins un gate échoue. Conserver la preuve et corriger la cause ; ne pas abaisser le protocole.

### `HARD_TIMEOUT`

Le HARD-40M ne termine pas sous 2400 s : échec du protocole pour cette configuration.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques passent. Restent la revue humaine, les backends, la multimodalité, les Golden Projects, le projet représentatif et la décision Gemma/Ministral.

### `MEASURED_FOR_MANUAL_SELECTION`

La comparaison Gemma/Ministral est complète. Ce verdict signifie uniquement que les preuves nécessaires à une décision humaine sont disponibles.

## Preuves V1 minimales

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU et inventaire matériel ;
- identité/digest/quantification des trois modèles routés ;
- preuve HARD-40M ;
- preuve OpenClaw E2E ;
- **preuve Gemma/Ministral de sélection** ;
- comparaison backend ;
- Golden Projects ;
- multimodalité réelle ;
- télémétrie réelle ;
- package du projet représentatif ;
- limites observées ;
- approbation humaine.

Les SHA-256 des preuves alimentent `config/v1/release_readiness.yaml`. V1 reste bloquée tant que les preuves matérielles réelles et l'approbation humaine ne sont pas complètes.
