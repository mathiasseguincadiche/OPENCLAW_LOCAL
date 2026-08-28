# Modèle de diagnostic

```text
SYMPTÔME
<ce qui se passe réellement>

RÉSULTAT ATTENDU
<ce qui devrait se passer>

DERNIÈRE ACTION
<commande/changement>

ERREUR EXACTE
<message ou log>

ENVIRONNEMENT
<OS, version, backend, namespace, etc.>

CE QUI A DÉJÀ ÉTÉ TESTÉ
- <test + résultat>

CONTRAINTES
<ne pas supprimer, ne pas modifier X, etc.>

DEMANDE
1. localise la couche en défaut ;
2. formule l'hypothèse ;
3. propose le test le moins destructif ;
4. corrige la cause ;
5. donne la validation et le rollback.
```

Joindre le log pertinent plutôt qu'une paraphrase lorsque c'est possible.