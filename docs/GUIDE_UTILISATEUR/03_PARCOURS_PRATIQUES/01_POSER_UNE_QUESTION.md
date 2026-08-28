# Poser une question ponctuelle

## Quand

Besoin limité qui ne nécessite ni plan multi-étapes ni historique projet.

## Étapes

1. choisir l'agent ;
2. formuler objectif + contexte + contrainte ;
3. prévisualiser le routage ;
4. exécuter ;
5. vérifier la réponse et les limites.

```powershell
python .\scripts\27_route_openclaw.py --agent chef-operations --message "Explique la différence entre audit et verify."
python .\scripts\27_route_openclaw.py --agent chef-operations --message "Explique la différence entre audit et verify." --execute
```

## Résultat attendu

Une réponse ciblée. Si la question se transforme en travail multi-fichiers ou durable, basculer vers un projet orchestré.