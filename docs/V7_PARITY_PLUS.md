# Filiation V7 — `openclaw_openrouter` vers `OPENCLAW_LOCAL`

`OPENCLAW_LOCAL` est la réécriture **local-first** de l'idée portée par `openclaw_openrouter` : OpenClaw reste le runtime agentique, huit rôles spécialisés conservent leurs responsabilités, et la couche de contrôle versionnée conserve projets, preuves, sécurité, budget, validation et gouvernance.

La différence structurante est le chemin IA :

```text
openclaw_openrouter
OpenClaw → OpenRouter → modèles cloud → contrats/projets/preuves

OPENCLAW_LOCAL
OpenClaw → LOCAL_FAST → LOCAL+WEB → LOCAL_DEEP → cloud exceptionnel
          └──────────── contrats/projets/preuves/orchestration ────────────┘
```

L'objectif n'est pas de prétendre qu'un petit modèle local est individuellement supérieur à tous les modèles frontier. La plateforme cherche à obtenir un meilleur **rapport autonomie / coût / confidentialité / vérifiabilité** grâce à l'orchestration, la spécialisation, le Web local-first, les corrections, l'audit et l'escalade cloud exceptionnelle.

## Capacités V7 conservées ou renforcées

| ADN V7 | OPENCLAW_LOCAL |
| --- | --- |
| 8 rôles spécialisés | conservés, avec Project Orchestrator |
| producteur ≠ auditeur | conservé et validé par politiques |
| projets + contrats | Project Intake + machine d'états complète |
| preuves | evidence/, runs namespacés, remediation history |
| budget | FinOps cloud plus strict, cloud désactivé par défaut |
| sécurité Intake | archive canonique, secrets, symlinks, SHA-256, MIME, ACL |
| pédagogie | efficient / balanced / intensive + artefacts d'apprentissage |
| accessibilité | Comprendre / Utiliser / Approfondir / Diagnostiquer |
| publication | machine d'états GitHub/GitLab avec gates humains |
| télémétrie | métriques locales + cloud sans prompts ni contenus privés |
| architecture | writer borné pour ADR/schémas, pas de droit générique |
| sécurité | agent sécurité read-only sur les sources |

## Principe de supériorité

Une amélioration n'est acceptée que si elle ne détruit pas un garde-fou utile de V7. Les validateurs `21_validate_repository.py`, `22_validate_configs.py` et `35_validate_v7_parity.py` empêchent les régressions structurantes.

Le chemin nominal doit rester utilisable sans OpenRouter. Le cloud est un **accélérateur exceptionnel**, jamais une dépendance cachée.

## Ce qui reste à prouver sur la workstation

La parité fonctionnelle du code ne qualifie pas automatiquement les modèles locaux ni l'Intel Arc B580. Les performances, le contexte utile, la stabilité, le tool calling et la qualité sémantique sur de vrais projets restent des preuves matérielles à mesurer.
