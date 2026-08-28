# Consulter le status

## Commande

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

## À lire en priorité

1. statut global ;
2. clarification bloquante ;
3. tâches prêtes ou échouées ;
4. livrables attendus ;
5. prochaine action possible.

## Réflexe

Quand vous ne savez plus « où en est le projet », n'ouvrez pas tous les dossiers au hasard : commencez par `status`, puis suivez les identifiants de tâches/clarifications vers les artefacts correspondants.