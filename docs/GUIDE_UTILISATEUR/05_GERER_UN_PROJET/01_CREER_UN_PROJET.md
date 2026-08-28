# Créer un projet

## Préparer

Un identifiant stable, un titre, les consignes, les sources et les livrables attendus.

## Exemple

```powershell
python .\scripts\28_create_project.py `
  --id mon-projet `
  --title "Mon projet" `
  --intake "C:\Travail\consignes.pdf" `
  --source "C:\Travail\repository" `
  --deliverable documentation `
  --deliverable scripts
```

## Résultat

Projet central sous `<OPENCLAW_LOCAL_ROOT>\projects\mon-projet` avec intake, sources, context, work, deliverables, evidence et diagrams.

## Vérifier

Lancer immédiatement `status` avant le premier `run`.