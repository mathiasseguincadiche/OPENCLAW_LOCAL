# Modèle de modification ciblée

```text
FICHIER(S)
<chemins>

EFFET RECHERCHÉ
<changement de comportement attendu>

ÉTAT ACTUEL
<ce qui existe aujourd'hui>

CONTRAINTES
- conserver <...>
- ne pas modifier <...>
- compatibilité <...>

MÉTHODE
1. lis le contexte nécessaire ;
2. explique la cause ou le besoin ;
3. propose le changement minimal ;
4. applique uniquement les fichiers nécessaires ;
5. lance le parseur/linter adapté ;
6. exécute le test fonctionnel ou contrat ;
7. montre le diff et les preuves.

ROLLBACK
<comment revenir à l'état précédent>
```

Utiliser avec l'agent spécialisé dans la surface modifiée.