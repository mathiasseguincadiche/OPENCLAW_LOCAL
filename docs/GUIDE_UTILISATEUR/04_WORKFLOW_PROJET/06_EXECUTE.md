# EXECUTE / IN_PROGRESS

## But

Exécuter les tâches prêtes selon leurs dépendances.

## Lancer

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action run --execute
```

## Pendant l'exécution

Le système resynchronise le workspace de l'agent, inclut les versions nécessaires de ses dépendances et conserve les sorties par tentative.

## À surveiller

- tâche en échec ;
- demande de clarification ;
- preuve manquante ;
- nouvelle tentative ;
- dépendance mise à jour.

Ne modifiez pas directement les bundles d'échange pour « aider » une tâche.