# Qualification de la workstation

## But

La qualification transforme la flotte et les backends déclarés dans Git en décisions fondées sur des **preuves réelles** produites sur la workstation cible. Elle ne sert pas à découvrir de nouveaux modèles : la flotte supportée est fermée à exactement trois modèles.

## Flotte obligatoire

| Alias | Runtime | Classe |
|---|---|---|
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST |

Les trois modèles sont `required: true`. L'échec de l'un d'eux fait échouer le gate global. Il n'existe aucun modèle local optionnel ni quatrième candidat dans cette qualification.

## Invariants

- aucun appel LLM cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- exactement trois modèles évalués ;
- aucun seuil modifié pour faire passer artificiellement un modèle ;
- aucune promotion automatique de backend, de catalogue ou de verdict V1 ;
- le fingerprint exact des modèles peut être promu vers l'état `QUALIFIED` **uniquement après un gate complet PASS** ;
- preuves brutes conservées hors Git ;
- toute dérive de modèle, backend, OpenClaw, Ollama ou pilote GPU invalide la réutilisation automatique d'une preuve précédente ;
- **la qualification complète ne doit jamais dépasser 40 minutes de temps mural**.

La promotion d'identité modèle n'est pas une promotion de backend ni une validation V1 : elle enregistre seulement le digest, le format, la famille, la taille de paramètres et la quantification réellement observés pendant une qualification complète réussie.

## 1. Installation propre

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Le parcours complet installe le runtime, configure le stockage local, télécharge les trois modèles, configure OpenClaw et le Gateway puis vérifie le parcours nominal.

Le smoke-test Ollama utilise l'API locale **`/api/chat`** avec `stream=false`. Il ne passe pas par `ollama run`. Pour Qwen3.8 et Gemma4, le thinking est désactivé pendant ce smoke-test minimal : cette étape vérifie que le runtime répond, pas sa capacité de raisonnement profond.

Après le smoke-test, `/api/ps` peut être interrogé pour afficher la taille réellement chargée en VRAM, la taille totale du modèle et le contexte alloué par Ollama.

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
- aucun cloud requis ;
- identité modèle actuelle compatible avec l'état qualifié lorsqu'il existe.

Sous Windows, les chemins de vérification utilisent le runtime Python géré OPENCLAW_LOCAL et ne doivent pas retomber silencieusement sur un Python système ambigu.

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

### Passe complète HARD-40M de référence

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Cette passe couvre **30 cas** :

- **24 cas 8K** : 8 scénarios adaptés au rôle de chacun des trois modèles ;
- **6 cas 16K** : 2 scénarios de stress ciblés par modèle ;
- les **12 scénarios** de `devops-v2` restent tous couverts collectivement à 8K ;
- les trois modèles restent obligatoires.

La matrice complète est versionnée dans `config/v1/qualification_policy.yaml` sous `automated_gates.scenario_matrix`.

Le 16K est conservé sur les tâches qui apportent réellement une contrainte de contexte : Project Intake et long contexte pour Qwen/Gemma ; diagnostic Kubernetes et long contexte pour Devstral.

### Qwen reasoning

Le thinking Qwen n'est plus activé sur tous les cas. Il reste **natif sur trois probes dédiés** :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Ces probes sont bornés à **768 tokens**. Tous les autres cas Qwen utilisent `think=false` et leur plafond de scénario normal. On conserve donc une preuve réelle du reasoning sans payer son coût sur les tâches courtes de formatage ou de contrôle.

Une génération qui atteint sa borne est considérée tronquée et fait échouer le gate. Le gain de temps ne repose pas sur l'acceptation silencieuse de réponses coupées.

### Budget temps contractualisé

`qualification_policy.yaml` fixe :

```text
qualification complète : 2400 s maximum
réserve évaluation      :   60 s
benchmark direct        : 2100 s par défaut
cas individuel          :  210 s maximum
```

`scripts/windows/07_run_qualification.ps1` démarre un chronomètre au début du parcours. Après audit, inventaire et capture de l'identité exacte des modèles, il retire le temps déjà consommé et réserve 60 secondes pour l'évaluation finale. Le budget restant est transmis au benchmark.

`scripts/benchmark_qualification_40m_v2.py` applique ensuite son propre deadline mural. Une erreur API, un timeout ou une sortie tronquée déclenche un **fail-fast**, puisque `max_error_rate: 0.0` rend déjà le gate impossible.

Si le budget de 40 minutes est atteint, le verdict est `FAIL/HARD_TIMEOUT` : le script ne continue pas au-delà de la limite.

### Verrouillage de l'identité des modèles

Avant le benchmark complet, la qualification capture l'identité runtime des trois modèles dans `state/qualification/candidate_model_identity.json`. Cette identité contient notamment le `runtime_id`, le digest, le format, la famille, la taille de paramètres et la quantification.

Après un gate complet PASS et seulement dans ce cas, cette même identité est promue vers `qualified_model_identity.json`. Si l'identité change pendant le run, la promotion est refusée. Si elle change ultérieurement, `verify` marque l'état qualifié `INVALIDATED` et impose une nouvelle qualification complète.

Le mode `-Quick` ne promeut jamais l'identité modèle.

### Suppression des smokes redondants en mode complet

La passe complète ne génère plus trois smokes avant le benchmark. Elle vérifie le catalogue et la présence des modèles, puis la matrice de benchmark effectue directement de vraies générations sur chacun d'eux.

Les smokes restent disponibles via `verify` et sont conservés dans le mode `-Quick`. Le gate OpenClaw E2E reste également distinct.

### Passe rapide d'itération

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Cette passe conserve **36 cas** : 3 modèles × 12 scénarios, uniquement à 8192 tokens, avec thinking Qwen désactivé.

Le mode Quick sert au diagnostic ; il **ne remplace pas** la qualification HARD-40M. Un Quick réussi retourne `QUICK_DIAGNOSTIC_PASS`, jamais `READY_FOR_MANUAL_QUALIFICATION`.

Ou directement :

```powershell
.\scripts\windows\07_run_qualification.ps1
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Le parcours complet enchaîne :

1. audit host/runtime et VRAM ;
2. lecture des trois modèles `required` ;
3. inventaire matériel/runtime ;
4. capture de l'identité exacte des trois modèles ;
5. benchmark HARD-40M via `/api/chat` ;
6. matrice 30 cas 8K/16K ;
7. évaluation des seuils versionnés ;
8. promotion du fingerprint modèle uniquement après PASS complet ;
9. contrôle final que la durée totale reste inférieure à 2400 s.

Après chaque scénario, l'opérateur voit le statut, la durée, le temps au premier token réellement généré, le délai jusqu'à la réponse finale, les tokens/s, le nombre de tokens générés, le volume de thinking sans son contenu, le budget restant et une estimation du temps restant.

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

Pour un modèle reasoning, le gate de latence utilise le **premier token réellement généré**, y compris un token du canal thinking. Le temps jusqu'au premier token de réponse finale reste enregistré séparément.

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

Les cinq golden projects pré-V1 complètent cette preuve, mais ne remplacent pas le projet représentatif final ni sa revue humaine.

## Verdicts

### `NOT_READY`

Au moins un garde-fou automatique échoue. Conserver la preuve, diagnostiquer puis corriger la cause. Ne pas abaisser un seuil sans justification et revue.

### `HARD_TIMEOUT`

La workstation ne termine pas la qualification dans le budget opérationnel de 40 minutes. Ce résultat est un échec de qualification pour ce protocole ; on optimise le runtime ou la matrice, on ne laisse pas le processus dériver au-delà de la limite.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques sont passés **et le parcours s'est terminé sous 40 minutes**. Ce verdict ne signifie pas V1 qualifiée. Il reste à valider les preuves E2E, les performances, la stabilité, les backends, les golden projects et le projet représentatif.

## Preuves minimales pour la décision V1

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU ;
- inventaire matériel ;
- protocole `qualification-hard-40m-v1` ;
- identité exacte/digest/quantification des trois modèles ;
- durée totale de qualification ;
- résultats des trois modèles ;
- politique de thinking réellement utilisée ;
- E2E OpenClaw ;
- comparaison backend ;
- test multimodal ;
- golden projects ;
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
4. qualification HARD-40M des trois modèles ;
5. identité modèle verrouillée par le PASS complet ;
6. comparaison des backends prévue ;
7. golden projects exécutés et revus ;
8. au moins un projet complet ;
9. limites documentées ;
10. validation humaine finale.
