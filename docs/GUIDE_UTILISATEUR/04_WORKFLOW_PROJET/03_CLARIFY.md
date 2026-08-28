# CLARIFY

## Signification

Le système ne peut pas continuer correctement sans une décision ou information humaine.

## Lire d'abord

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

Repérer l'identifiant et la question de clarification.

## Répondre

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action resolve --clarification-id <id> --answer "<votre décision>"
```

## Bonne réponse

Répondre à la question précise, ajouter la contrainte utile et éviter de redéfinir tout le projet si ce n'est pas nécessaire.

Un arrêt ici est normal : le système préfère demander plutôt qu'inventer.