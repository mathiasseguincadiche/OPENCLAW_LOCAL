# Benchmark local

## Objectif

Mesurer ce qui reste utile pour l'usage réel. Le benchmark/qualification sépare :

1. **fonctionnel** : requêtes et contrôles conformes ;
2. **performance observée** : premier token, débit et durée murale ;
3. **contexte** : nominal 8K puis stress ciblé 16K ;
4. **projet/DevOps** : tâches proches de l'usage réel ;
5. **agentique** : tool-calling et réparation ;
6. **sélection du spécialiste** : incumbent Ministral vs challenger Granite.

Le choix d'accélération GPU B580 n'est plus une dimension de benchmark : **Vulkan est verrouillé par Architecture V2**. Les mesures de débit, VRAM/RAM ou chargement servent uniquement à caractériser la voie Vulkan choisie.

Architecture V2 n'autorise aucun appel vers un modèle LLM cloud pendant la qualification.

## Flotte opérationnelle testée

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

`devstral-devops` est un alias logique de compatibilité ; son runtime V2 réel est Ministral 3 14B Reasoning.

## Challenger local du spécialiste DevOps

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite :

- n'est pas un quatrième modèle routé ;
- n'est pas un fallback ;
- n'entre pas dans les 30 cas HARD-40M de la flotte opérationnelle ;
- ne peut jamais être auto-promu ;
- ne remplace Ministral qu'après preuve et décision humaine explicite.

Cette comparaison concerne le **modèle spécialiste**, pas l'API GPU.

## Contextes : qualification != OpenClaw

```text
8192  -> contexte nominal HARD-40M
16384 -> stress ciblé HARD-40M
```

OpenClaw full-agent utilise séparément 16384 tokens comme fenêtre nominale d'orchestration. Cette valeur ne promeut pas automatiquement le benchmark à 16K/32K.

Les tailles de fichiers/registre ne prouvent pas la résidence complète en VRAM. `size_vram`, TTFT, débit, RAM et stabilité doivent être observés sur la B580 réelle.

## Suite active `devops-v2`

La suite `benchmarks/suites/devops_v2.yaml` fournit les scénarios fonctionnels. `config/v1/qualification_policy.yaml` possède la matrice HARD-40M, les seuils et le contrat challenger.

Runner :

```text
scripts/benchmark_qualification_40m_v2.py
```

Plan contractuel :

```text
24 cas 8K
 6 cas 16K
30 cas total
```

Les trois modèles routés restent obligatoires.

## Qwen thinking natif

La passe complète conserve trois probes Qwen avec thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond est **1024 tokens**. Une génération qui atteint la borne est classée tronquée et fait échouer le gate. Le mode Quick désactive le thinking Qwen pour fournir un diagnostic plus court.

## HARD-40M

```text
qualification complète : 2400 s
réserve évaluation      :   60 s
benchmark par défaut    : 2100 s
cas individuel          :  210 s
```

Le runner ne prolonge pas silencieusement un cas. Une erreur API, un timeout ou une troncature avec `max_error_rate: 0.0` déclenche un échec conformément au protocole.

## Seuils actifs

```text
max_error_rate                    = 0.0
min_check_pass_rate               = 0.875
min_median_tokens_per_second      = 6.0
max_p95_first_token_ms            = 12000
8K min check pass rate            = 0.875
16K min check pass rate           = 0.75
```

Architecture V2 n'abaisse aucun seuil.

## Métriques utiles

Pour chaque cas, conserver autant que possible :

- `wall_ms` ;
- premier token réellement généré ;
- délai jusqu'à la réponse finale ;
- `tokens_per_second` ;
- nombre de tokens de sortie ;
- volume de thinking sans contenu brut ;
- statut des checks ;
- runtime Vulkan réellement utilisé ;
- contexte ;
- identité exacte du modèle ;
- VRAM/RAM/offload lorsque disponibles.

Les valeurs inconnues restent inconnues. Une mesure de performance ne peut pas rebasculer automatiquement le projet vers une autre API GPU.

## Comparaison Ministral 3 Reasoning vs Granite 4.2

### Installation du challenger

```powershell
ollama pull granite4.2:8b-q4_K_M
```

### Dry-run

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
```

### Mesure réelle

```powershell
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

La comparaison teste le protocole d'outils natif, y compris une réparation après retour d'outil en erreur contrôlée.

Métriques contractuelles :

- `tool_intent_pass_rate` ;
- `tool_repair_pass_rate` ;
- `protocol_error_count` ;
- `median_wall_ms` ;
- `median_tokens_per_second` ;
- `median_gpu_residency_ratio` lorsque mesurable.

Le contenu brut des réponses n'a pas besoin d'être persisté. Les preuves structurées doivent suffire pour l'audit et la décision humaine.

Fichier attendu :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Le contrat impose :

```text
automatic_promotion: false
human_decision_required: true
evidence_required: true
```

## Critère de décision Ministral/Granite

La décision humaine regarde au minimum :

1. réussite du premier appel d'outil ;
2. réussite de la réparation après erreur ;
3. stabilité sur trois répétitions ;
4. erreurs de protocole ;
5. latence et débit ;
6. pression/résidence VRAM ;
7. qualité DevOps/coding sur les autres preuves du projet.

Le challenger n'est jamais autorisé à contourner un échec HARD-40M de la flotte active.

## Identité modèle

La qualification HARD-40M capture un fingerprint candidat des trois modèles routés et ne promeut ce fingerprint qu'après un gate complet PASS.

Cette opération ne modifie ni le catalogue, ni le choix Vulkan, ni l'approbation V1. Le mode `-Quick` ne promeut jamais l'identité modèle.

## Commandes

### Dry-run complet

```powershell
.\menu.ps1 -Action qualification -DryRun
```

### HARD-40M réel

```powershell
.\menu.ps1 -Action qualification
```

### Diagnostic Quick

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Quick ne remplace jamais le gate complet ni l'E2E.

## Validation du runtime Vulkan géré

Le profil B580 hybride se vérifie avec :

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action e2e -Backend b580-hybrid -DryRun
```

Ces commandes valident la voie choisie et son intégration OpenClaw. Elles ne constituent pas une compétition de backends.

## Local-only

```text
cloud_calls_allowed_during_qualification: false
cloud_models_supported: false
local_only: true
```

Un outil Web peut être utilisé dans un scénario de fraîcheur/sourcing lorsque le protocole le prévoit, mais aucun modèle LLM en ligne n'est appelé pour générer la réponse.

## Interprétation

Un modèle n'est pas retenu parce qu'il démarre ou parce qu'une fiche annonce une capacité. Il doit respecter les critères fonctionnels, le budget temps, la stabilité et le compromis VRAM/RAM/latence pertinent pour le workflow multi-agent.

Le backend GPU, lui, n'est plus à sélectionner : **le contrat actif est Vulkan**.
