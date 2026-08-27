# Télémétrie opérationnelle locale

OPENCLAW_LOCAL peut mesurer le comportement réel des agents et backends **sans enregistrer les prompts, réponses, secrets ou documents privés**.

## Métriques

Le contrat prévoit :

```text
agent
model
backend
route_kind
duration_ms
TTFT
tokens/s
prompt tokens
generated tokens
VRAM
RAM
tool calls
retries
local tier transition
cloud escalation
cloud cost
success / error class
```

Une métrique inconnue doit rester absente ou `null`. Elle ne doit jamais être inventée.

## Modèles locaux suivis

La télémétrie opérationnelle de la flotte locale concerne uniquement :

```text
qwen-max          -> qwen3.8:27b
gemma-deep        -> gemma4:26b
devstral-devops   -> devstral-small-2:24b
```

Le cloud, lorsqu'il est explicitement autorisé, est enregistré comme une route distincte et ne fait pas partie de la flotte locale supportée.

## Stockage

Chaque projet utilise :

```text
evidence/telemetry/runs.jsonl
```

Le format est append-only et reste local au projet géré.

## Enregistrement

```powershell
python .\scripts\34_record_telemetry.py `
  --project p5-devops `
  --agent ingenieur-devops `
  --model devstral-devops `
  --backend ollama-vulkan `
  --route-kind local_specialist `
  --duration-ms 8120 `
  --ttft-ms 430 `
  --tokens-per-second 18.7 `
  --generated-tokens 380 `
  --success
```

Les métriques doivent provenir d'une mesure réelle du runtime, d'OpenClaw ou du benchmark.

## Synthèse

```powershell
python .\scripts\34_record_telemetry.py `
  --project p5-devops `
  --summary
```

La synthèse donne le nombre de runs, la durée totale observée, les tokens générés connus, les escalades cloud, les transitions locales et le coût cloud connu.

Cette télémétrie complète la qualification matérielle : elle permet d'étudier les trois modèles de performance et les backends sur la workstation réelle au lieu de se limiter à un benchmark synthétique.
