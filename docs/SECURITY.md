# Sécurité

## Hypothèse importante

Un modèle local compact ou fortement quantifié n'est pas une barrière de sécurité. L'absence de fournisseur cloud ne supprime pas le risque d'injection de prompt, d'abus d'outil ou d'exfiltration via un outil autorisé.

## Mesures

- backend local en loopback ;
- permissions d'outils minimales par rôle ;
- secrets hors Git et hors prompts ;
- validation humaine pour publication, fusion, suppression et opérations sensibles ;
- séparation producteur/auditeur ;
- journalisation locale des escalades ;
- refus de transmettre automatiquement des données au cloud.

## Cloud

Une clé OpenRouter éventuelle doit avoir un plafond de dépense et être stockée dans l'état runtime local, jamais dans le dépôt.
