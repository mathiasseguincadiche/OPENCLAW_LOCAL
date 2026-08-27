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
local → deep transition
cloud escalation
cloud cost
success / error class
```

Une métrique inconnue doit rester absente ou `null`. Elle ne doit jamais être inventée.

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
  --model qwen-general `
  --backend ollama-vulkan `
  --route-kind local_primary `
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

La synthèse donne le nombre de runs, la durée totale observée, les tokens générés connus, les escalades cloud, les passages LOCAL_DEEP et le coût cloud connu.

Cette télémétrie complète la qualification matérielle : elle permet d'étudier la B580 en usage projet réel au lieu de se limiter à un benchmark synthétique.
