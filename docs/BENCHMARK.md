# Benchmark local

## Objectif

Mesurer avant de conclure. Le benchmark complète la qualification en séparant :

1. **fonctionnel** : requêtes réussies et contrôles conformes ;
2. **performance** : premier token, débit et durée murale ;
3. **contexte** : couverture fonctionnelle 8K puis stress ciblé 16K ;
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

La suite 8K couvre notamment :

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

La passe complète optimisée représente **48 cas** :

- **36 cas 8K** : 3 modèles × 12 scénarios, pour conserver la couverture fonctionnelle complète ;
- **12 cas 16K** : 3 modèles × 4 scénarios ciblés, pour éprouver uniquement les comportements où le contexte étendu apporte une information réelle : `project-intake-analysis`, `kubernetes-root-cause`, `tool-feedback-repair-json` et `long-context-discipline`.

Le mode `-Quick` reste à **36 cas** : les trois modèles et les douze scénarios, uniquement à 8192 tokens de contexte, avec thinking Qwen désactivé.

Cette matrice évite de rejouer à 16K des tâches courtes telles qu'un petit YAML, un diagramme D2 ou un JSON d'intention d'outil, sans retirer le stress 16K ni aucun des trois modèles.

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

Le runner utilise l'endpoint natif Ollama **`/api/chat`**. Ce choix permet de séparer `message.thinking` de `message.content`. Les sorties de raisonnement peuvent donc être mesurées sans être confondues avec la réponse finale soumise aux contrôles.

## Sorties bornées et politique de thinking

Chaque scénario déclare `max_output_tokens` dans `benchmarks/suites/devops_v2.yaml`. Le runner transmet une limite à Ollama via `num_predict` : aucune génération n'est laissée non bornée.

Deux politiques sont volontairement séparées :

- **Quick** : contexte 8192 uniquement et `think=false` pour Qwen ;
- **Complet optimisé** : Qwen conserve son thinking **natif**, mais son budget est borné à **768 tokens maximum par cas** au lieu de 2048. Les scénarios qui demandent davantage conservent toujours au moins leur propre limite. Gemma utilise `think=false` dans les gates fonctionnels bornés et les autres familles conservent leur limite de scénario.

Le plafond de 768 conserve un espace de raisonnement natif tout en empêchant qu'une tâche demandant 96 à 320 tokens de réponse puisse mobiliser jusqu'à 2048 tokens sur chaque cas.

Le mode complet optimisé reste la preuve de qualification de référence. Le mode Quick accélère les itérations mais ne remplace pas la couverture 16K ciblée.

Si Ollama termine un cas pour cause de limite de longueur, ou si `eval_count` atteint le budget `num_predict`, le runner enregistre `output_truncated=true`, ajoute `output_limit:fail` et marque le cas en `status=error`. Avec `max_error_rate: 0`, une sortie tronquée fait échouer le gate.

Le contenu du raisonnement interne n'est pas persisté. Le runner conserve seulement `thinking_chars` et les mesures de temps.

## Exécution

Qualification complète optimisée :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Passe rapide 8K uniquement :

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Runner direct :

```powershell
.\scripts\windows\07_run_qualification.ps1
.\scripts\windows\07_run_qualification.ps1 -Quick
```

La sélection individuelle de candidats n'existe pas dans la qualification : les trois modèles sont obligatoires.

## Mesures et progression

Après chaque cas, le runner affiche :

- `PASS`, `CHECK_FAIL` ou `ERROR` ;
- durée murale ;
- `first_tok`, temps jusqu'au **premier token réellement généré** ;
- `response_ttft`, temps jusqu'au premier token de réponse finale ;
- tokens/s ;
- nombre de tokens générés ;
- volume de thinking observé en caractères ;
- estimation du temps restant.

Pour un modèle reasoning en thinking natif, le premier token de thinking est bien le début réel de génération. Le gate de latence utilise donc `first_token_ms`, et non le délai jusqu'à la première partie de `message.content` après toute la réflexion.

Le JSON de preuve enregistre notamment :

- `first_generation_ms` ;
- `first_token_ms` ;
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
- durée murale totale.

## Contextes

- 8K : couverture fonctionnelle complète exigée ;
- 16K : couverture ciblée exigée sur quatre scénarios de stress ;
- 32K ou plus : uniquement après preuve que le coût KV-cache, la mémoire, le premier token et le débit restent acceptables.

Une capacité théorique annoncée par un modèle n'est pas une capacité opérationnelle qualifiée.

## Gate automatique

Les seuils sont versionnés dans `config/v1/qualification_policy.yaml` :

- aucune erreur API tolérée ;
- taux minimal de contrôles conformes ;
- débit médian minimal ;
- plafond p95 du temps au premier token ;
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

Les résultats bruts restent sous `benchmarks/results/` et hors Git. Une synthèse publiable indique au minimum le modèle, le runtime, le backend, les versions, le contexte, la politique de thinking, le pilote GPU, le protocole, la date, les mesures observées et les anomalies.
