# Modèles locaux

## Règle de promotion

Un modèle n'est jamais promu parce qu'il est populaire ou parce qu'un benchmark public est favorable. Il doit réussir les tâches représentatives du projet avec une qualité, une stabilité, une latence et une consommation mémoire acceptables sur la workstation cible.

La flotte est réévaluée en août 2026, mais **publication officielle ≠ qualification B580**. Les gros modèles restent `optional_candidate` tant qu'un benchmark réel Windows/OpenClaw/backend ne les a pas promus.

## Flotte de référence — août 2026

| Alias | Runtime Ollama | Classe | Usage | Statut |
|---|---|---|---|---|
| `qwen-general` | `qwen3.5:9b` | LOCAL_FAST | généraliste rapide, orchestration courante, DevOps courant | candidate / required |
| `gemma-review` | `gemma4:12b` | LOCAL_FAST | rédaction, architecture, revue indépendante rapide | candidate / required |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST | software engineering et DevOps agentique | optional candidate |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP | architecture, rédaction et revue complexes | optional candidate |
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX | raisonnement, orchestration et investigation locale maximale | optional candidate |
| `sera-devops` | `sera-14b` | LEGACY_CANDIDATE | spécialiste compact expérimental | hors routage actif |

Sources amont vérifiées lors de cette mise à jour :

- Qwen3.8 : https://ollama.com/library/qwen3.8
- Devstral Small 2 : https://ollama.com/library/devstral-small-2
- Gemma 4 : https://ollama.com/library/gemma4

La source de vérité opérationnelle reste `config/v1/model_catalog.yaml`.

## Pourquoi conserver Qwen3.5 9B et Gemma 4 12B

Les deux modèles fast restent requis parce qu'ils sont destinés au parcours quotidien sur 12 Go de VRAM. Ils constituent également le fallback sûr lorsque les modèles plus lourds ne sont pas encore qualifiés, ne sont pas chargés ou ne satisfont pas les seuils de stabilité/performance.

## LOCAL_SPECIALIST

`devstral-small-2:24b` est le spécialiste DevOps/code agentique de référence. Il est destiné aux tâches d'exploration de dépôt, modification multi-fichiers, automatisation et usage d'outils. Il ne devient nominal pour `ingenieur-devops` qu'après qualification réelle de la combinaison modèle + backend + B580.

SERA reste conservé comme candidat historique compact, mais n'est plus une route active : son provider `custom_gguf` ne doit jamais être exécuté silencieusement tant que l'import/backend correspondant n'a pas été préparé et qualifié.

## LOCAL_DEEP

`gemma4:26b` est le deep de la famille Gemma pour :

- architecture complexe ;
- ADR et compromis ;
- documentation longue ;
- revue qualité approfondie.

Le modèle est MoE et reste soumis au benchmark de mémoire, débit et stabilité. Sur la B580 12 Go, un offload VRAM + RAM est attendu plutôt qu'une résidence VRAM complète.

## LOCAL_MAX

`qwen3.8:27b` remplace l'ancien `qwen3.5:27b` comme candidat généraliste maximal. Il vise :

- planification complexe ;
- raisonnement transversal ;
- investigation sécurité ;
- synthèse de recherche difficile ;
- seconde route locale avant toute escalade cloud.

Il reste optionnel tant que les mesures réelles sur la workstation ne sont pas disponibles.

## Promotion runtime

Les modèles optionnels ne deviennent automatiquement sélectionnables par le parcours nominal que lorsqu'ils sont déclarés qualifiés dans l'état runtime local :

```powershell
$env:OPENCLAW_LOCAL_QUALIFIED_MODELS = 'qwen-max,gemma-deep,devstral-devops'
```

Cette variable est un mécanisme runtime local, non versionné. En production, elle doit refléter les résultats réels de qualification de la workstation, pas servir à contourner le benchmark.

Sans qualification :

```text
route préférée lourde
        ↓
non qualifiée
        ↓
LOCAL_FAST requis
```

Après qualification :

```text
Chef / Recherche / Sécurité -> Qwen3.8 27B si leur tier max est préféré
Architecte / Rédacteur / Auditeur -> Gemma 4 26B si deep est préféré
DevOps -> Devstral Small 2 24B si le spécialiste est préféré
Release -> Qwen3.5 9B par défaut
```

## Multimodalité

Qwen, Gemma et Devstral sont déclarés selon les modalités publiées par leur runtime. Cette déclaration **n'est pas une preuve de qualification multimodale** : PDF, images, vision, tool-calling et contexte doivent réussir les tests E2E réels avant promotion.

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

## Contexte

Le catalogue peut annoncer des fenêtres de contexte très grandes, mais OPENCLAW_LOCAL conserve un contexte opérationnel prudent tant que l'impact KV-cache, VRAM/RAM, TTFT et débit n'a pas été benchmarké. Le contexte est augmenté par mesure, jamais par marketing.

## Gate anti-régression

`scripts/45_validate_model_fleet.py` vérifie la flotte août 2026, les tiers, les identifiants runtime, la qualification obligatoire des gros modèles et l'indépendance de l'Auditeur. Le gate est exécuté dans CI, Python 3.12/3.13 et Release.
