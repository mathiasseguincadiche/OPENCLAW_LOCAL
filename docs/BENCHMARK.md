# Benchmark local

## Objectif

Mesurer avant de conclure. Le benchmark complète la qualification en séparant :

1. **fonctionnel** : requêtes réussies et contrôles conformes ;
2. **performance** : TTFT, débit et durée murale ;
3. **contexte** : 8K puis 16K ;
4. **projet/DevOps** : tâches proches de l'usage réel ;
5. **agentique** : discipline outil et réparation ;
6. **backend** : comparaison Ollama/Vulkan et candidats llama.cpp.

Le benchmark ne prétend pas qu'un modèle local est systématiquement équivalent à un modèle frontier cloud.

## Flotte testée

La plateforme supporte exactement trois modèles et la qualification les teste tous :

```text
qwen-max          -> qwen3.8:27b
gemma-deep        -> gemma4:26b
devstral-devops   -> devstral-small-2:24b
```

Il n'existe aucun modèle local optionnel dans le runner de qualification.

## Suite active : `devops-v2`

`scripts/benchmark_local.py` lit `config/v1/qualification_policy.yaml` puis charge la suite versionnée `benchmarks/suites/devops_v2.yaml`.

La suite couvre notamment :

- analyse de Project Intake ;
- GitLab CI YAML ;
- diagnostic Kubernetes sans cause inventée ;
- Terraform multi-fichiers ;
- idempotence Ansible ;
- revue sécurité ;
- runbook avec rollback ;
- diagramme D2 ;
- discipline face à une donnée récente ;
- intention d'outil JSON ;
- réparation après retour d'outil ;
- contexte synthétique long.

La passe complète représente **72 cas** : 3 modèles × 2 contextes × 12 scénarios. Le mode `-Quick` représente **36 cas** : les mêmes 3 modèles et 12 scénarios, mais uniquement à 8192 tokens de contexte.

## Contrôles exécutables

Le runner prend en charge :

- `nonempty` ;
- `contains_all` ;
- `contains_any` ;
- `not_contains_any` ;
- `json_keys` ;
- `yaml_keys`.

`scripts/22_validate_configs.py` refuse une suite contenant un contrôle inconnu.

## API d'inférence

Le runner utilise l'endpoint natif Ollama **`/api/chat`**. Ce choix correspond mieux au comportement conversationnel des modèles et permet de séparer proprement `message.thinking` de `message.content`. Les sorties de raisonnement peuvent donc être mesurées sans être confondues avec la réponse finale soumise aux contrôles.

## Sorties bornées et politique de thinking

Chaque scénario déclare `max_output_tokens` dans `benchmarks/suites/devops_v2.yaml`, avec une valeur par défaut de suite. Le runner transmet une limite à Ollama via `num_predict` : aucune génération n'est laissée avec le comportement non borné du runtime.

Deux politiques sont volontairement séparées :

- **Quick** : contexte 8192 uniquement et `think=false` pour la famille Qwen. Cette passe sert au diagnostic rapide des formats, contrôles et performances d'inférence sans payer le coût du raisonnement interne de Qwen3.8 sur chaque cas ;
- **Complet** : contextes 8192 et 16384, thinking Qwen laissé **natif**. Pour éviter qu'un petit plafond de scénario coupe le raisonnement avant la réponse finale, Qwen dispose alors d'un budget borné de 2048 tokens par cas. Les autres familles conservent le plafond spécifique du scénario.

Le mode complet reste donc la preuve de qualification de référence. Le mode Quick accélère les itérations mais ne remplace pas la passe complète.

Si Ollama termine un cas pour cause de limite de longueur, ou si `eval_count` atteint le budget `num_predict`, le runner enregistre `output_truncated=true`, ajoute `output_limit:fail` et marque le cas en `status=error`. Avec `max_error_rate: 0`, une sortie tronquée fait donc échouer le gate au lieu d'être absorbée par la tolérance du taux de contrôles.

Le contenu du raisonnement interne n'est pas persisté dans la preuve. Le runner conserve seulement `thinking_chars` et le temps avant premier token de réponse afin de mesurer le coût du thinking sans stocker sa trace brute.

## Exécution

Qualification complète :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Passe rapide 8K uniquement via le même centre de contrôle :

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Runner direct :

```powershell
.\scripts\windows\07_run_qualification.ps1
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Runner Python de diagnostic :

```powershell
python .\scripts\benchmark_local.py --qwen-thinking native
python .\scripts\benchmark_local.py --context 8192 --qwen-thinking off
```

La sélection individuelle de candidats n'existe plus dans la qualification : les trois modèles sont obligatoires.

## Source de vérité

Les scripts PowerShell obtiennent les modèles via `scripts/20_list_models.py`, alimenté par `config/v1/model_catalog.yaml`. Une qualification ne peut donc pas utiliser une flotte différente du routage sans modifier explicitement les contrats.

## Mesures et progression

Après chaque cas, le runner affiche une ligne opérateur avec :

- `PASS`, `CHECK_FAIL` ou `ERROR` ;
- durée murale du cas ;
- TTFT jusqu'au premier token de réponse finale ;
- tokens/s ;
- nombre de tokens générés ;
- volume de thinking observé en caractères, sans en stocker le contenu ;
- estimation du temps restant fondée sur la moyenne des cas déjà terminés.

Le JSON de preuve enregistre notamment :

- `first_generation_ms` ;
- `ttft_ms` ;
- `wall_ms` ;
- `eval_count` ;
- `eval_duration_ns` ;
- `tokens_per_second` ;
- `thinking_chars` ;
- `thinking_mode` ;
- `done_reason` ;
- `output_truncated` ;
- `scenario_max_output_tokens` ;
- `max_output_tokens` réellement appliqué ;
- contexte demandé ;
- résultat de chaque contrôle ;
- durée murale totale ;
- sortie finale brute dans les preuves locales hors Git.

La comparaison B580 complète ces données avec VRAM, RAM, stabilité, erreurs et tool-calling lorsqu'ils sont réellement observés.

## Contextes

- 8K : exigé ;
- 16K : exigé en passe complète ;
- 32K ou plus : uniquement après preuve que le coût KV-cache, la mémoire, le TTFT et le débit restent acceptables.

Une capacité théorique annoncée par un modèle n'est pas une capacité opérationnelle qualifiée.

## Gate automatique

Les seuils sont versionnés dans `config/v1/qualification_policy.yaml` :

- aucune erreur API tolérée ;
- taux minimal de contrôles conformes ;
- débit médian minimal ;
- plafond p95 du TTFT ;
- seuils par contexte requis.

Un succès donne au mieux `READY_FOR_MANUAL_QUALIFICATION`. Aucun script ne modifie automatiquement le catalogue ou le backend nominal.

## Gate manuel

Avant toute décision V1 ou promotion de backend, vérifier encore :

1. tool-calling OpenClaw réel ;
2. réparation après retour d'outil ;
3. Project Intake E2E ;
4. recherche Web locale E2E ;
5. multimodalité PDF/image ;
6. trois exécutions stables ;
7. absence de dépendance cloud nominale ;
8. comparaison des backends Intel Arc ;
9. revue humaine.

## Preuves

Les résultats bruts restent sous `benchmarks/results/` et hors Git. Une synthèse publiable indique au minimum :

- modèle et runtime exact ;
- backend ;
- versions OpenClaw/Ollama ;
- contexte ;
- politique de thinking appliquée ;
- pilote GPU ;
- protocole ;
- date ;
- mesures réellement observées ;
- limites et anomalies.
