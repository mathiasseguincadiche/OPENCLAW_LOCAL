# REVIEW

## But

Contrôler la cohérence globale après les validations techniques.

## Sortie

`evidence/review_report.json`.

## Différence avec VALIDATE

`VALIDATE` vérifie des critères/tâches. `REVIEW` regarde le résultat comme un ensemble : cohérence entre fichiers, consignes, documentation, architecture, sécurité et livrables.

## Si la revue échoue

Le workflow rouvre les tâches responsables et retourne vers `IN_PROGRESS`. Une nouvelle tentative doit corriger les défauts sans effacer les preuves précédentes.