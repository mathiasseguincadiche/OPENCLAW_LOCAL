# Modèles locaux

## Politique V2

`OPENCLAW_LOCAL` utilise une flotte **B580 right-sized, performance-only et LLM local-only**. La flotte opérationnelle installée et routée contient **exactement trois modèles**, tous en Q4_K_M. Aucun petit modèle de secours, runtime legacy caché ou modèle LLM en ligne n'est autorisé.

| Alias routé | Runtime Ollama local | Taille registre indicative | Usage |
|---|---|---:|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | ~6,6 Go | orchestration, recherche, sécurité, release, raisonnement transversal, multimodal |
| `gemma-deep` | `gemma4:12b-it-q4_K_M` | ~7,6 Go | architecture, rédaction, audit, contre-revue multimodale |
| `devstral-devops` | `hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M` | ~8,24 Go | DevOps, software engineering agentique, outils dépôt, texte/code |

La source de vérité est `config/v1/model_catalog.yaml`. Le validateur CI exige que l'ensemble des alias **routés** reste exactement `{qwen-max, gemma-deep, devstral-devops}`.

L'alias `devstral-devops` est conservé pour compatibilité logique avec les routes, workspaces et états existants. En Architecture V2, son runtime réel est **Ministral 3 14B Reasoning** exécuté localement par Ollama depuis le GGUF officiel Mistral AI.

## Challenger local : Granite 4.2 8B

Le catalogue déclare un challenger séparé :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Ce challenger sert à comparer le spécialiste DevOps nominal sur coding, tool-calling natif, réparation après erreur d'outil et adéquation B580 lorsque cette preuve de sélection est nécessaire.

Important : Granite ne devient pas un quatrième modèle opérationnel :

- `routing_active: false` ;
- il n'est référencé par aucun rôle nominal ;
- il n'est pas un fallback ;
- il ne compte pas dans `local_model_count: 3` ;
- il n'est pas inclus comme substitut dans le HARD-40M des trois modèles routés ;
- `automatic_promotion: false` ;
- une décision humaine explicite est obligatoire avant tout éventuel remplacement de `devstral-devops`.

Le contrat de comparaison est versionné dans `config/v1/qualification_policy.yaml` sous `model_selection_challenger`.

## Pourquoi cette architecture

La cible matérielle est une Intel Arc B580 12 Go. Architecture V2 privilégie donc une flotte 9B/12B/14B quantifiée Q4_K_M, avec des responsabilités distinctes, plutôt que de considérer les fenêtres de contexte ou tailles maximales théoriques comme des réglages pratiques.

Ce dimensionnement est une **hypothèse d'architecture à qualifier**, pas une revendication de performance. Seules les mesures réelles B580 peuvent établir TTFT, tokens/s, VRAM/RAM, stabilité, résidence GPU et qualité utile.

## Support logiciel vs qualification matérielle

Trois niveaux sont séparés :

1. **flotte opérationnelle candidate** : Qwen 3.5 9B + Gemma 4 12B + Ministral 3 14B Reasoning ;
2. **challenger de sélection** : Granite 4.2 8B, hors routage ;
3. **qualification matérielle** : fonctionnement, stabilité, contexte, tool-calling, multimodalité et comportement réel sur la workstation.

`required: true` signifie que les trois modèles constituent la flotte fonctionnelle candidate ; cela ne signifie pas qu'ils sont déjà qualifiés sur la B580.

## Qwen 3.5 9B — `qwen-max`

`qwen3.5:9b-q4_K_M` couvre notamment :

- Chef des opérations ;
- Expert recherche ;
- Ingénieur sécurité ;
- Ingénieur Release/Forges ;
- raisonnement transversal ;
- contre-revue lorsque Gemma produit ;
- parcours multimodal PDF/image.

Les outils Web accessibles à certains rôles fournissent des sources d'information ; l'inférence LLM demeure locale.

## Gemma 4 12B — `gemma-deep`

`gemma4:12b-it-q4_K_M` est le modèle deep candidat pour :

- Architecte solutions ;
- Rédacteur technique ;
- Auditeur qualité ;
- revue multimodale ;
- documentation complexe.

Le contrat le déclare `input: [text, image]` et famille `gemma4`.

## Ministral 3 14B Reasoning — alias `devstral-devops`

Runtime :

```text
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Le spécialiste nominal de l'Ingénieur DevOps couvre exploration de dépôts, édition multi-fichiers, automatisation, CI/CD, conteneurs, Kubernetes, IaC, scripts, tool-calling et raisonnement technique.

Dans le contrat `OPENCLAW_LOCAL`, il reste **text-only**. Lorsqu'une tâche dépend d'une image ou d'un PDF, Qwen 3.5 ou Gemma 4 réalise la lecture multimodale puis transmet un handoff traçable au spécialiste.

Le catalogue enregistre explicitement :

```text
source_kind         = huggingface_gguf
source_repo         = mistralai/Ministral-3-14B-Reasoning-2512-GGUF
source_quantization = Q4_K_M
source_license      = Apache-2.0
```

## Granite 4.2 8B — `granite-devops`

`granite4.2:8b-q4_K_M` sert uniquement à une comparaison locale séparée. Les preuves peuvent recommander une décision, mais ne modifient jamais le routage automatiquement.

## Routage nominal

```text
Chef opérations       -> Qwen 3.5 9B
Expert recherche      -> Qwen 3.5 9B + outils Web
Architecte solutions  -> Gemma 4 12B
Ingénieur DevOps      -> Ministral 3 14B Reasoning
Ingénieur sécurité    -> Qwen 3.5 9B
Release/Forges        -> Qwen 3.5 9B
Rédacteur technique   -> Gemma 4 12B
Auditeur qualité      -> Gemma 4 12B
                         -> Qwen 3.5 9B si séparation de famille requise
```

Granite n'apparaît pas dans ce routage tant qu'une preuve comparative et une décision humaine n'ont pas conduit à modifier le catalogue dans une PR dédiée.

## Politique de contexte

La politique distingue le benchmark de l'orchestration :

```text
benchmark nominal / HARD-40M : 8192 tokens
OpenClaw agent orchestration : 16384 tokens
```

Le 16384 d'OpenClaw n'est pas une promotion du benchmark. Une montée à 32768 ou au-delà exige une qualification séparée ; elle n'est jamais automatique.

## HARD-40M

Le HARD-40M exige exactement :

```text
qwen-max
gemma-deep
devstral-devops
```

Si l'un de ces trois modèles échoue, la qualification de la flotte échoue. Granite constitue une **preuve de sélection séparée** et ne permet pas de contourner l'échec d'un modèle actif.

Le HARD-40M conserve 30 cas : 24 à 8K et 6 à 16K. Les seuils ne sont pas abaissés par Architecture V2.

## Backend GPU

Le choix de l'API GPU est déjà décidé : **Vulkan uniquement**.

Les chemins actifs sont :

```text
ollama-vulkan
llama-cpp-vulkan
b580-hybrid
```

`b580-hybrid` combine exclusivement des moteurs Vulkan locaux. Il n'existe plus de compétition entre API GPU dans le parcours actif et aucune re-comparaison de backend retiré n'est requise. Les vérifications matérielles servent uniquement à confirmer le fonctionnement et la stabilité de l'installation Vulkan réelle.

## Local-only

Le catalogue impose :

```text
local_first: true
local_only: true
cloud_models_supported: false
```

Aucun catalogue de modèle LLM cloud n'est accepté. Une demande de routage LLM cloud doit échouer explicitement. L'utilisation d'un outil Web ne change pas cette règle : le modèle qui analyse les résultats reste local.

## Gate anti-régression

`scripts/45_validate_model_fleet.py` vérifie notamment :

- exactement trois modèles locaux routés ;
- les trois runtime IDs V2 attendus ;
- Q4_K_M ;
- benchmark nominal 8192 ;
- orchestration OpenClaw 16384 séparée ;
- aucun retour des runtimes legacy ;
- Vulkan comme unique accélération GPU LLM active ;
- aucun retour du backend GPU retiré dans les surfaces actives ;
- qualification obligatoire des trois modèles ;
- indépendance Gemma/Qwen de l'Auditeur lorsque praticable ;
- Granite 4.2 exact et séparé du routage ;
- `automatic_promotion: false` ;
- refus du routage cloud.
