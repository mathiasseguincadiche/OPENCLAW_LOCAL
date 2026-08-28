# Backends d'inférence locale

## Objectif

La plateforme ne lie pas définitivement les trois modèles supportés à un seul backend GPU. Le backend est un axe d'exploitation distinct du choix du modèle et du rôle.

## Backends déclarés

| ID | Provider | Accélération | Statut |
|---|---|---|---|
| `ollama-vulkan` | Ollama | Vulkan | nominal pré-qualification |
| `llama-cpp-sycl` | llama.cpp | SYCL | candidat |
| `llama-cpp-vulkan` | llama.cpp | Vulkan | candidat |

Le mot **nominal** signifie « chemin d'installation et d'intégration actuel », pas « vainqueur de performance ».

## Flotte indépendante du backend

```text
Modèles supportés
  +-- LOCAL_MAX        -> qwen-max        -> qwen3.8:27b
  +-- LOCAL_DEEP       -> gemma-deep      -> gemma4:26b
  +-- LOCAL_SPECIALIST -> devstral-devops -> devstral-small-2:24b

Backends
  +-- Ollama/Vulkan
  +-- llama.cpp/SYCL
  +-- llama.cpp/Vulkan
```

Changer de backend ne doit pas nécessiter de réécrire les huit rôles, le Project Orchestrator ou les politiques d'escalade.

## Ollama/Vulkan

Ollama est le chemin nominal car il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- intégration OpenClaw ;
- exploitation quotidienne ;
- tool-calling sur le parcours actuel.

L'API reste liée à `127.0.0.1:11434`. Les modèles sont stockés sous `<OPENCLAW_LOCAL_ROOT>\models\ollama` via `OLLAMA_MODELS`.

## llama.cpp/SYCL et Vulkan

Ces backends restent candidats tant qu'ils n'ont pas été :

1. installés explicitement ;
2. configurés ;
3. testés avec les modèles/quantifications compatibles ;
4. intégrés au parcours OpenClaw ;
5. benchmarkés ;
6. validés E2E.

Aucun candidat n'est installé ni promu silencieusement.

## Protocole de comparaison

Comparer, autant que possible, le même modèle et la même quantification sur :

- TTFT ;
- tokens/seconde ;
- VRAM ;
- RAM ;
- stabilité ;
- erreurs ou sorties corrompues ;
- tool-calling OpenClaw ;
- contextes 8K et 16K ;
- simplicité de démarrage, mise à jour et récupération.

Une différence de débit seule ne suffit pas si elle dégrade la stabilité ou l'intégration agentique.

## Promotion

`qualification_policy.yaml` impose l'absence de promotion automatique. Une décision de backend doit être documentée avec :

- versions exactes ;
- pilote GPU ;
- protocole ;
- résultats ;
- limites ;
- raison du choix ;
- procédure de rollback.

## Preuve matérielle

Les performances de la workstation ne sont jamais dérivées du nom de la carte graphique ni d'un benchmark externe. Les rapports locaux constituent la preuve opérationnelle et ne deviennent publiables qu'après revue et redaction.
