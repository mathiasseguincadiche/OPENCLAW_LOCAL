# Qualification de la workstation

## But

La qualification transforme la flotte et les backends déclarés dans Git en décisions fondées sur des **preuves réelles** produites sur la workstation cible. Elle ne sert pas à découvrir de nouveaux modèles : la flotte supportée est déjà fermée à exactement trois modèles.

## Flotte obligatoire

| Alias | Runtime | Classe |
|---|---|---|
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST |

Les trois modèles sont `required: true`. L'échec de l'un d'eux fait échouer le gate global. Il n'existe aucun modèle local optionnel, aucun quatrième candidat et aucun switch de qualification permettant d'en ajouter un.

## Invariants

- aucun appel LLM cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- exactement trois modèles évalués ;
- aucun seuil modifié pour faire passer artificiellement un modèle ;
- aucune promotion automatique ;
- preuves brutes conservées hors Git ;
- toute dérive de modèle, backend, OpenClaw, Ollama ou pilote GPU invalide la réutilisation automatique d'une preuve précédente.

## 1. Installation propre

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Le parcours complet installe le runtime, configure le stockage local, télécharge les trois modèles, configure OpenClaw et le Gateway puis vérifie le parcours nominal.

Le smoke-test Ollama utilise l'API locale **`/api/chat`** avec `stream=false`. Il ne passe pas par `ollama run`. Pour Qwen3.8 et Gemma4, le thinking est désactivé pendant ce smoke-test minimal : cette étape vérifie que le runtime répond, pas sa capacité de raisonnement profond.

Après le smoke-test, `/api/ps` est interrogé pour afficher la taille réellement chargée en VRAM, la taille totale du modèle et le contexte alloué par Ollama.

## 2. Vérification du runtime

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Avant de poursuivre, vérifier notamment :

- runtime conforme au lock ;
- Ollama sur loopback ;
- trois modèles présents ;
- huit agents configurés ;
- aucun cloud requis.

### VRAM Windows

`Win32_VideoController.AdapterRAM` reste une information secondaire. L'audit privilégie `HardwareInformation.qwMemorySize`, champ QWORD 64 bits du registre Windows. Le fallback historique 32 bits n'est jamais présenté comme une mesure fiable sur un GPU moderne de plus de 4 GiB.

## 3. Gate OpenClaw E2E

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le gate E2E doit prouver au minimum :

1. les huit agents via le Gateway ;
2. le routage local attendu ;
3. un vrai appel d'outil ;
4. une erreur d'outil contrôlée suivie d'une réparation ;
5. trois exécutions locales stables ;
6. aucune dépendance cloud nominale.

Les preuves sont écrites sous `<OPENCLAW_LOCAL_ROOT>\proofs\`.

## 4. Qualification automatique des trois modèles

### Passe complète optimisée de référence

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Cette passe couvre **48 cas** :

- **36 cas 8K** : 3 modèles × 12 scénarios, pour conserver la couverture fonctionnelle complète ;
- **12 cas 16K** : 3 modèles × 4 scénarios ciblés : `project-intake-analysis`, `kubernetes-root-cause`, `tool-feedback-repair-json` et `long-context-discipline`.

Les tests 16K ne rejouent donc plus les tâches courtes qui n'apportent aucune information supplémentaire à contexte étendu. Le stress 16K reste obligatoire sur les tâches qui sollicitent réellement analyse, diagnostic, réparation et long contexte.

Pour Qwen3.8, le thinking reste dans son mode **natif** pendant la passe complète, mais son budget est borné à **768 tokens maximum par cas** au lieu de 2048. Les scénarios conservent au minimum leur propre limite fonctionnelle. Une génération qui atteint cette borne est considérée tronquée et fait échouer le gate : le gain de temps ne repose donc pas sur l'acceptation silencieuse d'une réponse coupée.

### Passe rapide d'itération

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Cette passe couvre **36 cas** : les mêmes 3 modèles et 12 scénarios, uniquement à 8192 tokens. Elle désactive le thinking de Qwen3.8 afin de vérifier rapidement formats, contrôles et performances d'inférence.

Le mode Quick sert au diagnostic et aux itérations courantes ; il **ne remplace pas** la passe complète optimisée pour une décision de qualification. Un Quick réussi retourne `QUICK_DIAGNOSTIC_PASS`, jamais `READY_FOR_MANUAL_QUALIFICATION`.

Ou directement :

```powershell
.\scripts\windows\07_run_qualification.ps1
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Le parcours enchaîne :

1. audit host/runtime ;
2. lecture des trois modèles `required` depuis `model_catalog.yaml` ;
3. smoke test API de chacun ;
4. inventaire matériel/runtime ;
5. benchmark via `/api/chat` selon `qualification_policy.yaml` ;
6. couverture complète 8K et stress ciblé 16K ;
7. évaluation des seuils versionnés.

Chaque scénario possède un plafond fonctionnel `max_output_tokens`. Une génération qui atteint le budget appliqué est enregistrée comme tronquée, marquée `status=error` et fait échouer le gate puisque la politique impose `max_error_rate: 0`.

Après chaque scénario, l'opérateur voit le statut, la durée, le temps au premier token réellement généré, le délai jusqu'à la réponse finale, les tokens/s, le nombre de tokens générés, le volume de thinking observé sans son contenu et une estimation du temps restant.

## 5. Mesures à collecter

Pour chaque modèle/backend pertinent :

- temps au premier token réellement généré ;
- délai jusqu'au premier token de réponse finale ;
- tokens/s ;
- durée murale ;
- VRAM fiable ou explicitement inconnue ;
- offload VRAM réellement observé via Ollama ;
- RAM ;
- stabilité ;
- erreurs ;
- contexte 8K/16K ;
- politique de thinking ;
- tool-calling ;
- réparation après retour d'outil ;
- comportement multimodal PDF/image lorsqu'il s'applique.

Pour un modèle reasoning, le gate de latence utilise le **premier token réellement généré**, y compris un token du canal thinking. Le temps jusqu'au premier token de réponse finale reste enregistré séparément mais n'est pas confondu avec la TTFT d'inférence.

Les mesures absentes restent absentes : elles ne sont jamais inventées. La trace brute du thinking n'est pas conservée ; seul son volume est comptabilisé.

## 6. Comparaison des backends Intel Arc

Le contrat déclare :

- `ollama-vulkan` — chemin nominal pré-qualification ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat.

Comparer autant que possible le même modèle et la même quantification. Le choix doit reposer sur le compromis réel entre premier token, débit, VRAM/RAM, stabilité, contexte soutenable, compatibilité OpenClaw/tool-calling et simplicité d'exploitation.

Aucun backend n'est auto-promu.

## 7. Projet représentatif obligatoire avant V1

La qualification technique doit être complétée par au moins un projet réel couvrant :

```text
INTAKE_READY
-> ANALYZE
-> CLARIFY si nécessaire
-> PLAN
-> ASSIGN
-> EXECUTE
-> VALIDATE
-> REVIEW
-> PACKAGE
-> approbation humaine
-> COMPLETE
```

Le scénario doit idéalement contenir plusieurs formats et une dépendance entre tâches permettant de vérifier l'Artifact Exchange et la resynchronisation.

## Verdicts

### `NOT_READY`

Au moins un garde-fou automatique échoue. Conserver la preuve, diagnostiquer puis corriger la cause. Ne pas abaisser un seuil sans justification et revue.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques sont passés. Ce verdict **ne signifie pas V1 qualifiée**. Il reste à valider les preuves E2E, les performances, la stabilité, les backends et le projet représentatif.

## Preuves minimales pour la décision V1

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU ;
- inventaire matériel ;
- résultats des trois modèles ;
- politique de thinking réellement utilisée ;
- E2E OpenClaw ;
- comparaison backend ;
- test multimodal ;
- projet complet ;
- limites observées ;
- revue humaine.

## Pourquoi GitHub Actions ne suffit pas

La CI valide le code, les contrats, la compatibilité Python/PowerShell, les tests de sécurité et les invariants documentaires. Elle ne possède ni la workstation cible, ni son pilote, ni sa VRAM, ni les modèles réellement chargés.

La CI peut donc prouver la **conformité logicielle**, jamais inventer une qualification matérielle.

## Critère V1.0.0

`1.0.0` ne doit être envisagée qu'après :

1. installation propre ;
2. `audit` et `verify` réussis ;
3. E2E réel réussi ;
4. qualification des trois modèles ;
5. comparaison des backends prévue ;
6. au moins un projet complet ;
7. limites documentées ;
8. validation humaine finale.
