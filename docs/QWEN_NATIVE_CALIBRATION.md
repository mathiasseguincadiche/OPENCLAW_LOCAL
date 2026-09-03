# Calibration Qwen thinking sur Intel Arc B580

## Pourquoi ce parcours existe

La qualification HARD-40M est un **gate**. Elle doit rester fail-closed : une sortie tronquée,
un timeout ou une erreur API rend le gate impossible lorsque `max_error_rate: 0.0`.

Les mesures réelles B580 ont montré que les trois probes Qwen en thinking natif présentent
une variabilité importante de durée et de débit. Modifier successivement la borne de sortie ou
le timeout du gate à partir d'un seul échec risquerait d'adapter le protocole à l'aveugle.

La calibration sépare donc trois questions :

1. combien de tokens et de temps les probes Qwen demandent-ils réellement sur cette machine ?
2. quelle part du coût vient spécifiquement du thinking natif ?
3. quelles bornes ou quel routage peuvent ensuite être justifiés dans le protocole HARD-40M ?

La calibration **ne qualifie rien** et ne modifie aucun état de promotion.

## Périmètre

Le runner lit directement `automated_gates.qwen_native_cases` dans
`config/v1/qualification_policy.yaml`. Il mesure donc exactement les probes déclarés par le
contrat actif :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le modèle est `qwen-max` / `qwen3.8:27b` via Ollama.

## Modes de thinking

Deux modes sont disponibles :

```text
native  -> comportement reasoning natif Ollama/Qwen (`think` non forcé)
off     -> thinking explicitement désactivé (`think=false`)
```

`native` reste la valeur par défaut pour préserver la compatibilité avec le protocole de
calibration initial.

L'intérêt du mode `off` est de permettre un **A/B strict** : mêmes trois probes, mêmes prompts,
mêmes contextes, même modèle, même backend et mêmes bornes. Seul le thinking change.

## Exécution

Dry-run natif :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -DryRun
```

Mesure native :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1
```

Mesure A/B avec thinking désactivé :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -ThinkingMode off
```

Le profil par défaut est volontairement plus large que le gate :

```text
max output : 1536 tokens
timeout    : 480 s par probe
repeats    : 1
```

Pour mesurer la variabilité après une première passe complète :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -ThinkingMode off -Repeats 2
```

Les valeurs peuvent être ajustées explicitement pour un diagnostic, sans modifier le contrat :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 `
  -ThinkingMode off `
  -MaxOutputTokens 2048 `
  -CaseTimeoutSeconds 600 `
  -Repeats 1
```

## Ce qui est mesuré

Pour chaque probe :

- contexte ;
- mode de thinking ;
- statut `COMPLETE`, `CHECK_FAIL`, `TRUNCATED`, `TIMEOUT` ou `ERROR` ;
- premier token réellement généré ;
- TTFT de la réponse finale ;
- durée murale ;
- `eval_count` ;
- tokens/s ;
- volume de thinking ;
- `done_reason` ;
- état de troncature ;
- résultat des checks fonctionnels ;
- snapshot Ollama `/api/ps`, notamment `size`, `size_vram` et `context_length` lorsqu'ils sont
  disponibles.

Le contenu brut de la réponse n'est pas persisté dans la preuve. Seuls sa longueur et son
SHA-256 sont enregistrés.

## Preuve produite

Les nouveaux résultats sont écrits sous :

```text
benchmarks/results/qwen_thinking_calibration_native_YYYYMMDD_HHMMSS.json
benchmarks/results/qwen_thinking_calibration_off_YYYYMMDD_HHMMSS.json
```

Le protocole est :

```text
qwen-thinking-calibration-v2
```

Le JSON porte explicitement :

```text
thinking_mode: native|off
qualification_effect: none
promotion_allowed: false
```

Les anciennes preuves `qwen_native_calibration_*.json` produites par le protocole v1 restent
valides comme mesures historiques natives ; elles ne sont pas réécrites.

Même si les trois probes sont `COMPLETE`, ce fichier n'est **pas** un PASS HARD-40M et ne doit
jamais être utilisé comme substitut à la qualification.

## Comment interpréter l'A/B

Le run `off` doit être comparé au run `native` probe par probe :

- statut de complétion ;
- résultat des checks fonctionnels ;
- durée murale ;
- premier token / TTFT ;
- `eval_count` ;
- tokens/s ;
- contexte et état `/api/ps`.

Si `off` complète nettement plus vite tout en conservant les checks fonctionnels, le coût
principal est attribuable au reasoning natif et le HARD-40M peut ensuite être revu en termes de
routage ou de sélection des probes, plutôt qu'en abaissant artificiellement les seuils.

Si `off` reste trop lent ou échoue également, l'investigation doit plutôt cibler le backend,
l'offload, la quantification ou l'adéquation de `qwen3.8:27b` à 12 GiB de VRAM.

## Comment décider ensuite

Ne modifier le HARD-40M qu'après avoir observé au minimum :

- la comparaison native/off des trois probes ;
- leurs `eval_count` réels ;
- leurs durées murales ;
- la variabilité entre runs lorsque nécessaire ;
- l'état de résidence/offload exposé par `/api/ps` ;
- la compatibilité de toute nouvelle borne avec le plafond global de 2400 s.

Si un probe atteint encore 1536 ou 2048 tokens, ou dépasse plusieurs minutes de manière
irrégulière, la bonne décision peut être de revoir le rôle de ce probe dans le HARD-40M plutôt
que d'augmenter indéfiniment les bornes.

## Invariants

La calibration ne doit jamais :

- promouvoir `qualified_model_identity.json` ;
- modifier `release_readiness.yaml` ;
- déclarer un backend vainqueur ;
- abaisser les seuils de qualité ou performance ;
- appeler un fournisseur cloud ;
- transformer une mesure exploratoire en preuve V1.
