# Modèles locaux

## Règle de promotion

Un modèle n'est jamais promu parce qu'il est populaire ou parce qu'un benchmark public est favorable. Il doit réussir les tâches représentatives du projet avec une qualité, une stabilité, une latence et une consommation mémoire acceptables sur la workstation cible.

## Candidats V0.2

| Alias | Runtime | Classe | Usage | Statut |
|---|---|---|---|---|
| `qwen-general` | `qwen3.5:9b` | LOCAL_FAST | généraliste, orchestration, DevOps courant | candidate / required |
| `gemma-review` | `gemma4:12b` | LOCAL_FAST | rédaction, architecture, seconde opinion | candidate / required |
| `qwen-deep` | `qwen3.5:27b` | LOCAL_DEEP | raisonnement plus lourd | optional candidate |
| `sera-devops` | `sera-14b` | LOCAL_DEEP | software engineering / DevOps spécialisé | optional candidate |

La source de vérité est `config/v1/model_catalog.yaml`.

## Tags explicites

Les modèles Ollama doivent utiliser un identifiant versionné/taggé explicite. La V0.2 corrige notamment l'ambiguïté `gemma4` en utilisant `gemma4:12b`.

Le validateur de configuration refuse un `runtime_id` Ollama non taggé et le validateur de dépôt empêche les scripts Windows de recopier les identifiants déclarés dans le catalogue.

## LOCAL_FAST

La classe LOCAL_FAST vise le travail quotidien et une résidence GPU aussi confortable que possible sur 12 Go de VRAM :

- questions et explications ;
- scripts ;
- CI/CD ;
- configuration ;
- revue ;
- documentation ;
- orchestration.

La classe ne garantit pas une performance donnée : elle décrit l'intention de routage avant mesure.

## LOCAL_DEEP

LOCAL_DEEP accepte :

- un modèle plus lourd ;
- de l'offload VRAM/RAM ;
- une latence plus importante ;
- un chargement à la demande.

Le but est d'obtenir davantage de qualité locale avant d'utiliser le cloud.

`qwen3.5:27b` et SERA ne doivent être activés que lorsque leur runtime réel a été préparé et qualifié.

## Multimodalité

Qwen et Gemma sont déclarés avec des entrées `text` + `image` dans le catalogue afin de rendre la capacité testable. Cette déclaration **n'est pas une preuve de qualification multimodale** : l'usage image doit réussir des tests réels OpenClaw/backend avant promotion.

## Tool-calling

La qualité du texte ne suffit pas. Pour être route agentique de production, un modèle doit réussir :

- appel d'outil structuré ;
- non-fabrication d'un résultat d'outil ;
- gestion d'erreur ;
- réparation après erreur ;
- respect du rôle ;
- arrêt correct ;
- stabilité sur plusieurs runs ;
- résistance raisonnable aux instructions adverses.

## Backends

Le modèle et le backend restent découplés. La V0.2 compare :

- Ollama/Vulkan ;
- llama.cpp/SYCL ;
- llama.cpp/Vulkan.

Voir `docs/RUNTIME_BACKENDS.md`.

## Ce que 12 Go de VRAM impliquent

Les 12 Go de la B580 rendent les modèles compacts particulièrement adaptés au parcours quotidien. Les modèles plus lourds peuvent devenir utilisables avec offload RAM, mais la vitesse, le contexte et la stabilité doivent être mesurés au lieu d'être déduits de la taille du modèle.
