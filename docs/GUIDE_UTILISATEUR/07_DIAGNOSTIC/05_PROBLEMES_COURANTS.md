# Problèmes courants

| Symptôme | Premier réflexe |
|---|---|
| commande non reconnue après installation | rouvrir PowerShell, puis `audit` |
| Ollama ne répond pas | `configure-local`, puis `verify` |
| modèle absent | `models` et vérifier `OLLAMA_MODELS` |
| Gateway indisponible | `openclaw gateway status --require-rpc --json` |
| agent en échec | transcript + preuve E2E/tâche |
| projet bloqué | `status` avant toute relance |
| clarification requise | `resolve` avec l'identifiant exact |
| validation/review en échec | lire le rapport et les tâches rouvertes |
| réponse lente | benchmark/qualification avant changement |
| configuration OpenClaw rejetée | lire le schéma vivant sous `runtime\generated` et le log |

Pour les procédures techniques profondes, utiliser `../../TROUBLESHOOTING.md`.