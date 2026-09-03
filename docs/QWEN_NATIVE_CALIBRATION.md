# Calibration Qwen native sur Intel Arc B580

## Pourquoi ce parcours existe

La qualification HARD-40M est un **gate**. Elle doit rester fail-closed : une sortie tronquée,
un timeout ou une erreur API rend le gate impossible lorsque `max_error_rate: 0.0`.

Les mesures réelles B580 ont montré que les trois probes Qwen en thinking natif présentent
une variabilité importante de durée et de débit. Modifier successivement la borne de sortie ou
le timeout du gate à partir d'un seul échec risquerait d'adapter le protocole à l'aveugle.

La calibration sépare donc deux questions :

1. combien de tokens et de temps les probes Qwen demandent-ils réellement sur cette machine ?
2. quelles bornes peuvent ensuite être justifiées dans le protocole HARD-40M ?

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

## Exécution

Dry-run :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -DryRun
```

Première mesure :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1
```

Le profil par défaut est volontairement plus large que le gate :

```text
max output : 1536 tokens
timeout    : 480 s par probe
repeats    : 1
```

Pour mesurer la variabilité après une première passe complète :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -Repeats 2
```

Les valeurs peuvent être ajustées explicitement pour un diagnostic, sans modifier le contrat :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 `
  -MaxOutputTokens 2048 `
  -CaseTimeoutSeconds 600 `
  -Repeats 1
```

## Ce qui est mesuré

Pour chaque probe :

- contexte ;
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

Le résultat est écrit sous :

```text
benchmarks/results/qwen_native_calibration_YYYYMMDD_HHMMSS.json
```

Le protocole est :

```text
qwen-native-calibration-v1
```

Le JSON porte explicitement :

```text
qualification_effect: none
promotion_allowed: false
```

Même si les trois probes sont `COMPLETE`, ce fichier n'est **pas** un PASS HARD-40M et ne doit
jamais être utilisé comme substitut à la qualification.

## Comment décider ensuite

Ne modifier le HARD-40M qu'après avoir observé au minimum :

- une complétion naturelle des trois probes ;
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
