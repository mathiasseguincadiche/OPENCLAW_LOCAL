# Routage hybride

## Intention

Le parcours nominal reste local. OpenRouter n'est jamais un fallback technique automatique : c'est une **escalade explicite** soumise à motif, préconditions, budget et, selon le cas, validation humaine.

## Flotte locale fermée

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est un alias de compatibilité vers Qwen 2.5 Coder 14B. Aucun quatrième modèle local n'est supporté.

## Routage nominal par rôle

```text
Chef opérations       -> qwen-max
Expert recherche      -> qwen-max + Web
Architecte solutions  -> gemma-deep
Ingénieur DevOps      -> devstral-devops
Ingénieur sécurité    -> qwen-max
Release/Forges        -> qwen-max
Rédacteur technique   -> gemma-deep
Auditeur qualité      -> gemma-deep
```

Si le producteur est de famille Gemma, l'Auditeur peut utiliser `qwen-max` comme alternative indépendante lorsque cela est praticable.

## Profil backend `b580-hybrid`

Le profil candidat répartit les modèles selon le moteur local :

```text
qwen-max        -> ollama-vulkan
gemma-deep      -> llama-cpp-vulkan
devstral-devops -> llama-cpp-vulkan
image/PDF       -> ollama-vulkan
```

Ce profil est **explicite** et ne devient jamais nominal par simple modification de configuration. La nouvelle flotte doit produire ses propres mesures B580 et un E2E complet avant toute décision.

## Fallback local

Les fallbacks restent dans la flotte fermée :

- rôles Qwen généralistes -> Gemma lorsque pertinent ;
- rôles Gemma -> Qwen généraliste ;
- DevOps -> Qwen généraliste si le spécialiste est indisponible et si la tâche reste compatible ;
- aucune indisponibilité locale ne déclenche automatiquement OpenRouter.

Les champs `local_specialist`, `local_deep`, `local_max` et `independent_alternative` expriment les routes autorisées ; ils ne donnent jamais accès à un alias hors catalogue.

## Multimodalité et handoff DevOps

`qwen-max` et `gemma-deep` prennent en charge le parcours image/PDF. `devstral-devops` est text-only.

Pour une tâche DevOps issue d'un PDF ou d'une image :

```text
document/image
  -> ingestion + analyse multimodale Qwen/Gemma
  -> représentation/provenance
  -> handoff textuel
  -> devstral-devops / Qwen 2.5 Coder 14B
```

Le spécialiste ne prétend jamais avoir directement observé une image qu'il n'a pas reçue.

## Web local-first

Une information récente suit d'abord :

```text
expert-recherche local
  -> web_search / web_fetch / browser si nécessaire
  -> sources récentes
  -> synthèse locale
```

La fraîcheur seule n'est pas un motif d'appel LLM cloud.

## Motifs cloud versionnés

Les motifs actifs sont définis dans `config/v1/escalation_policy.yaml`.

- `deep_web_research` : recherche approfondie après tentative Web locale démontrée ;
- `source_conflict` : conflit réel entre sources ;
- `context_overflow` : contexte requis au-delà de la capacité locale **qualifiée** ;
- `repeated_local_failure` : échecs locaux réels selon le nombre minimal de tentatives ;
- `high_impact_decision` : approbation humaine requise ;
- `independent_final_review` : seconde opinion cloud exceptionnelle et approuvée.

## Interdictions

Le routeur refuse notamment :

- `web_freshness_only` ;
- la commodité ;
- la seule lenteur du local ;
- un fallback cloud silencieux ;
- l'absence de benchmark comme prétexte automatique ;
- un secret ;
- l'envoi automatique d'un document privé ;
- un modèle local hors flotte.

## Conditions générales du cloud

```text
cloud_enabled
+ motif explicite et versionné
+ rôle autorisé
+ préconditions démontrées
+ budget disponible
+ approbation humaine si requise
```

La planification peut vérifier le coût projeté sans modifier le ledger. Une exécution réelle réserve atomiquement le budget juste avant l'appel.

## Exemple local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

La route nominale est :

```text
devstral-devops -> qwen2.5-coder:14b-instruct-q4_K_M
```

## Exemple cloud explicite

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
$env:OPENROUTER_API_KEY = '<secret-local>'

python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis la recherche.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops `
  --execute
```

## Qualification avant promotion

Une modification de flotte invalide la réutilisation des conclusions de performance de l'ancienne flotte. Avant de promouvoir un backend ou le profil hybride, il faut de nouvelles preuves : benchmark isolé, E2E OpenClaw, tool-calling, stabilité, contexte, multimodalité et revue humaine.

Aucun backend, modèle ou verdict V1 n'est auto-promu.
