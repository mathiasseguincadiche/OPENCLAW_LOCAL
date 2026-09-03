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

La suite versionnée reste `benchmarks/suites/devops_v2.yaml`. Elle contient douze scénarios :

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

La passe de qualification complète active est exécutée par `scripts/benchmark_qualification_40m_v2.py`. `scripts/benchmark_local.py` reste le runner générique et le support du mode `-Quick`.

## Matrice complète HARD-40M

La qualification de référence représente **30 cas** :

- **24 cas 8K** : 8 scénarios par modèle ;
- **6 cas 16K** : 2 scénarios ciblés par modèle ;
- les trois modèles restent obligatoires ;
- les douze scénarios de `devops-v2` sont tous couverts collectivement à 8K.

La matrice est adaptée au rôle nominal de chaque modèle au lieu de demander aux trois modèles d'exécuter douze fois exactement la même batterie.

### `qwen-max`

8K : Project Intake, GitLab CI, diagnostic Kubernetes, sécurité pipeline, fraîcheur Web, intention outil, réparation outil, long contexte.

16K : Project Intake et long contexte.

### `gemma-deep`

8K : Project Intake, Terraform, Ansible, sécurité pipeline, runbook, diagramme D2, fraîcheur Web, long contexte.

16K : Project Intake et long contexte.

### `devstral-devops`

8K : GitLab CI, diagnostic Kubernetes, Terraform, Ansible, sécurité pipeline, intention outil, réparation outil, long contexte.

16K : diagnostic Kubernetes et long contexte.

Le mode `-Quick` reste à **36 cas** : les trois modèles × les douze scénarios, uniquement à 8192 tokens, avec thinking Qwen désactivé. Il sert au diagnostic et ne remplace pas la qualification HARD-40M.

## Contrôles exécutables

Le runner prend en charge :

- `nonempty` ;
- `contains_all` ;
- `contains_any` ;
- `not_contains_any` ;
- `json_keys` ;
- `yaml_keys`.

Une génération tronquée est `status=error`. Comme `max_error_rate` reste à `0.0`, elle fait échouer la qualification immédiatement.

## API d'inférence

Le runner utilise l'endpoint natif Ollama **`/api/chat`**. Ce choix permet de séparer `message.thinking` de `message.content`. Le contenu du raisonnement interne n'est pas persisté ; seul son volume est compté.

## Politique de thinking

Gemma utilise `think=false` dans les gates fonctionnels bornés.

Pour Qwen, le thinking natif n'est plus payé sur chaque cas. Il est conservé sur exactement trois probes représentatifs :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Ces trois probes disposent d'un plafond de **768 tokens**. Tous les autres cas Qwen utilisent `think=false` et conservent la limite propre au scénario. Cette séparation préserve une preuve réelle de la capacité reasoning sans multiplier le coût de réflexion sur des tâches courtes de formatage JSON/YAML ou de contrôle simple.

## Budget temps dur

Le budget est versionné dans `config/v1/qualification_policy.yaml` :

```text
qualification complète : 2400 s = 40 min maximum
réserve évaluation      :   60 s
benchmark direct        : 2100 s = 35 min par défaut
timeout par cas         :  210 s maximum
```

Le runner complet est **fail-fast** lorsqu'une erreur API, un timeout ou une sortie tronquée rend déjà le gate impossible (`max_error_rate: 0`). Il ne continue pas pendant des dizaines de minutes pour produire un verdict déjà condamné.

Le parcours PowerShell mesure aussi sa durée depuis le début de la qualification. Le temps consommé par l'audit, l'inventaire et la capture d'identité modèle est retiré du budget transmis au benchmark. L'évaluation finale et la promotion conditionnelle du fingerprint restent incluses dans la limite de 40 minutes.

## Smokes et redondance

Le mode complet ne relance plus trois smokes d'inférence avant le benchmark : les trois modèles sont vérifiés dans le catalogue, puis leurs vraies générations de benchmark constituent la preuve d'inférence. Cela supprime une étape redondante.

Le mode `-Quick` conserve les smokes séparés pour son rôle de diagnostic rapide.

Le gate OpenClaw E2E reste distinct et conserve ses propres preuves de routage, tool-calling, réparation et stabilité.

## Exécution

Qualification complète HARD-40M :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Passe rapide 8K :

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Runner direct :

```powershell
.\scripts\windows\07_run_qualification.ps1
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Benchmark complet direct :

```powershell
.\scripts\windows\05_benchmark.ps1
```

Il utilise `benchmark_qualification_40m_v2.py` et un budget benchmark de 35 minutes par défaut. La qualification complète lui transmet un budget dynamique plus strict afin de conserver la limite de 40 minutes de bout en bout.

## Mesures et progression

Après chaque cas, le runner affiche :

- `PASS`, `CHECK_FAIL` ou `ERROR` ;
- durée murale ;
- `first_tok`, temps jusqu'au **premier token réellement généré** ;
- `response_ttft`, temps jusqu'au premier token de réponse finale ;
- tokens/s ;
- nombre de tokens générés ;
- volume de thinking observé ;
- budget restant et estimation du temps restant.

Pour Qwen en thinking natif, le premier token du canal `thinking` est bien le début réel de génération. Le gate de latence utilise donc `first_token_ms`, et non le délai jusqu'à la première partie de `message.content` après toute la réflexion.

Le JSON de preuve HARD-40M enregistre notamment :

- protocole `qualification-hard-40m-v1` ;
- budget global et timeout par cas ;
- matrice de scénarios ;
- probes Qwen natifs ;
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
- résultat de chaque contrôle ;
- durée murale totale ;
- état `budget_exhausted`.

## Identité modèle et qualification

Le benchmark ne choisit pas automatiquement un backend ni un modèle. La qualification complète capture séparément l'identité exacte des trois modèles Ollama avant le benchmark et ne promeut ce fingerprint vers l'état `QUALIFIED` qu'après un PASS complet.

Cette promotion d'identité signifie uniquement « ces poids/digest/quantification sont ceux qui ont passé le gate ». Elle ne modifie ni le catalogue, ni le routage nominal, ni le backend actif, ni le verdict V1. Le mode `-Quick` ne promeut jamais cette identité.

## Gate automatique

Les seuils restent versionnés dans `config/v1/qualification_policy.yaml` et ne sont pas abaissés pour tenir le budget :

- aucune erreur API tolérée ;
- taux minimal de contrôles conformes inchangé ;
- débit médian minimal inchangé ;
- plafond p95 du premier token inchangé ;
- seuils 8K et 16K inchangés.

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
