# Répondre à une clarification

## Étapes

1. lire `status` ;
2. retrouver la question exacte ;
3. décider ce qui doit être tranché ;
4. répondre sans ambiguïté ;
5. relancer le workflow.

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action resolve --clarification-id <clarification-id> --answer "Utiliser le backend local prévu, sans cloud."
```

## Bonnes pratiques

Ajouter la raison si elle influence les futures décisions. Si la clarification révèle un changement majeur de besoin, demander une replanification plutôt qu'une simple reprise aveugle.