# FinOps Cloud

## Objectif

OpenRouter est une capacité d'escalade, pas le chemin nominal. La V0.2 impose un contrôle budgétaire **et une réservation atomique** avant l'appel cloud réel, puis journalise le coût réellement observé lorsqu'il est disponible.

Le contrat est `config/v1/budget_policy.yaml`.

## Limites V0.2

| Portée | Limite |
|---|---:|
| journée | 1,00 EUR |
| mois | 5,00 EUR |
| projet / mois | 2,00 EUR |

Ces valeurs sont des garde-fous initiaux versionnés, pas une obligation économique permanente. Toute modification doit passer par revue du contrat.

## Réservation avant appel

Le mode planification peut vérifier une dépense projetée sans mutation. En revanche, juste avant une **exécution cloud réelle**, le routeur acquiert le verrou FinOps, relit le ledger, vérifie les limites puis écrit une réservation append-only avant de lancer le processus OpenClaw.

Si le coût exact n'est pas encore connu, une réservation conservatrice de `0.25 EUR` est utilisée par défaut. La réservation possède un identifiant et une durée de validité bornée (`reservation_ttl_seconds`, 3600 secondes par défaut).

Cette deuxième vérification atomique est volontaire : deux agents concurrents ne peuvent pas tous deux valider le même budget disponible à partir d'un état périmé.

Le dépassement d'une limite produit un refus (`deny`). Il n'existe pas d'override silencieux dans la V0.2.

## Ledger append-only

Les événements sont enregistrés par défaut dans :

```text
<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl
```

Le fichier reste hors Git. Un fichier `.lock` voisin sert uniquement à la synchronisation inter-processus locale.

Les événements pris en charge sont :

- `reservation` : budget réservé avant appel ;
- `settlement` : réservation clôturée avec le coût réellement observé ;
- `release` : réservation abandonnée sans coût ;
- `cost` : coût direct enregistré sans réservation préalable, sous contrôle budgétaire atomique.

Les anciennes lignes sans champ `event` restent interprétées comme des coûts pour préserver la compatibilité du ledger existant.

## Règlement d'une réservation

Après un appel cloud pour lequel le coût réel est connu, utiliser l'identifiant de réservation produit par le routeur :

```powershell
python .\scripts\30_record_cloud_cost.py `
  --role expert-recherche `
  --model perplexity/sonar-pro-search `
  --reason deep_web_research `
  --project-id p5-devops `
  --reservation-id '<reservation-id>' `
  --cost-eur 0.08
```

Le règlement remplace comptablement la réservation active par le coût observé. Une réservation déjà clôturée ne peut pas être réglée une deuxième fois.

Pour un coût qui n'a pas été précédé d'une réservation :

```powershell
python .\scripts\30_record_cloud_cost.py `
  --role expert-recherche `
  --model perplexity/sonar-pro-search `
  --reason deep_web_research `
  --project-id p5-devops `
  --cost-eur 0.08
```

Cette écriture directe est elle aussi effectuée sous verrou et refusée si elle dépasserait les limites, en tenant compte des réservations actives des autres agents.

## Routage avec réservation

Prévisualiser une route sans exécuter :

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

Pour une exécution réelle, ajouter `--execute` et fournir `OPENROUTER_API_KEY` dans l'environnement local. Le routeur effectue alors la réservation atomique immédiatement avant le lancement.

Le secret ne doit jamais apparaître dans Git, les logs ou les preuves publiables.

## Expiration

Une réservation non clôturée cesse de bloquer le budget après son TTL. Elle reste dans le ledger comme preuve historique, mais n'est plus comptée comme réservation active.

Un appel qui échoue avant qu'un coût fournisseur soit facturé peut utiliser `release_cloud_reservation()` côté code afin de clôturer explicitement la réservation ; sinon son TTL garantit qu'elle ne bloque pas indéfiniment les appels futurs.

## Principes

- cloud désactivé par défaut ;
- raison explicite obligatoire ;
- budget vérifié en planification puis **réservé atomiquement** avant appel réel ;
- réservations concurrentes prises en compte dans les limites ;
- coût attribuable à un rôle et idéalement à un projet ;
- ledger append-only et compatible avec les anciennes entrées ;
- pas de fallback payant invisible ;
- pas de dépense uniquement parce que le local est plus lent.
