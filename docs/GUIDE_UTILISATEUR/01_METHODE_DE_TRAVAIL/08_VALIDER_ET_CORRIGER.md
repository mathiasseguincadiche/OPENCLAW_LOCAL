# Valider et corriger

## Validation

Une validation doit répondre : « quelle preuve montre que le résultat satisfait le critère ? »

Exemples : tests automatisés, commande qui retourne 0, pod `Ready`, fichier produit, hash, schéma valide, revue indépendante.

## Si cela échoue

1. conserver la preuve de l'échec ;
2. identifier la tâche responsable ;
3. identifier ses dépendants ;
4. corriger dans une nouvelle tentative ;
5. republier uniquement après `PASS` ;
6. resynchroniser les consommateurs affectés ;
7. revalider.

Les anciennes tentatives (`run-001`, `run-002`, …) restent des preuves. Ne modifiez pas un bundle d'échange en place.