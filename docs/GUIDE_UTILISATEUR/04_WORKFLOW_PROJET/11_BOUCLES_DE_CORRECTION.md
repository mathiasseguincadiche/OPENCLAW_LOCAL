# Boucles de correction

## Cas normal

```text
VALIDATING/REVIEW
      ↓ FAIL
IN_PROGRESS
      ↓ nouvelle tentative
VALIDATING/REVIEW
```

## Ce que le système conserve

Chaque tentative possède sa propre version (`run-001`, `run-002`, …), sa provenance et ses hashes.

## Propagation

Un résultat n'est publié vers les dépendants qu'après `PASS`. Si une nouvelle version d'une tâche change, seuls les consommateurs directs/transitifs affectés doivent être resynchronisés et rejoués.

## Règle utilisateur

Ne demandez pas de « repartir de zéro » à chaque échec. Utilisez le rapport de validation pour corriger la cause précise et conserver l'historique.