# Accessibilité documentaire progressive

La documentation projet doit rester exacte techniquement tout en étant compréhensible par une personne qui part de zéro.

Le principe n'est pas de créer plusieurs parcours selon le niveau du lecteur. Il existe **un seul parcours partagé**, dont la profondeur augmente progressivement.

## Progression commune

```text
COMPRENDRE
   ↓
UTILISER
   ↓
APPROFONDIR
   ↓
DIAGNOSTIQUER
```

Ces quatre profondeurs ne correspondent pas à quatre publics. Tout le monde peut parcourir les quatre, dans le même ensemble documentaire.

### Comprendre

Objectif, contexte, problème résolu, vocabulaire essentiel, risques principaux et résultat attendu.

### Utiliser

Prérequis, droits nécessaires, procédure, résultats attendus, validation, preuves et rollback.

### Approfondir

Architecture, décisions, compromis, sécurité, limites, contrats et références.

### Diagnostiquer

Symptômes, contrôles, erreurs courantes, conditions d'arrêt, récupération et preuves.

## Principes

- une seule documentation pour tous ;
- un seul parcours principal ;
- aucune zone réservée à un niveau de compétence ;
- le lecteur peut commencer sans connaître le contexte ;
- la profondeur technique augmente progressivement ;
- l'exactitude technique passe avant la simplification ;
- aucune simplification fausse ;
- aucun prérequis critique implicite ;
- jargon défini à la première utilisation lorsque nécessaire ;
- profondeur technique complète conservée ;
- structure lisible et parcourable ;
- la sécurité n'est jamais affaiblie pour rendre le texte plus simple.

L'objectif est qu'une personne qui découvre OPENCLAW_LOCAL puisse suivre l'ordre indiqué et arriver progressivement jusqu'à une vraie compréhension du fonctionnement DevOps, des contrats, des preuves et du diagnostic du projet.

Chaque projet reçoit `context/documentation_profile.json`, copié ensuite dans les snapshots agents. Le Rédacteur technique produit la documentation ; l'Auditeur qualité contrôle sa fidélité, son accessibilité et son actionnabilité.
