# Routage hybride

## Intention

Le local traite le travail courant. Le cloud n'est appelé que lorsqu'un signal d'escalade est présent et autorisé.

## Signaux possibles

- information fraîche ou vérification web requise ;
- contexte dépassant la capacité locale qualifiée ;
- échec répété d'une tâche après la limite locale ;
- décision à impact élevé ;
- désaccord entre deux familles locales ;
- audit indépendant explicitement demandé.

## Interdictions

- escalade parce que le modèle local est simplement plus lent ;
- escalade silencieuse ;
- envoi d'un secret ou d'un document privé sans politique explicite ;
- auto-approbation par le producteur.

## Budget

Le budget cloud doit être borné hors Git. L'objectif est de mesurer le taux d'escalade, le coût par rôle et la valeur réelle obtenue avant d'élargir l'usage.
