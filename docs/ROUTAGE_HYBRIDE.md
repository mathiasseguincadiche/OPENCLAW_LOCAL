# Routage hybride

## Intention

Le local traite le parcours nominal. Le cloud n'est pas un fallback technique : c'est une **escalade explicite** soumise à politique, preuve et budget.

La flotte locale est performance-only : toutes les routes locales doivent rester dans cet ensemble fermé :

```text
qwen-max          -> qwen3.8:27b
gemma-deep        -> gemma4:26b
devstral-devops   -> devstral-small-2:24b
```

Aucun quatrième modèle local n'est supporté.

## Routage nominal

```text
Chef opérations       -> Qwen 3.8 27B
Expert recherche      -> Qwen 3.8 27B + Web
Architecte solutions  -> Gemma 4 26B
Ingénieur DevOps      -> Devstral Small 2 24B
Ingénieur sécurité    -> Qwen 3.8 27B
Release/Forges        -> Qwen 3.8 27B
Rédacteur technique   -> Gemma 4 26B
Auditeur qualité      -> Gemma 4 26B
```

Les champs de tier `local_specialist`, `local_deep` et `local_max` restent présents pour exprimer la spécialité d'un rôle et pour les diagnostics, mais ils ne donnent jamais accès à un modèle hors de la flotte supportée.

La recherche d'informations récentes suit un chemin parallèle **LOCAL + WEB** et ne justifie pas à elle seule un appel LLM cloud.

## Fallback local

Le fallback local reste lui aussi performance-only :

- rôles Qwen -> Gemma 4 26B lorsque pertinent ;
- rôles Gemma -> Qwen 3.8 27B ;
- DevOps -> Qwen 3.8 27B si Devstral est indisponible ;
- aucune indisponibilité locale ne déclenche automatiquement OpenRouter.

## Indépendance de l'Auditeur

L'Auditeur utilise Gemma 4 26B nominalement. Si le producteur est de famille Gemma, le routeur sélectionne **Qwen 3.8 27B** comme revue indépendante lorsque cela est praticable.

Le paramètre `producer_model_alias` permet au routeur de vérifier explicitement cette séparation de famille.

## Tiers explicites de diagnostic

`scripts/27_route_openclaw.py` expose :

```text
--specialist-available
--deep-local-available
--max-local-available
--producer-model-alias
```

Ces options servent aux tests et diagnostics opérateur. Elles ne permettent pas de contourner le catalogue : toute route locale doit résoudre l'un des trois alias supportés.

## Motifs cloud versionnés

Les motifs actifs sont définis dans `config/v1/escalation_policy.yaml`.

### `deep_web_research`

- rôles : `expert-recherche`, `chef-operations` ;
- exige une tentative Web locale démontrée ;
- route préférée : recherche cloud.

### `source_conflict`

- rôles : `expert-recherche`, `chef-operations` ;
- exige un conflit réel entre sources Web ;
- route préférée : recherche cloud.

### `context_overflow`

- réservé aux rôles techniques autorisés ;
- utilisé lorsque le contexte requis dépasse la capacité locale **qualifiée**, pas simplement la capacité annoncée par le modèle.

### `repeated_local_failure`

- nécessite une preuve d'échec local ;
- nécessite au moins le nombre de tentatives locales prévu par le contrat.

### `high_impact_decision`

- exige une approbation humaine.

### `independent_final_review`

- exige une approbation humaine ;
- permet une seconde opinion frontier sur un livrable important.

## Interdictions explicites

Le routeur ne doit jamais accepter :

- `web_freshness_only` ;
- un modèle local seulement plus lent comme motif de cloud ;
- la commodité ;
- un fallback silencieux ;
- l'absence de benchmark local comme prétexte automatique au cloud ;
- l'envoi d'un secret ;
- l'envoi automatique d'un document privé ;
- un modèle local absent de la flotte performance-only.

## Conditions générales du cloud

Toute route cloud exige au minimum :

```text
cloud_enabled
+ explicit_reason
+ budget_ok
+ préconditions du motif
+ approbation humaine si le motif l'exige
```

Le script `scripts/27_route_openclaw.py` applique ces règles avant de construire la commande OpenClaw.

## Exemple : DevOps local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

La route nominale est `devstral-devops` / `devstral-small-2:24b`. Si un fallback local est nécessaire, il reste dans les trois modèles supportés.

## Exemple : recherche approfondie cloud explicite

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'

python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis la recherche.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops
```

Sans `--local-web-attempted`, la route est refusée.

## Budget et traçabilité

Le contrôle FinOps est défini dans `budget_policy.yaml`. Le routeur vérifie une dépense projetée avant l'appel. Les coûts observés peuvent ensuite être enregistrés dans le ledger local avec `scripts/30_record_cloud_cost.py`.

Voir `docs/FINOPS.md`.
