# FinOps Cloud

## Objectif

OpenRouter est une capacité d'escalade, pas le chemin nominal. La V0.2 impose un contrôle budgétaire avant l'appel cloud et journalise les coûts réellement observés lorsqu'ils sont disponibles.

Le contrat est `config/v1/budget_policy.yaml`.

## Limites V0.2

| Portée | Limite |
|---|---:|
| journée | 1,00 EUR |
| mois | 5,00 EUR |
| projet / mois | 2,00 EUR |

Ces valeurs sont des garde-fous initiaux versionnés, pas une obligation économique permanente. Toute modification doit passer par revue du contrat.

## Réservation avant appel

Avant une escalation cloud, le routeur vérifie une dépense projetée. Si le coût exact n'est pas encore connu, une réservation conservatrice de `0.25 EUR` est utilisée par défaut.

Le dépassement d'une limite produit un refus (`deny`). Il n'existe pas d'override silencieux dans la V0.2.

## Ledger

Les coûts sont enregistrés par défaut dans :

```text
<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl
```

Ce fichier reste hors Git.

Chaque entrée peut contenir :

- timestamp ;
- rôle ;
- modèle ;
- motif d'escalade ;
- projet ;
- coût EUR.

## Enregistrement d'un coût observé

```powershell
python .\scripts\30_record_cloud_cost.py `
  --role expert-recherche `
  --model perplexity/sonar-pro-search `
  --reason deep_web_research `
  --project-id p5-devops `
  --cost-eur 0.08
```

Le script refuse lui-même l'enregistrement si la nouvelle dépense dépasserait les limites applicables.

## Routage avec réservation

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Recherche approfondie après échec local.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops `
  --proposed-cost-eur 0.10
```

L'exécution réelle nécessite en plus le secret OpenRouter local. Le secret ne doit jamais apparaître dans Git, les logs ou les preuves publiables.

## Principes

- cloud désactivé par défaut ;
- raison explicite obligatoire ;
- budget validé avant appel ;
- coût attribuable à un rôle et idéalement à un projet ;
- pas de fallback payant invisible ;
- pas de dépense uniquement parce que le local est plus lent.
