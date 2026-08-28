# Workflow projet — vue d'ensemble

Le Project Orchestrator matérialise un cycle de travail contrôlé :

```text
INTAKE_READY
→ ANALYZED
→ CLARIFICATION_REQUIRED si nécessaire
→ PLANNED
→ ASSIGNED
→ IN_PROGRESS
→ VALIDATING
→ REVIEW
→ PACKAGING
→ COMPLETE
```

`VALIDATING` ou `REVIEW` peuvent renvoyer le projet vers `IN_PROGRESS`.

## Comment lire ce workflow

Chaque état répond à une question :

- avons-nous les bonnes entrées ?
- avons-nous compris ?
- manque-t-il une décision humaine ?
- avons-nous un plan ?
- les tâches ont-elles un propriétaire ?
- le travail est-il exécuté ?
- est-il techniquement correct ?
- est-il cohérent globalement ?
- les livrables sont-ils assemblés ?
- l'humain approuve-t-il la fin ?

Les fiches suivantes expliquent quoi regarder et quoi faire à chaque étape.