# Reprendre après un échec

## Ne pas faire immédiatement

- supprimer les répertoires ;
- réinstaller tout ;
- changer de modèle/backend au hasard ;
- activer le cloud ;
- lancer dix commandes de réparation.

## Procédure

1. conserver le log ;
2. relever la dernière étape réussie ;
3. identifier la première erreur causale ;
4. vérifier l'état courant ;
5. corriger la cause minimale ;
6. relancer l'action idempotente ;
7. vérifier que l'étape fautive passe ;
8. poursuivre jusqu'au prochain gate.

Le bootstrap et les workflows sont conçus pour réutiliser les éléments déjà conformes lorsque c'est sûr.