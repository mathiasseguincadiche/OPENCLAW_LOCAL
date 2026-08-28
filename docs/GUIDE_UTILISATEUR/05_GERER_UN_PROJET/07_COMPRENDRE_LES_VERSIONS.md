# Comprendre les versions de travail

Les tentatives sont conservées : `run-001`, `run-002`, etc.

## Pourquoi

Cela permet de savoir : quelle sortie a échoué, quelle correction a été appliquée, quelle version a été validée et quelle version a été transmise aux dépendants.

## Règles

- ne pas écraser une ancienne tentative ;
- ne pas modifier un bundle d'échange après publication ;
- n'utiliser une nouvelle sortie chez les dépendants qu'après `PASS` ;
- conserver hashes et provenance.

La « dernière version » n'est pas automatiquement la « bonne version » : la version consommable est celle publiée après validation.