# Ingénieur DevOps

## Quand l'utiliser

CI/CD, Docker, Kubernetes, Helm, Terraform, Ansible, scripts PowerShell/Bash, GitOps, observabilité et diagnostic d'infrastructure.

## À lui fournir

Fichiers concernés, état actuel, erreur exacte, environnement, contraintes, résultat attendu et commande/test de validation.

## Bon cadrage

```text
Objectif : corriger le déploiement p4-dev.
Contexte : Helm + Kubernetes + PostgreSQL.
Symptôme : le backend ne résout pas le service PostgreSQL.
Contrainte : ne pas modifier le code Java.
Résultat : correction infra + explication + commandes de validation.
Validation : pods Ready et DNS fonctionnel.
```

## Ne pas l'utiliser pour

Inventer des exigences métier ou approuver seul la sécurité et la qualité finale.