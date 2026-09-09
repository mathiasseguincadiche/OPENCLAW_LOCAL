# Routage local — Architecture V2

> Le nom de fichier `ROUTAGE_HYBRIDE.md` est conservé pour compatibilité des liens historiques. En V2, « hybride » désigne uniquement la combinaison locale **Ollama/Vulkan + llama.cpp/Vulkan**, jamais un mélange local + LLM cloud.

## Intention

Architecture V2 impose un parcours **LLM local-only**. Le routeur ne contient aucune destination vers un modèle en ligne. Une demande de cloud est refusée explicitement afin qu'une panne locale, une lenteur ou une absence de qualification ne puissent jamais être masquées par un fournisseur externe.

Les outils Web restent disponibles pour récupérer des sources ; la synthèse et le raisonnement sont réalisés localement.

Sur l'Intel Arc B580, le contrat GPU est également fermé : **Vulkan uniquement**.

## Flotte locale fermée

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

`devstral-devops` est un alias de compatibilité vers Ministral 3 14B Reasoning. Aucun quatrième modèle n'est routé.

Challenger de modèle séparé :

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

Le contrat `model_routing.yaml` peut exprimer :

```text
local_primary
local_specialist
local_deep
local_max
local_fallback
independent_alternative
```

Chaque alias référencé doit appartenir à la flotte routée fermée. Aucun tier ne peut résoudre un modèle externe ou le challenger Granite sans modification explicite du catalogue/routage.

## Profil backend `b580-hybrid`

Le profil hybride est explicite et **100 % Vulkan** :

```text
qwen-max        -> ollama-vulkan
gemma-deep      -> llama-cpp-vulkan
devstral-devops -> llama-cpp-vulkan
image/PDF       -> ollama-vulkan
```

`llama-cpp-vulkan` est un runtime géré interne. Les profils OpenClaw sélectionnables restent :

```text
ollama-vulkan
b580-hybrid
```

Le profil hybride doit produire son E2E et ses preuves B580 réelles avant usage quotidien. Cette exigence valide le fonctionnement du chemin choisi ; elle ne remet pas l'API GPU en compétition.

## Fallback local

Les fallbacks restent dans la flotte fermée :

- rôles Qwen généralistes -> Gemma lorsque pertinent ;
- rôles Gemma -> Qwen généraliste ;
- DevOps -> Qwen généraliste si le spécialiste est indisponible et si la tâche reste compatible ;
- aucune indisponibilité locale ne déclenche un modèle externe.

Si aucun chemin local autorisé n'est viable, l'opération **échoue** et produit une preuve de diagnostic.

## Multimodalité et handoff DevOps

`qwen-max` et `gemma-deep` prennent en charge le parcours image/PDF. `devstral-devops` est text-only dans le contrat nominal.

```text
document/image
  -> ingestion + analyse multimodale Qwen/Gemma
  -> représentation/provenance
  -> handoff textuel
  -> devstral-devops / Ministral 3 14B Reasoning
```

Le spécialiste ne prétend jamais avoir directement observé une image qu'il n'a pas reçue.

## Web local-first

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
- une promotion automatique après mesure ;
- une montée 32K implicite ;
- une autre API GPU LLM que Vulkan ;
- le masquage d'un échec local par un service externe.

## Exemple local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

Route nominale :

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
qualification nominale : 8192
OpenClaw agent          : 16384
```

Le contexte agent 16K n'est pas une promotion du benchmark. Aucun passage à 32K n'est automatique.

## Qualification

Une modification de flotte ou de runtime exige des preuves cohérentes avec le commit courant : HARD-40M, E2E OpenClaw, tool-calling, stabilité, contexte, multimodalité et revue humaine.

Le challenger Granite ne peut être promu qu'après comparaison réelle et décision humaine. Le profil hybride Vulkan ne peut être déclaré prêt qu'après preuve B580 réelle. **Le choix de l'API GPU, lui, n'est plus un sujet de promotion : il est verrouillé sur Vulkan.**
