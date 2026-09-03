# Calibration Qwen thinking sur Intel Arc B580

## Pourquoi ce parcours existe

La qualification HARD-40M est un **gate** fail-closed : une sortie tronquée, un timeout ou une erreur API rend le gate impossible lorsque `max_error_rate: 0.0`.

La calibration est un parcours diagnostique séparé. Elle permet de mesurer le coût du thinking natif Qwen sans modifier les seuils ou promouvoir un état de qualification.

Elle répond à trois questions :

1. combien de tokens et de temps les probes Qwen demandent-ils réellement sur cette machine ?
2. quelle part du coût vient spécifiquement du thinking natif ?
3. les bornes HARD-40M restent-elles adaptées à la flotte actuelle ?

La calibration **ne qualifie rien** et ne modifie aucun état de promotion.

## Périmètre actif

Le runner lit directement `automated_gates.qwen_native_cases` dans `config/v1/qualification_policy.yaml` :

```text
8192  project-intake-analysis
8192  kubernetes-root-cause
16384 long-context-discipline
```

Le modèle courant est résolu par l'alias `qwen-max`, soit `qwen3.5:9b-q4_K_M` via Ollama. Le probe 16K reste un **stress de qualification** ; le contexte nominal OpenClaw de la flotte est 8192.

Les anciennes calibrations produites avec la flotte 24–27B restent des preuves historiques expliquant le right-sizing. Elles ne qualifient pas ce nouveau runtime.

## Modes de thinking

```text
native  -> comportement reasoning natif Ollama/Qwen (`think` non forcé)
off     -> thinking explicitement désactivé (`think=false`)
```

`native` reste la valeur par défaut du parcours de calibration. Le mode `off` fournit un A/B strict : mêmes probes, prompts, contextes, modèle et backend ; seul le thinking change.

## Exécution

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -DryRun
.\scripts\windows\22_calibrate_qwen_native.ps1
.\scripts\windows\22_calibrate_qwen_native.ps1 -ThinkingMode off
```

Le profil diagnostique par défaut reste volontairement plus large que le gate :

```text
max output : 1536 tokens
timeout    : 480 s par probe
repeats    : 1
```

Exemple de répétition :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 -ThinkingMode off -Repeats 2
```

Exemple de bornes diagnostiques explicites :

```powershell
.\scripts\windows\22_calibrate_qwen_native.ps1 `
  -ThinkingMode off `
  -MaxOutputTokens 2048 `
  -CaseTimeoutSeconds 600 `
  -Repeats 1
```

Ces paramètres exploratoires ne modifient pas le contrat HARD-40M.

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
- snapshot Ollama `/api/ps` (`size`, `size_vram`, `context_length`) lorsqu'il est disponible.

Le contenu brut de la réponse n'est pas persisté dans la preuve. Seuls sa longueur et son SHA-256 sont enregistrés.

## Preuve produite

```text
benchmarks/results/qwen_thinking_calibration_native_YYYYMMDD_HHMMSS.json
benchmarks/results/qwen_thinking_calibration_off_YYYYMMDD_HHMMSS.json
```

Protocole :

```text
qwen-thinking-calibration-v2
```

Le JSON porte explicitement :

```text
thinking_mode: native|off
qualification_effect: none
promotion_allowed: false
```

Même si les trois probes sont `COMPLETE`, ce fichier n'est **pas** un PASS HARD-40M.

## Interprétation

Comparer `off` à `native` probe par probe sur : statut, checks fonctionnels, durée murale, premier token/TTFT, `eval_count`, tokens/s et état `/api/ps`.

Si `off` complète nettement plus vite tout en conservant les checks, le surcoût vient principalement du reasoning natif. Si `off` reste trop lent ou échoue, examiner le backend, l'offload, la quantification ou la pression contexte/mémoire.

Ne modifier le HARD-40M qu'après plusieurs mesures cohérentes. Une borne atteinte reste une troncature ; elle ne doit jamais être acceptée silencieusement.

## Invariants

La calibration ne doit jamais :

- promouvoir `qualified_model_identity.json` ;
- modifier `release_readiness.yaml` ;
- déclarer un backend vainqueur ;
- abaisser les seuils de qualité ou performance ;
- appeler un fournisseur cloud ;
- transformer une mesure exploratoire en preuve V1.
