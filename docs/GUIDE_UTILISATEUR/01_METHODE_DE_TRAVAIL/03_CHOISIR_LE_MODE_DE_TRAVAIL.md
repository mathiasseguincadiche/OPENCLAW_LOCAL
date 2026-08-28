# Choisir le mode de travail

## Agent direct

Choisissez-le pour : explication, question ciblée, diagnostic court, recherche ponctuelle, petite revue.

Exemple :

```powershell
python .\scripts\27_route_openclaw.py --agent ingenieur-devops --message "Analyse cette erreur Helm et propose les vérifications." --execute
```

## Projet orchestré

Choisissez-le si au moins un de ces critères est important : plusieurs fichiers, plusieurs livrables, plusieurs rôles, dépendances entre tâches, corrections successives, besoin d'historique ou de preuves.

## Règle simple

Si vous devez vous demander « où en sommes-nous ? », « qui fait quoi ? », « qu'est-ce qui a été validé ? » ou « quelle version est la bonne ? », utilisez un projet orchestré.