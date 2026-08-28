# COMPLETE

## Gate humain final

Après packaging, le système attend l'approbation humaine.

## Avant d'approuver

Lire les livrables, le rapport final, les limites et les preuves principales.

## Approuver

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action complete --human-approved
```

## Signification

`COMPLETE` signifie que le projet a terminé le workflow prévu et que l'utilisateur accepte le résultat. Cela ne signifie pas automatiquement qu'une publication distante ou une release externe a eu lieu.