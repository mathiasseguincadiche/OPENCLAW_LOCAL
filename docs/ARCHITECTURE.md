# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` gère les contrats, l'installation reproductible et les outils de la plateforme IA locale. Il ne transforme pas Windows en workstation générale et ne gère pas WSL2.

```text
HOST Windows 11 Pro
|
+-- OPENCLAW_LOCAL runtime verrouillé
|    +-- Python / venv clawlocal
|    +-- Node.js isolé
|    +-- OpenClaw
|    +-- Ollama natif Windows
|
+-- OpenClaw / Gateway loopback
|    +-- 8 agents matérialisés
|    +-- 8 workspaces gérés
|    +-- politiques outils par rôle
|    +-- Ollama natif Windows (nominal)
|    |    +-- Qwen / Gemma
|    +-- OpenRouter (optionnel, escalade explicite)
|
+-- clawlocal
|    +-- contrats de rôles
|    +-- catalogue modèles
|    +-- décision de routage
|    +-- renderer de configuration OpenClaw
|    +-- pont décision -> commande OpenClaw
|    +-- qualification / preuves
|
+-- WSL2 (externe, facultatif)
     +-- outils DevOps/Linux
```

## Chaîne de configuration

```text
config/v1/*.yaml + runtime_versions.json + agents/*
                    |
                    v
          clawlocal.openclaw_config
                    |
                    v
         openclaw.local.patch.json
                    |
          config patch --dry-run
                    |
                    v
        config OpenClaw validée
                    |
                    v
         Gateway + 8 agents locaux
```

Aucun secret n'est incorporé au patch généré. Les workspaces sont reconstruits depuis Git et l'état runtime reste hors dépôt.

## Sources de vérité

- `config/v1/*.yaml` : rôles, routage, sécurité et qualification ;
- `config/v1/runtime_versions.json` : versions runtime supportées/préférées ;
- `agents/*` : comportements humainement lisibles ;
- `src/clawlocal/openclaw_config.py` : rendu de la flotte ;
- `src/clawlocal/runtime.py` : routage exécutable ;
- runtime local : état observé, jamais supposé conforme ;
- `benchmarks/results/` et `<OPENCLAW_LOCAL_ROOT>/proofs/` : preuves locales non versionnées.

## Modes

1. **LOCAL_FAST** : modèle compact entièrement ou majoritairement en VRAM ;
2. **LOCAL_DEEP** : modèle plus lourd/offload, latence acceptée et activation explicite ;
3. **CLOUD_ESCALATION** : appel explicitement autorisé pour un motif déclaré.

Les fallbacks persistants OpenClaw restent locaux. L'escalade cloud est décidée par `clawlocal`, jamais par un fallback implicite dans la configuration de l'agent.

## Contrôles de sécurité structurants

- Ollama en loopback et API native ;
- Gateway en mode local/loopback ;
- filesystem borné au workspace ;
- exec en mode `ask` lorsqu'il est autorisé ;
- elevated désactivé ;
- rôles de revue sans mutation/exec ;
- cloud désactivé par défaut ;
- secrets hors Git ;
- aucune promotion automatique à partir de la CI.
