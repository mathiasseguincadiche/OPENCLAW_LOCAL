# Comprendre les preuves

Une preuve est une donnée observable liée à un critère : sortie de test, JSON E2E, rapport de validation, hash, inventaire ou résultat de tâche.

## Questions à poser

- quelle action a produit cette preuve ?
- à quelle version/tentative correspond-elle ?
- quel critère démontre-t-elle ?
- est-elle complète et actuelle ?
- permet-elle de distinguer succès réel et simple intention ?

## Emplacements

Preuves plateforme : `<OPENCLAW_LOCAL_ROOT>\proofs`. Preuves projet : `projects\<id>\evidence`. Résultats benchmark : `<REPO>\benchmarks\results`.