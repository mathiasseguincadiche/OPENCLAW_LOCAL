# Routage hybride

## Intention

Le local traite le parcours nominal. OpenRouter n'est pas un fallback technique automatique : c'est une **escalade explicite** soumise à motif, préconditions, budget, et parfois validation humaine.

## Flotte locale fermée

```text
qwen-max          -> qwen3.8:27b
gemma-deep        -> gemma4:26b
devstral-devops   -> devstral-small-2:24b
```

Aucun quatrième modèle local n'est supporté.

## Routage nominal

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

## Fallback local

Les fallbacks restent dans la même flotte fermée :

- rôles Qwen -> Gemma lorsque pertinent ;
- rôles Gemma -> Qwen ;
- DevOps -> Qwen si Devstral est indisponible ;
- aucune indisponibilité locale ne déclenche automatiquement OpenRouter.

Les champs `local_specialist`, `local_deep`, `local_max` et `independent_alternative` expriment la spécialité et les routes autorisées ; ils ne donnent jamais accès à un alias hors catalogue.

## Web local-first

Une information récente suit d'abord :

```text
expert-recherche local
  -> web_search / web_fetch / browser si nécessaire
  -> sources récentes
  -> synthèse locale
```

La simple fraîcheur d'une donnée n'est pas un motif d'appel LLM cloud.

## Motifs cloud versionnés

Les motifs actifs sont définis dans `config/v1/escalation_policy.yaml`.

### `deep_web_research`

- pour les rôles autorisés ;
- exige une tentative Web locale démontrée ;
- destiné à une recherche approfondie justifiée.

### `source_conflict`

- exige un conflit réel entre sources ;
- ne doit pas contourner une recherche locale incomplète.

### `context_overflow`

- uniquement si le contexte requis dépasse la capacité locale **qualifiée** ;
- une fenêtre théorique annoncée par un modèle n'est pas une preuve.

### `repeated_local_failure`

- exige des échecs locaux réels ;
- exige le nombre minimal de tentatives défini par contrat.

### `high_impact_decision`

- exige une approbation humaine.

### `independent_final_review`

- exige une approbation humaine ;
- permet une seconde opinion cloud exceptionnelle sur un livrable important.

## Interdictions

Le routeur refuse notamment :

- `web_freshness_only` ;
- la commodité ;
- la seule lenteur du local ;
- un fallback cloud silencieux ;
- l'absence de benchmark comme prétexte automatique ;
- un secret ;
- l'envoi automatique d'un document privé ;
- un modèle local hors de la flotte supportée.

## Conditions générales du cloud

Une route cloud exige :

```text
cloud_enabled
+ motif explicite et versionné
+ rôle autorisé
+ préconditions démontrées
+ budget disponible
+ approbation humaine si requise
```

Une **planification** peut vérifier le coût projeté sans modifier le ledger. Une **exécution réelle** acquiert ensuite le verrou FinOps, relit le ledger et réserve atomiquement le budget immédiatement avant de lancer OpenClaw.

## Exemple local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

La route nominale est `devstral-devops` / `devstral-small-2:24b`.

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

Lors de `--execute`, une réservation FinOps est créée avant l'appel. L'identifiant de réservation doit ensuite être utilisé pour le règlement du coût réel lorsqu'il est connu.

## FinOps

Le ledger local est append-only et tient compte :

- des coûts déjà réglés ;
- des réservations actives ;
- des limites quotidiennes ;
- des limites mensuelles ;
- des limites par projet.

Deux agents concurrents ne peuvent donc pas consommer le même budget disponible à partir d'un état périmé.

Voir `docs/FINOPS.md`.
