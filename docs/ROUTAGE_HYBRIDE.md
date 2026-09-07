# Routage local — Architecture V2

> Le nom de fichier `ROUTAGE_HYBRIDE.md` est conservé pour compatibilité des liens historiques. En V2, « hybride » désigne uniquement la combinaison de **backends locaux** Ollama/llama.cpp, jamais un mélange local + LLM cloud.

## Intention

Architecture V2 impose un parcours **LLM local-only**. Le routeur ne contient aucune destination vers un modèle en ligne. Une demande de cloud est refusée explicitement afin qu'une panne locale, une lenteur ou une absence de qualification ne puissent jamais être masquées par un fournisseur externe.

Les outils Web restent disponibles pour récupérer des sources ; la synthèse et le raisonnement sont réalisés localement.

## Flotte locale fermée

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

`devstral-devops` est un alias de compatibilité vers Ministral 3 14B Reasoning. Aucun quatrième modèle n'est routé.

Challenger benchmark séparé :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite possède `routing_active: false` et `automatic_promotion: false`.

## Routage nominal par rôle

```text
Chef opérations       -> qwen-max
Expert recherche      -> qwen-max + outils Web
Architecte solutions  -> gemma-deep
Ingénieur DevOps      -> devstral-devops
Ingénieur sécurité    -> qwen-max
Release/Forges        -> qwen-max
Rédacteur technique   -> gemma-deep
Auditeur qualité      -> gemma-deep
```

Si le producteur est de famille Gemma, l'Auditeur peut utiliser `qwen-max` comme alternative indépendante lorsque cela est praticable.

## Tiers locaux

Le contrat `model_routing.yaml` peut exprimer les tiers :

```text
local_primary
local_specialist
local_deep
local_max
local_fallback
independent_alternative
```

Chaque alias référencé par ces champs doit appartenir à la flotte routée fermée. Aucun tier ne peut résoudre un modèle externe ou le challenger Granite sans modification explicite du catalogue/routage.

## Profil backend `b580-hybrid`

Le profil candidat répartit les modèles entre moteurs **tous locaux** :

```text
qwen-max        -> backend local sélectionné
gemma-deep      -> backend local sélectionné
devstral-devops -> backend local sélectionné
image/PDF       -> Ollama local tant que le multimodal alternatif n'est pas qualifié
```

Les implémentations actuelles permettent notamment Ollama/Vulkan et llama.cpp/Vulkan/SYCL selon les contrats runtime.

Ce profil est **explicite** et ne devient jamais nominal par simple modification de configuration. La flotte V2 doit produire ses propres mesures B580 et un E2E complet avant toute décision.

## Fallback local

Les fallbacks restent dans la flotte fermée :

- rôles Qwen généralistes -> Gemma lorsque pertinent ;
- rôles Gemma -> Qwen généraliste ;
- DevOps -> Qwen généraliste si le spécialiste est indisponible et si la tâche reste compatible ;
- aucune indisponibilité locale ne déclenche un modèle externe.

Si aucun chemin local autorisé n'est viable, l'opération **échoue** et produit une preuve de diagnostic.

## Multimodalité et handoff DevOps

`qwen-max` et `gemma-deep` prennent en charge le parcours image/PDF. `devstral-devops` est text-only dans le contrat nominal.

Pour une tâche DevOps issue d'un PDF ou d'une image :

```text
document/image
  -> ingestion + analyse multimodale Qwen/Gemma
  -> représentation/provenance
  -> handoff textuel
  -> devstral-devops / Ministral 3 14B Reasoning
```

Le spécialiste ne prétend jamais avoir directement observé une image qu'il n'a pas reçue.

## Web local-first

Une information récente suit :

```text
expert-recherche
  -> web_search / web_fetch / browser si nécessaire
  -> sources récentes
  -> validation/provenance
  -> synthèse par qwen-max local
```

L'outil Web fournit des données. Il ne constitue pas un backend LLM.

## Interdictions V2

Le routeur refuse notamment :

- toute demande `request_cloud` ;
- l'option historique `--cloud` ;
- un alias hors catalogue routé ;
- l'utilisation de Granite comme fallback implicite ;
- un quatrième modèle routé caché ;
- une promotion automatique après benchmark ;
- une montée 32K implicite ;
- le masquage d'un échec local par un service externe.

## Exemple local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

La route nominale est :

```text
devstral-devops -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

## Exemple de refus cloud

La compatibilité CLI conserve éventuellement le mot-clé historique pour produire un échec explicite :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis la recherche.' `
  --cloud
```

Résultat attendu : erreur de politique `Architecture V2 local-only` et code de sortie non nul. Aucun appel vers un modèle en ligne n'est tenté.

## Contextes

```text
benchmark nominal : 8192
OpenClaw agent     : 16384
```

Le contexte agent 16K n'est pas une promotion du benchmark. Aucun passage à 32K n'est automatique.

## Qualification avant promotion

Une modification de flotte invalide la réutilisation des conclusions de performance de l'ancienne flotte. Avant de promouvoir un backend local, il faut de nouvelles preuves : benchmark isolé, E2E OpenClaw, tool-calling, stabilité, contexte, multimodalité et revue humaine.

Le challenger Granite ne peut être promu qu'après benchmark réel et décision humaine. Aucun backend, modèle, contexte étendu ou verdict V1 n'est auto-promu.
