# Clôturer un projet

## Conditions

Validation et revue réussies, package final produit, preuves suffisantes, limites connues.

## Contrôle humain

Ouvrir les livrables réellement produits, pas seulement le rapport qui les décrit.

## Commande

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action complete --human-approved
```

## Après COMPLETE

Conserver `projects/`, `state/` et `proofs/` selon la politique de sauvegarde. Une publication GitHub/GitLab éventuelle suit sa propre machine d'états et ne doit pas être déduite de `COMPLETE`.