# Routage hybride

## Intention

Le local traite le parcours nominal. Le cloud n'est pas un fallback technique : c'est une **escalade explicite** soumise à politique, preuve et budget.

```text
LOCAL_FAST
   ↓ si besoin
LOCAL_DEEP / spécialiste local
   ↓ si besoin démontré
CLOUD_ESCALATION
```

La recherche d'informations récentes suit un chemin parallèle **LOCAL + WEB** et ne justifie pas à elle seule un appel LLM cloud.

## Parcours local

Sans demande cloud, `clawlocal.routing.select_route()` choisit :

1. `local_specialist` si le rôle en possède un et que sa disponibilité qualifiée est déclarée ;
2. `local_deep` si le rôle en possède un et qu'il est explicitement disponible ;
3. sinon `local_primary`.

Les fallbacks persistants configurés dans OpenClaw restent exclusivement locaux.

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
- un modèle local seulement plus lent ;
- la commodité ;
- un fallback silencieux ;
- l'absence de benchmark local comme prétexte automatique au cloud ;
- l'envoi d'un secret ;
- l'envoi automatique d'un document privé.

## Conditions générales

Toute route cloud exige au minimum :

```text
cloud_enabled
+ explicit_reason
+ budget_ok
+ préconditions du motif
+ approbation humaine si le motif l'exige
```

Le script `scripts/27_route_openclaw.py` applique ces règles avant de construire la commande OpenClaw.

## Exemple : recherche approfondie

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
