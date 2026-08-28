# Suivre l'exécution

## Projet orchestré

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

Regardez en priorité : statut global, clarifications bloquantes, tâches prêtes/en cours/échouées, livrables déjà produits et prochaine transition autorisée.

## Où regarder

- `context/` : analyse, plan, assignations et décisions ;
- `work/` : travail intermédiaire ;
- `evidence/` : résultats de tâches et validations ;
- `deliverables/` : sorties finales ;
- `context/exchange/` : versions publiées entre tâches.

Ne relancez pas un workflow au hasard si le statut indique qu'une décision humaine est attendue.