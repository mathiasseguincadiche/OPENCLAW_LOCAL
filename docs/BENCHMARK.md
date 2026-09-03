# Benchmark local

## Objectif

Mesurer avant de conclure. Le benchmark sépare :

1. **fonctionnel** : requêtes réussies et contrôles conformes ;
2. **performance** : premier token, débit et durée murale ;
3. **contexte** : nominal 8K puis stress ciblé 16K ;
4. **projet/DevOps** : tâches proches de l'usage réel ;
5. **agentique** : discipline outil et réparation ;
6. **backend** : comparaison Ollama/Vulkan et candidats llama.cpp.

## Flotte testée

La plateforme supporte exactement trois modèles Q4_K_M :

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est l'alias logique historique du spécialiste DevOps ; son runtime réel est Qwen2.5 Coder 14B. Aucun quatrième modèle local n'est optionnel dans le gate.

## Dimensionnement B580

Le contexte **8192** est nominal. Le contexte **16384** reste un stress de qualification. Les poids indicatifs du registre sont environ 6,6 Go / 8,1 Go / 9,0 Go, mais la résidence VRAM complète et le débit restent à mesurer sur la B580 réelle.

Le redimensionnement de la flotte ne modifie pas les seuils de qualification : il doit démontrer son bénéfice par les mesures.

## Suite active `devops-v2`

La suite `benchmarks/suites/devops_v2.yaml` fournit les scénarios fonctionnels. `config/v1/qualification_policy.yaml` possède la matrice HARD-40M et les seuils.

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

Les trois modèles restent obligatoires.

## Qwen thinking

La passe complète conserve trois probes Qwen avec thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond est **1024 tokens** pour ces probes. Une génération qui atteint le plafond est classée tronquée et fait échouer le gate. Les autres cas Qwen utilisent une génération bornée sans payer systématiquement le coût du reasoning natif.

Le benchmark Quick désactive le thinking Qwen pour fournir un diagnostic court et comparable.

## HARD-40M

Le contrat temps reste :

```text
qualification complète : 2400 s
réserve évaluation      :   60 s
benchmark par défaut    : 2100 s
cas individuel          :  210 s maximum
```

Le runner ne prolonge pas silencieusement un cas au-delà de son deadline. Une erreur API, un timeout ou une troncature avec `max_error_rate: 0.0` déclenche un fail-fast lorsque le résultat global est déjà impossible.

## Métriques

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

Pour les comparaisons de backends, ajouter :

- temps de chargement ;
- prompt tokens/s ;
- `size_vram`/VRAM lorsqu'observable ;
- RAM lorsqu'observable ;
- stabilité ;
- temps de changement de modèle ;
- tool-calling.

Les valeurs inconnues restent inconnues.

## Identité modèle

La qualification complète capture un fingerprint candidat avant les générations. Elle **ne promeut ce fingerprint** vers `qualified_model_identity.json` qu'après un gate complet PASS et si l'identité n'a pas changé pendant l'exécution.

Cette opération **ne modifie ni le catalogue** de modèles ni le backend sélectionné et ne vaut pas approbation V1.

**Le mode `-Quick` ne promeut jamais** l'identité modèle.

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

Quick utilise 36 cas à 8192 tokens et ne remplace jamais le gate complet.

## Comparaison Intel Arc

Le dépôt prépare :

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Le comparateur utilise les mêmes modèles avec thinking désactivé, contexte 8192 et prompts identiques autant que possible. Le profil Vulkan/hybride reste lui aussi soumis à preuve réelle.

Aucun backend n'est auto-promu.

## Interprétation

Un modèle n'est pas retenu parce qu'il démarre. Il doit également respecter les critères fonctionnels, le budget temps, la stabilité, le tool-calling et le compromis VRAM/RAM/latence pertinent pour le workflow multi-agent.

Une amélioration de débit obtenue en sacrifiant les checks fonctionnels n'est pas un succès. Inversement, un modèle exact mais trop lent pour le workflow nominal n'est pas considéré comme correctement dimensionné.
