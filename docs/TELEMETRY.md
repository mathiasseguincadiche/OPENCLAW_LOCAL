# Télémétrie opérationnelle locale

La télémétrie sert à répondre avec des mesures à des questions comme : **quel agent coûte du temps ? quel modèle est réellement le plus rapide ? quand LOCAL_DEEP est-il utile ? la B580 suffit-elle ?**

## Principe

Les événements runtime sont stockés hors Git dans :

```text
<OPENCLAW_LOCAL_ROOT>/state/telemetry/events.jsonl
```

Le routage enregistre automatiquement les décisions lorsque la racine plateforme est disponible. Les métriques détaillées peuvent être ajoutées par les runners/benchmarks ou via la CLI.

## Champs supportés

- agent, modèle et backend ;
- type de route ;
- TTFT ;
- durée ;
- prompt tokens et generated tokens ;
- tokens/s ;
- VRAM et RAM mesurées ;
- nombre d'appels outils ;
- retries ;
- transition LOCAL_FAST → LOCAL_DEEP ;
- escalade cloud ;
- coût cloud en EUR.

Les métriques matérielles restent optionnelles : une valeur absente est préférable à une valeur inventée.

## Vie privée

La télémétrie refuse les champs de contenu de prompt/réponse et ne doit jamais enregistrer document source ou secret. Elle est opérationnelle, pas conversationnelle.

## Résumé

```powershell
python .\scripts\35_telemetry.py
python .\scripts\35_telemetry.py --project p5-devops --export-project-summary
```

L'export projet produit `evidence/telemetry_summary.json`. Le ledger brut reste hors Git.

## Enregistrement explicite

Un runner peut produire un petit JSON de métriques puis l'enregistrer :

```json
{
  "event_type": "agent_call",
  "project_id": "p5-devops",
  "agent": "ingenieur-devops",
  "model": "ollama/qwen3.5:9b",
  "backend": "ollama-vulkan",
  "ttft_ms": 420,
  "duration_ms": 5100,
  "generated_tokens": 640,
  "tokens_per_second": 31.2,
  "vram_mb": 8900,
  "ram_mb": 6200,
  "tool_calls": 3,
  "retries": 0,
  "cloud_escalation": false
}
```

Puis :

```powershell
python .\scripts\35_telemetry.py --record .\metrics.json
```
