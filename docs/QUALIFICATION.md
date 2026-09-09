# Qualification de la workstation

## But

La qualification transforme les contrats Git en décisions fondées sur des **preuves réelles** produites sur Windows 11 + Intel Arc B580. GitHub Actions valide les contrats logiciels ; elle ne fabrique jamais une qualification matérielle.

Architecture V2 est **LLM local-only** et **Vulkan-only côté accélération GPU LLM B580**. Le choix de l'API GPU est déjà arrêté et n'est pas re-benchmarké pendant la qualification.

## Flotte opérationnelle — exactement trois modèles

| Alias logique | Runtime | Quantification | Rôle principal |
|---|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | Q4_K_M | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma4:12b-it-q4_K_M` | Q4_K_M | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M` | Q4_K_M | DevOps, code, outils dépôt, tool-calling |

Les trois modèles sont `required: true` et constituent l'intégralité du routage nominal. L'alias `devstral-devops` reste un alias logique de compatibilité ; son runtime V2 est Ministral 3 14B Reasoning et reste text-only dans le contrat nominal.

## Challenger local du spécialiste DevOps

La sélection du **modèle spécialiste** peut être confrontée à :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite est un challenger de modèle, pas un quatrième modèle routé, pas un fallback et pas un candidat de backend. Il reste `routing_active: false` et ne peut pas être promu automatiquement.

## Invariants

- aucun appel LLM cloud pendant la qualification ;
- Vulkan est l'unique accélération GPU LLM supportée sur la B580 ;
- aucune re-comparaison d'API GPU ;
- aucun téléchargement implicite pendant les tests de qualification ;
- exactement trois modèles routés dans le HARD-40M ;
- Granite est évalué séparément comme challenger de modèle ;
- quantification attendue Q4_K_M ;
- contexte qualification nominal : **8192 tokens** ;
- contexte HARD-40M 16384 : stress ciblé ;
- contexte OpenClaw full-agent nominal : **16384 tokens**, contrat distinct ;
- aucune promotion automatique à 32768 ;
- aucun seuil modifié pour fabriquer un PASS ;
- aucune promotion automatique de modèle, profil runtime, catalogue ou V1 ;
- preuves brutes conservées hors Git ;
- toute dérive modèle/runtime/pilote invalide la réutilisation automatique d'une preuve ;
- HARD-40M complet : **2400 s maximum**.

## 1. Installation

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

## 2. Vérification du runtime nominal Vulkan

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le contrôle doit confirmer la B580, les versions verrouillées, Ollama sur loopback et la présence exacte des trois modèles. Les métriques de résidence GPU, débit et contexte réellement alloué sont des observations ; elles ne changent pas la décision backend.

## 3. Gate OpenClaw E2E nominal

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
6. aucune dépendance LLM cloud nominale ;
7. aucun fallback silencieux de provider ou de transport.

## 4. HARD-40M des trois modèles routés

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le launcher utilise `benchmark_qualification_40m_v2.py`.

La matrice contient **30 cas** :

- 24 cas à 8192 tokens ;
- 6 cas à 16384 tokens ;
- exactement trois modèles requis ;
- scénarios définis par `devops-v2` et `qualification_policy.yaml`.

Granite **n'entre pas dans ces 30 cas**. Il ne peut pas remplacer un échec d'un modèle routé.

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

## 5. Profil B580 hybride Vulkan

Le runtime géré llama.cpp/Vulkan est validé avec :

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

Puis le profil hybride :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Ce contrôle ne compare pas Vulkan à une autre API. Il prouve que la répartition retenue fonctionne :

```text
qwen-max        -> Ollama/Vulkan
gemma-deep      -> llama.cpp/Vulkan
devstral-devops -> llama.cpp/Vulkan
image/PDF       -> Ollama/Vulkan
```

Le gate hybride doit confirmer le provider réellement utilisé agent par agent, le tool-calling Ministral/Vulkan, la réparation après erreur et trois runs stables.

## 6. Comparaison Ministral 3 Reasoning vs Granite 4.2

Cette étape concerne uniquement le **choix du modèle spécialiste DevOps**.

Installation explicite du challenger :

```powershell
ollama pull granite4.2:8b-q4_K_M
```

Dry-run puis mesure réelle :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Contrat :

```text
incumbent   : devstral-devops / Ministral 3 14B Reasoning
challenger  : granite-devops / Granite 4.2 8B
contexte    : 8192
répétitions : 3
protocole   : native_tool_calling_v1
```

Les métriques contractuelles incluent tool intent, réparation, erreurs de protocole, durée, débit et résidence GPU lorsque mesurable.

Même si Granite domine, aucun fichier de routage n'est modifié automatiquement. La décision finale reste humaine.

## 7. Identité exacte des modèles

Avant le HARD-40M, la qualification capture l'identité des trois runtimes routés dans :

```text
state/qualification/candidate_model_identity.json
```

Après un gate complet PASS, cette identité peut être promue vers :

```text
state/qualification/qualified_model_identity.json
```

Cette promotion n'est autorisée qu'après un gate complet PASS. Une dérive d'identité, digest, quantification ou verrou runtime/pilote doit invalider l'état et exiger une nouvelle qualification complète.

Le mode `-Quick` ne promeut jamais l'identité modèle.

## 8. Diagnostic Quick

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Quick est un diagnostic. Il ne remplace ni HARD-40M, ni E2E, ni les preuves matérielles réelles.

## 9. Golden Projects et projet représentatif

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

Les Golden Projects complètent la qualification mais ne remplacent pas un projet réel de `INTAKE_READY` à `COMPLETE` avec revue humaine, multimodalité réelle, Artifact Exchange, télémétrie et package final.

## 10. Redémarrage, récupération et endurance

Avant un GO usage quotidien, vérifier aussi sur la workstation réelle :

- redémarrage Windows ;
- redémarrage Ollama/OpenClaw ;
- récupération du runtime llama.cpp/Vulkan géré ;
- absence de port orphelin ;
- rollback vers `ollama-vulkan` ;
- reprise d'un projet existant ;
- plusieurs cycles d'agents et changements de modèle ;
- stabilité mémoire et absence de fuite évidente ;
- conservation correcte des preuves/logs.

## Verdicts

### `NOT_READY`

Au moins un gate échoue. Conserver la preuve et corriger la cause ; ne pas abaisser le protocole.

### `HARD_TIMEOUT`

Le HARD-40M ne termine pas sous 2400 s : échec du protocole pour cette configuration.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques passent. Restent les validations matérielles finales, Golden Projects, projet représentatif et revue humaine.

### `MEASURED_FOR_MANUAL_SELECTION`

La comparaison Ministral/Granite est complète. Ce verdict signifie uniquement que les preuves nécessaires à une décision humaine sur le **modèle spécialiste** sont disponibles.

## Preuves V1 minimales

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU et inventaire matériel ;
- identité/digest/quantification des trois modèles routés ;
- preuve HARD-40M ;
- preuve OpenClaw E2E nominal ;
- preuve runtime llama.cpp/Vulkan et E2E hybride si ce profil est retenu pour l'usage ;
- preuve Ministral/Granite si la décision de modèle reste ouverte ;
- Golden Projects ;
- multimodalité réelle ;
- télémétrie réelle ;
- package du projet représentatif ;
- redémarrage/récupération/endurance ;
- limites observées ;
- approbation humaine.

Les SHA-256 des preuves alimentent `config/v1/release_readiness.yaml`. V1 reste bloquée tant que les preuves matérielles réelles et l'approbation humaine ne sont pas complètes.
