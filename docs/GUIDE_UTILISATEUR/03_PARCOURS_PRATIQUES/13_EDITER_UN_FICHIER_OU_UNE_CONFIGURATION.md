# Éditer un fichier ou une configuration

## Quand utiliser cette procédure

Modification ciblée d'un script, YAML, JSON, fichier de configuration, pipeline, manifest, documentation ou code.

## Méthode

1. **Définir l'effet recherché** : ce qui doit changer dans le comportement, pas seulement la ligne à modifier.
2. **Lire le contexte** : fichier complet ou section suffisante, fichiers liés, conventions du dépôt.
3. **Préserver les contraintes** : format, indentation, schéma, compatibilité, secrets, permissions.
4. **Demander un diff minimal** : éviter les refactorisations sans rapport.
5. **Valider la syntaxe** : parseur/linter adapté.
6. **Valider le comportement** : test ou commande qui démontre l'effet recherché.
7. **Vérifier les régressions** : tests du composant ou CI.
8. **Conserver la preuve** : diff + commandes + résultats.

## Exemple de mission

```text
Modifie uniquement la configuration nécessaire pour activer <fonction>. Préserve les clés existantes, ne change pas les versions. Avant modification, vérifie le schéma attendu. Après modification, parse le fichier puis exécute le test de contrat concerné. Fournis le diff et les résultats.
```

## Règle

Une modification de texte qui « a l'air correcte » n'est pas une validation. La preuve dépend du type de fichier et de son usage réel.