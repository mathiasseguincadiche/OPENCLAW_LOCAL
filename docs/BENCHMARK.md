# Benchmark local

## Objectif

Mesurer avant de conclure. Le benchmark sépare :

1. **fonctionnel** : requêtes et contrôles conformes ;
2. **performance** : premier token, débit et durée murale ;
3. **contexte benchmark** : nominal 8K puis stress ciblé 16K ;
4. **projet/DevOps** : tâches proches de l'usage réel ;
5. **agentique** : tool-calling et réparation ;
6. **sélection du spécialiste** : incumbent Ministral vs challenger Granite ;
7. **backend** : Ollama/Vulkan et candidats llama.cpp locaux.

Architecture V2 n'autorise aucun appel vers un modèle LLM cloud pendant la qualification.

## Flotte opérationnelle testée

La plateforme route exactement trois modèles Q4_K_M :

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

`devstral-devops` est un alias logique de compatibilité ; son runtime V2 réel est Ministral 3 14B Reasoning.

Cette liste est la **flotte routée**, pas la totalité des modèles pouvant être chargés ponctuellement pour une comparaison de sélection.

## Challenger local du spécialiste DevOps

Le dépôt déclare un challenger hors routage :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite est mesuré contre l'incumbent `devstral-devops` pour le coding, le tool-calling natif, la réparation après retour d'outil et l'adéquation B580.

Granite :

- n'est pas un quatrième modèle routé ;
- n'est pas un fallback ;
- n'entre pas dans les 30 cas HARD-40M de la flotte opérationnelle ;
- ne peut jamais être auto-promu ;
- ne remplace Ministral qu'après preuve matérielle et décision humaine explicite dans une modification ultérieure du catalogue/routage.

## Contextes : benchmark != OpenClaw

Le benchmark utilise :

```text
8192  -> contexte nominal
16384 -> stress ciblé HARD-40M
```

OpenClaw full-agent utilise séparément 16384 tokens comme fenêtre nominale d'orchestration. Cette valeur **ne promeut pas** le benchmark 16K et n'autorise aucune montée automatique à 32768.

Les tailles de fichiers/registre ne prouvent pas la résidence complète en VRAM. `size_vram`, TTFT, débit, RAM et stabilité doivent être observés sur la B580 réelle.

## Suite active `devops-v2`

La suite `benchmarks/suites/devops_v2.yaml` fournit les scénarios fonctionnels. `config/v1/qualification_policy.yaml` possède la matrice HARD-40M, les seuils et le contrat challenger.

La passe complète utilise :

```text
benchmark_qualification_40m_v2.py
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

Le plafond est **1024 tokens** pour ces probes. Une génération qui atteint le plafond est classée tronquée et fait échouer le gate. Le benchmark Quick désactive le thinking Qwen afin de fournir un diagnostic plus court et comparable.

## HARD-40M

Le contrat temps reste :

```text
qualification complète : 2400 s
réserve évaluation      :   60 s
benchmark par défaut    : 2100 s
cas individuel          :  210 s
```

Le runner ne prolonge pas silencieusement un cas. Une erreur API, un timeout ou une troncature avec `max_error_rate: 0.0` déclenche un échec conformément au protocole.

Le runner actif est `scripts/benchmark_qualification_40m_v2.py`. Les valeurs ci-dessus restent alignées avec `config/v1/qualification_policy.yaml`.

## Seuils actifs

Le contrat `automated_gates.thresholds` impose notamment :

```text
max_error_rate                    = 0.0
min_check_pass_rate               = 0.875
min_median_tokens_per_second      = 6.0
max_p95_first_token_ms            = 12000
8K min check pass rate            = 0.875
16K min check pass rate           = 0.75
```

Architecture V2 n'abaisse aucun de ces seuils.

## Métriques HARD-40M

Pour chaque cas, conserver autant que possible :

- `wall_ms` ;
- premier token réellement généré ;
- délai jusqu'à la réponse finale ;
- `tokens_per_second` ;
- nombre de tokens de sortie ;
- volume de thinking sans contenu brut ;
- statut des checks ;
- backend ;
- contexte ;
- identité exacte du modèle.

Les valeurs inconnues restent inconnues.

## Comparaison Ministral 3 Reasoning vs Granite 4.2

### Installation du challenger

Le benchmark ne télécharge jamais le challenger implicitement :

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

Le wrapper utilise le Python géré OPENCLAW_LOCAL et le protocole versionné par le dépôt.

### Protocole `native_tool_calling_v1`

Paramètres de politique :

```text
incumbent   : devstral-devops / Ministral 3 14B Reasoning
challenger  : granite-devops / Granite 4.2 8B
contexte    : 8192
répétitions : 3
```

La comparaison teste le **protocole d'outils natif**, et non une simple génération JSON simulant une intention d'outil.

Pour chaque répétition, le modèle doit effectuer le parcours d'outil attendu, recevoir un retour contrôlé en erreur et produire la réparation prévue par le protocole.

Métriques contractuelles :

- `tool_intent_pass_rate` ;
- `tool_repair_pass_rate` ;
- `protocol_error_count` ;
- `median_wall_ms` ;
- `median_tokens_per_second` ;
- `median_gpu_residency_ratio` lorsque mesurable.

### Confidentialité de la preuve

Le contenu brut des réponses n'a pas besoin d'être persisté. Les preuves structurées doivent suffire pour l'audit, la comparaison et la décision humaine.

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

Une défaite fonctionnelle d'un modèle est une **preuve négative valide**. Modèle absent, API inaccessible ou protocole incomplet rendent en revanche la comparaison incomplète.

## Critère de décision Ministral/Granite

La décision humaine doit regarder au minimum :

1. réussite du premier appel d'outil ;
2. réussite de la réparation après erreur ;
3. stabilité sur trois répétitions ;
4. erreurs de protocole ;
5. latence et débit ;
6. pression/résidence VRAM ;
7. qualité DevOps/coding sur les autres preuves du projet.

Le challenger n'est jamais autorisé à contourner un échec du HARD-40M de la flotte active.

## Identité modèle

La qualification HARD-40M capture un fingerprint candidat des trois modèles routés et **ne promeut ce fingerprint** vers l'identité qualifiée qu'après un gate complet PASS.

Cette opération **ne modifie ni le catalogue** de modèles ni le backend sélectionné et ne vaut pas approbation V1. La preuve challenger est indépendante et ne modifie aucun fingerprint qualifié.

**Le mode `-Quick` ne promeut jamais** l'identité modèle.

## Commandes HARD-40M

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

Quick utilise le parcours diagnostique 8K prévu par le lanceur et ne remplace jamais le gate complet ni la comparaison Ministral/Granite.

## Comparaison Intel Arc des backends

Le dépôt prépare notamment :

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Pour les comparaisons de backends, ajouter temps de chargement, prompt tokens/s, VRAM/RAM, stabilité et temps de changement de modèle. Aucun backend n'est auto-promu.

## Local-only

Pendant la qualification :

```text
cloud_calls_allowed_during_qualification: false
cloud_models_supported: false
local_only: true
```

Un outil Web peut être utilisé dans un scénario qui évalue la discipline de fraîcheur/sourcing lorsque le protocole le prévoit, mais aucun modèle LLM en ligne n'est appelé pour générer la réponse.

## Interprétation

Un modèle n'est pas retenu parce qu'il démarre ou parce qu'une fiche annonce une capacité. Il doit respecter les critères fonctionnels, le budget temps, la stabilité et le compromis VRAM/RAM/latence pertinent pour le workflow multi-agent.

La flotte devient « candidate officielle à benchmarker » lorsqu'elle est contractualisée ; elle ne devient « qualifiée » qu'après preuves matérielles et revue humaine.
