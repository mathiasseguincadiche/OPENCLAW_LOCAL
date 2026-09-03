# Qualification de la workstation

## But

La qualification transforme la flotte et les backends déclarés dans Git en décisions fondées sur des **preuves réelles** produites sur la workstation Windows 11 + Intel Arc B580. La CI valide les contrats ; elle ne fabrique jamais une qualification matérielle.

## Flotte obligatoire B580

| Alias logique | Runtime | Quantification | Rôle principal |
|---|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | Q4_K_M | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | Q4_K_M | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | Q4_K_M | DevOps, code, outils dépôt |

L'alias `devstral-devops` est conservé pour compatibilité logique ; le runtime est désormais Qwen2.5 Coder 14B et reste text-only. Les entrées PDF/image destinées au DevOps passent par Qwen/Gemma puis par un handoff traçable.

Les trois modèles sont `required: true`. L'échec de l'un d'eux fait échouer le gate global. Aucun quatrième modèle local n'est un fallback caché.

## Invariants

- aucun appel LLM cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- exactement trois modèles évalués ;
- quantification attendue Q4_K_M ;
- contexte nominal opérationnel : **8192 tokens** ;
- contexte **16384** : stress de qualification, jamais promotion nominale implicite ;
- aucun seuil modifié pour faire passer artificiellement un modèle ;
- aucune promotion automatique de backend, de catalogue ou de verdict V1 ;
- le fingerprint exact des modèles peut être promu vers l'état `QUALIFIED` **uniquement après un gate complet PASS** ;
- preuves brutes conservées hors Git ;
- toute dérive modèle/backend/runtime/pilote invalide la réutilisation automatique d'une preuve ;
- qualification complète : **2400 s** maximum.

## 1. Installation de la nouvelle flotte

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Pour une workstation déjà installée :

```powershell
.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
```

Le pull lit `model_catalog.yaml` et télécharge les trois runtimes requis. Les anciens modèles éventuellement présents sur disque ne font plus partie du routage supporté.

## 2. Vérification du runtime

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le smoke Ollama utilise `/api/chat`, un contexte réduit et une sortie courte. Pour Qwen 3.5, le thinking est désactivé pendant ce smoke minimal : cette étape vérifie la disponibilité du runtime, pas le raisonnement profond.

`/api/ps` expose lorsque disponible la taille chargée, `size_vram` et le contexte réellement alloué. Une résidence GPU complète n'est jamais supposée sans mesure.

Sous Windows, les chemins sensibles utilisent le runtime Python géré OPENCLAW_LOCAL.

## 3. Gate OpenClaw E2E

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le gate doit prouver :

1. les huit agents via le Gateway ;
2. le routage local attendu ;
3. un vrai appel d'outil avec Qwen Coder pour l'Ingénieur DevOps ;
4. une erreur d'outil contrôlée suivie d'une réparation ;
5. trois exécutions stables ;
6. aucune dépendance cloud nominale.

Les preuves sont écrites sous `<OPENCLAW_LOCAL_ROOT>\proofs\`.

## 4. HARD-40M

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le launcher utilise `benchmark_qualification_40m_v2.py`.

La matrice versionnée contient **30 cas** :

- 24 cas à 8192 tokens ;
- 6 cas à 16384 tokens ;
- exactement trois modèles requis ;
- les scénarios restent définis dans `devops-v2` et `qualification_policy.yaml`.

Le 16K sert à vérifier si le contexte étendu reste viable. Le support logiciel ne transforme jamais automatiquement ce stress en valeur nominale.

### Qwen reasoning

Trois probes Qwen gardent le thinking natif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le plafond HARD-40M reste **1024 tokens** sur ces probes. Atteindre cette borne reste une troncature et un échec. Tous les autres cas Qwen utilisent une génération bornée adaptée au scénario.

L'ancienne flotte 27B a montré sur la B580 que davantage de tokens ou de temps ne suffisait pas à corriger un mauvais ajustement matériel. Cette preuve historique motive le redimensionnement de la flotte ; elle ne constitue pas une qualification des nouveaux modèles.

### Budget temps contractualisé

```text
qualification complète : 2400 s maximum
réserve évaluation      :   60 s
benchmark direct        : 2100 s par défaut
cas individuel          :  210 s maximum
```

Le runner applique un deadline mural et un fail-fast lorsque `max_error_rate: 0.0` rend déjà le gate impossible. Un timeout, une erreur API ou une sortie tronquée ne sont jamais convertis en PASS.

## 5. Identité exacte des modèles

Avant le benchmark complet, la qualification capture l'identité des trois runtimes dans :

```text
state/qualification/candidate_model_identity.json
```

Elle contient notamment runtime ID, digest, format, famille, paramètres et quantification observée.

Après un gate complet PASS, et seulement dans ce cas, cette identité peut être promue vers :

```text
state/qualification/qualified_model_identity.json
```

Si l'identité change ensuite, `verify` doit retourner `INVALIDATED`. Cette promotion d'identité n'est **aucune promotion automatique de backend** ni une approbation V1.

Le mode `-Quick` ne promeut jamais l'identité modèle.

## 6. Diagnostic Quick

```powershell
.\menu.ps1 -Action qualification -Quick -DryRun
.\menu.ps1 -Action qualification -Quick
```

Quick conserve 36 cas à 8192 tokens avec thinking Qwen désactivé. Un succès produit un diagnostic ; il ne remplace pas HARD-40M.

## 7. Comparaison des backends

Backends candidats :

- `ollama-vulkan` ;
- `llama-cpp-sycl` ;
- `llama-cpp-vulkan` ;
- profil `b580-hybrid`.

Comparer autant que possible même modèle, même quantification, même contexte et mêmes prompts. Mesures à conserver : TTFT, tokens/s, prompt tokens/s, wall time, VRAM/RAM, temps de chargement, stabilité, tool-calling et changements de modèles.

Aucun backend n'est auto-promu.

## 8. Golden Projects et projet représentatif

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

Les cinq Golden Projects complètent le benchmark mais ne remplacent pas un projet réel de `INTAKE_READY` à `COMPLETE` avec revue humaine, multimodalité réelle, Artifact Exchange, télémétrie et package final.

## Verdicts

### `NOT_READY`

Au moins un gate échoue. Conserver la preuve et corriger la cause ; ne pas abaisser le protocole pour obtenir du vert.

### `HARD_TIMEOUT`

Le parcours ne termine pas sous 2400 s. C'est un échec du protocole pour cette configuration.

### `READY_FOR_MANUAL_QUALIFICATION`

Les gates automatiques passent sous le budget. Il reste la revue humaine, les backends, la multimodalité, les Golden Projects et le projet représentatif.

## Preuves V1 minimales

- commit Git exact ;
- versions Windows/PowerShell/Python/OpenClaw/Ollama ;
- pilote GPU ;
- inventaire matériel ;
- identité/digest/quantification des trois modèles ;
- preuve HARD-40M ;
- preuve OpenClaw E2E ;
- comparaison backend ;
- Golden Projects ;
- multimodalité réelle ;
- télémétrie réelle ;
- package du projet représentatif ;
- limites observées ;
- approbation humaine.

Les SHA-256 de ces preuves alimentent `config/v1/release_readiness.yaml`. Pour une version `>=1.0.0`, le validateur reste :

```powershell
python .\scripts\24_validate_release.py --tag v<VERSION>
```

V1 reste bloquée tant que les preuves matérielles réelles et l'approbation humaine ne sont pas complètes.
