# Accessibilité documentaire progressive

La documentation projet doit rester exacte techniquement tout en étant exploitable à plusieurs niveaux de lecture.

## Quatre profondeurs

```text
COMPRENDRE
   ↓
UTILISER
   ↓
APPROFONDIR
   ↓
DIAGNOSTIQUER
```

### Comprendre

Objectif, contexte, problème résolu, vocabulaire essentiel, risques principaux et résultat attendu.

### Utiliser

Prérequis, droits nécessaires, procédure, résultats attendus, validation, preuves et rollback.

### Approfondir

Architecture, décisions, compromis, sécurité, limites et références.

### Diagnostiquer

Symptômes, contrôles, erreurs courantes, conditions d'arrêt, récupération et preuves.

## Principes

- l'exactitude technique passe avant la simplification ;
- aucune simplification fausse ;
- aucun prérequis critique implicite ;
- jargon défini à la première utilisation ;
- profondeur experte conservée ;
- structure lisible et parcourable ;
- la sécurité n'est jamais affaiblie pour rendre le texte plus simple.

Chaque projet reçoit `context/documentation_profile.json`, copié ensuite dans les snapshots agents. Le Rédacteur technique produit la documentation ; l'Auditeur qualité contrôle sa fidélité et son actionnabilité.
