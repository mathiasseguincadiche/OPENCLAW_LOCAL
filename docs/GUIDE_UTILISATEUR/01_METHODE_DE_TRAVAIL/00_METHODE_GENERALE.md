# Méthode générale de travail

Cette procédure s'applique à presque tout : DevOps, architecture, documentation, recherche, sécurité, correction ou nouveau projet.

## 1 — Définir

Écrire en une phrase ce qui doit être vrai à la fin.

## 2 — Préparer

Rassembler consignes, fichiers, dépôt, état actuel, erreurs, contraintes et livrables attendus. Ne fournissez pas de secrets inutiles.

## 3 — Choisir le mode

- besoin ponctuel, peu de fichiers, pas de dépendances → agent direct ;
- travail structuré, plusieurs étapes/fichiers/rôles, besoin de preuves → projet orchestré.

## 4 — Choisir le rôle

Si le rôle n'est pas évident, commencer par `chef-operations`.

## 5 — Cadrer la mission

Toujours préciser : objectif, contexte, entrées, contraintes, livrables et critères de réussite.

## 6 — Analyser puis planifier

Ne pas confondre « commencer à produire » avec « comprendre le besoin ». Vérifier le plan, les hypothèses et les ambiguïtés.

## 7 — Exécuter

Exécuter les tâches dans l'ordre de dépendance. Une tâche doit produire un résultat contrôlable.

## 8 — Suivre

Pour un projet : consulter `status`, les tâches prêtes, les clarifications et les artefacts produits.

## 9 — Valider

Contrôler le résultat avec des tests, commandes, hashes, fichiers attendus ou autres preuves observables.

## 10 — Corriger

Réouvrir uniquement les tâches affectées. Ne pas écraser les tentatives précédentes.

## 11 — Revoir et finaliser

La revue indépendante vérifie la cohérence globale. Le package rassemble les livrables finaux.

## 12 — Approuver

`COMPLETE` reste une décision humaine.

## Critère d'un résultat « fini »

Un travail n'est pas terminé parce qu'un agent dit « terminé ». Il est terminé lorsque le livrable existe, respecte les contraintes, passe ses contrôles, possède ses preuves et a reçu l'approbation requise.