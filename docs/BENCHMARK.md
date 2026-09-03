# Benchmark local

## Objectif

Mesurer avant de conclure. Le benchmark sépare :

1. **fonctionnel** : requêtes et contrôles conformes ;
2. **performance** : premier token, débit et durée murale ;
3. **contexte** : nominal 8K puis stress ciblé 16K ;
4. **projet/DevOps** : tâches proches de l'usage réel ;
5. **agentique** : tool-calling et réparation ;
6. **sélection de modèle** : incumbent deep vs challenger ;
7. **backend** : Ollama/Vulkan et candidats llama.cpp.

## Flotte opérationnelle testée

La plateforme route exactement trois modèles Q4_K_M :

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est un alias logique de compatibilité ; son runtime réel est Qwen2.5 Coder 14B.

Cette liste est la **flotte routée**, pas la totalité des modèles pouvant être chargés ponctuellement pour une comparaison de sélection.

## Challenger obligatoire de Gemma

Le dépôt déclare un challenger hors routage :

```text
ministral-tool-calling -> ministral-3:14b-instruct-2512-q4_K_M
```

Il est obligatoire avant la sélection humaine définitive du modèle deep afin de mesurer notamment le tool-calling natif et la réparation après retour d'outil.

Ministral :

- n'est pas un quatrième modèle routé ;
- n'est pas un fallback ;
- n'entre pas dans les 30 cas HARD-40M ;
- ne peut jamais être auto-promu ;
- ne remplace Gemma qu'après preuve et décision humaine explicite dans une modification ultérieure du catalogue.

## Dimensionnement B580

Le contexte **8192** est nominal. Le contexte **16384** reste un stress HARD-40M. Les poids indicatifs du registre des trois modèles routés sont environ 6,6 / 8,1 / 9,0 Go. Le challenger Ministral est référencé à environ 9,1 Go dans le contrat.

Ces tailles ne constituent pas une preuve de résidence complète en VRAM. `size_vram`, TTFT, débit et stabilité doivent être observés sur la B580 réelle.

## Suite active `devops-v2`

La suite `benchmarks/suites/devops_v2.yaml` fournit les scénarios fonctionnels. `config/v1/qualification_policy.yaml` possède la matrice HARD-40M, les seuils et le contrat challenger.

La passe complète utilise :

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

## Qwen thinking

La passe complète conserve trois probes Qwen avec thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond est **1024 tokens** pour ces probes. Une génération qui atteint le plafond est classée tronquée et fait échouer le gate. Le benchmark Quick désactive le thinking Qwen pour fournir un diagnostic court et comparable.

## HARD-40M

Le contrat temps reste :

```text
qualification complète : 2400 s
réserve évaluation      :   60 s
benchmark par défaut    : 2100 s
cas individuel          :  210 s maximum
```

Le runner ne prolonge pas silencieusement un cas. Une erreur API, un timeout ou une troncature avec `max_error_rate: 0.0` déclenche un fail-fast lorsque le résultat global est déjà impossible.

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

## Comparaison Gemma 3 12B vs Ministral 3 14B

### Installation du challenger

Le benchmark ne télécharge jamais le challenger implicitement :

```powershell
ollama pull ministral-3:14b-instruct-2512-q4_K_M
```

### Dry-run

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
```

### Mesure réelle

```powershell
.\scripts\windows\23_compare_model_challenger.ps1
```

Le wrapper utilise le Python géré OPENCLAW_LOCAL et appelle :

```text
scripts/52_compare_tool_calling_models.py
```

### Protocole `native_tool_calling_v1`

Paramètres par défaut :

```text
Gemma      : gemma3:12b-it-q4_K_M
Ministral  : ministral-3:14b-instruct-2512-q4_K_M
contexte   : 8192
répétitions: 3
timeout     : 180 s par échange
```

La comparaison teste le **protocole d'outils natif Ollama**, et non une simple génération JSON simulant une intention d'outil.

Pour chaque répétition :

1. le modèle reçoit deux définitions d'outils : `read_file` et `list_files` ;
2. il doit appeler `read_file(path="config/prod.yaml")` ;
3. le runner renvoie un message outil `ERROR file_not_found` ;
4. le modèle doit se réparer en appelant `list_files(directory="config")`.

Le protocole mesure :

- `tool_intent_pass_rate` ;
- `tool_repair_pass_rate` ;
- erreurs de protocole ;
- médiane des durées ;
- tokens/s lorsque fournis par Ollama ;
- taille chargée, `size_vram`, ratio de résidence GPU et contexte via `/api/ps` lorsque disponibles.

### Confidentialité de la preuve

Le contenu brut des réponses n'est pas persisté. La preuve conserve :

- longueur du contenu ;
- SHA-256 du contenu ;
- appels d'outils structurés ;
- métriques runtime utiles.

Fichier :

```text
benchmarks/results/tool_calling_challenger_YYYYMMDD_HHMMSS.json
```

Une comparaison complète produit :

```text
VERDICT=MEASURED_FOR_MANUAL_SELECTION
PROMOTION_ALLOWED=false
MANUAL_DECISION_REQUIRED=true
```

Une défaite fonctionnelle d'un modèle n'est pas une erreur du benchmark : c'est une **preuve négative valide**. En revanche, modèle absent, API inaccessible ou protocole incomplet rendent la comparaison `INCOMPLETE`.

## Critère de décision Gemma/Ministral

La décision humaine doit regarder au minimum :

1. réussite du premier appel d'outil ;
2. réussite de la réparation après erreur ;
3. stabilité sur trois répétitions ;
4. erreurs de protocole ;
5. latence et débit ;
6. pression/résidence VRAM ;
7. qualité architecture/rédaction/audit sur les autres preuves du projet.

Le tool-calling est une raison de challenger Gemma, pas un critère unique permettant de sacrifier la qualité des tâches deep.

## Identité modèle

La qualification HARD-40M capture un fingerprint candidat des trois modèles routés et ne le promeut qu'après PASS complet. La preuve challenger est indépendante et ne modifie aucun fingerprint qualifié ni le catalogue.

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

Quick utilise 36 cas à 8192 tokens et ne remplace jamais le gate complet ni la comparaison Gemma/Ministral.

## Comparaison Intel Arc des backends

Le dépôt prépare notamment :

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Pour les comparaisons de backends, ajouter temps de chargement, prompt tokens/s, VRAM/RAM, stabilité et temps de changement de modèle. Aucun backend n'est auto-promu.

## Interprétation

Un modèle n'est pas retenu parce qu'il démarre ou parce qu'une fiche annonce une capacité. Il doit respecter les critères fonctionnels, le budget temps, la stabilité et le compromis VRAM/RAM/latence pertinent pour le workflow multi-agent.

La flotte devient « candidate officielle à benchmarker » lorsqu'elle est contractualisée ; elle ne devient « qualifiée » qu'après preuves matérielles et revue humaine.
