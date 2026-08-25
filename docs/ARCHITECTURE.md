# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` gère les contrats et outils de la plateforme IA locale. Il ne transforme pas Windows en workstation générale et ne gère pas WSL2.

```text
HOST Windows 11 Pro
|
+-- OpenClaw / Gateway
|    |
|    +-- Ollama natif Windows (nominal)
|    |    +-- modèles locaux
|    |
|    +-- OpenRouter (optionnel, escalade)
|
+-- clawlocal
|    +-- rôles
|    +-- catalogue modèles
|    +-- routage
|    +-- politique d'escalade
|    +-- validations / preuves
|
+-- WSL2 (externe, facultatif)
     +-- outils DevOps/Linux
```

## Sources de vérité

- `config/v1/*.yaml` : état attendu ;
- `agents/*/AGENTS.md` : comportement humainement lisible ;
- runtime local : état observé, jamais supposé conforme ;
- `benchmarks/results/` : preuves locales ignorées par Git.

## Modes

1. **LOCAL_FAST** : modèle compact entièrement ou majoritairement en VRAM ;
2. **LOCAL_DEEP** : modèle plus lourd/offload, latence acceptée ;
3. **CLOUD_ESCALATION** : appel explicitement autorisé pour un motif déclaré.

Le mode cloud n'est jamais un fallback silencieux de confort.
