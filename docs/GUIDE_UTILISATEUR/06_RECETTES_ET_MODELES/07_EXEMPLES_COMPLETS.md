# Exemples complets

## Exemple 1 — correction Kubernetes

Objectif : rétablir la résolution DNS PostgreSQL sans toucher au code métier. Entrées : manifests/Helm, `kubectl get all`, événements et logs. Agent principal : DevOps. Validation : pods Ready, DNS résolu, requête applicative fonctionnelle. Review : qualité, puis sécurité si le changement touche NetworkPolicy/RBAC.

## Exemple 2 — nouveau runbook

Objectif : produire une procédure de reprise après panne. Entrées : scripts réels, chemins de sauvegarde, logs. Agent principal : Rédacteur. Validation : chaque commande correspond au dépôt et le runbook contient résultat attendu + rollback.

## Exemple 3 — choix d'architecture

Objectif : choisir entre deux backends. Architecte compare critères mesurables ; DevOps vérifie faisabilité ; Sécurité contrôle les risques ; Auditeur vérifie que la recommandation découle bien des critères.