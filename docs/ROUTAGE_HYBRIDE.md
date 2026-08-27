# Routage hybride

## Intention

Le local traite le parcours nominal. Le cloud n'est pas un fallback technique : c'est une **escalade explicite** soumise à politique, preuve et budget.

```text
LOCAL_PRIMARY / FAST
        ↓ si rôle spécialisé et modèle qualifié
LOCAL_SPECIALIST
        ↓ si besoin de profondeur et modèle qualifié
LOCAL_DEEP
        ↓ si besoin maximal et modèle qualifié
LOCAL_MAX
        ↓ seulement si besoin démontré
CLOUD_ESCALATION
```

La recherche d'informations récentes suit un chemin parallèle **LOCAL + WEB** et ne justifie pas à elle seule un appel LLM cloud.

## Sélection automatique du meilleur tier qualifié

Chaque rôle possède un `default_preferred_tier` dans `config/v1/model_routing.yaml`. Un modèle optionnel n'est sélectionné automatiquement que si son alias figure dans `OPENCLAW_LOCAL_QUALIFIED_MODELS`.

Si le tier préféré n'est pas qualifié, le routeur retombe fail-safe sur le `local_primary` requis. Il ne saute jamais automatiquement vers le cloud.

Flotte de référence août 2026 :

```text
Chef opérations       -> Qwen3.8 27B max, sinon Qwen3.5 9B
Expert recherche      -> Qwen3.8 27B max, sinon Qwen3.5 9B
Architecte            -> Gemma 4 26B deep, sinon Gemma 4 12B
DevOps                 -> Devstral Small 2 24B spécialiste, sinon Qwen3.5 9B
Sécurité               -> Qwen3.8 27B max, sinon Qwen3.5 9B
Release/Forges         -> Qwen3.5 9B
Rédacteur              -> Gemma 4 26B deep, sinon Gemma 4 12B
Auditeur               -> Gemma 4 26B deep, sinon Gemma 4 12B
```

## Indépendance de l'Auditeur

L'Auditeur doit utiliser une famille différente de celle du producteur lorsque cela est praticable. Sa famille nominale est Gemma. Si un livrable a été produit par Gemma, le routeur peut utiliser une alternative Qwen :

- `qwen-max` si qualifié ;
- sinon `qwen-general`, qui reste requis.

Le paramètre `producer_model_alias` permet au routeur de vérifier cette séparation explicitement.

## Tiers explicites de diagnostic

`scripts/27_route_openclaw.py` expose :

```text
--specialist-available
--deep-local-available
--max-local-available
--producer-model-alias
```

Ces options servent aux tests/diagnostics opérateur. Une seule route locale explicite peut être forcée à la fois. Le parcours nominal s'appuie plutôt sur la qualification runtime.

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
- la promotion automatique d'un modèle lourd non qualifié.

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

## Exemple : activation locale après qualification

```powershell
$env:OPENCLAW_LOCAL_QUALIFIED_MODELS = 'qwen-max,gemma-deep,devstral-devops'

python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce dépôt et propose la correction.'
```

Le DevOps choisit alors son spécialiste qualifié. Sans cette qualification, il revient à Qwen3.5 9B.

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
