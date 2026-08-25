# ADR-0001 — Local-first, cloud-on-demand

**Statut :** accepté

## Contexte

Une plateforme multi-agents peut multiplier les tokens et donc les coûts API. La workstation dispose d'un GPU local dédié.

## Décision

Les routes nominales sont locales. Le cloud est une escalade motivée, observable et désactivable.

## Conséquences

- coût marginal local faible ;
- dépendance accrue au benchmark matériel ;
- modèles locaux moins robustes que les modèles frontier sur certaines tâches ;
- nécessité d'une politique d'escalade explicite.
