# Learning & Accessibility

OPENCLAW_LOCAL doit pouvoir **livrer le projet** tout en aidant l'utilisateur à le comprendre et à le défendre. La pédagogie reste donc intégrée au contexte, sans transformer chaque tâche en cours ou en quiz.

## Profils pédagogiques

| Profil | Exécution | Apprentissage | Usage |
|---|---:|---:|---|
| `efficient` | 90 % | 10 % | tâche connue, priorité livraison |
| `balanced` | 70 % | 30 % | profil par défaut |
| `intensive` | 60 % | 40 % | formation, soutenance, évaluation |

Le profil est créé dans `context/learning/profile.json` et résumé dans `context/PROJECT_GUIDANCE.md`, que les agents doivent lire lorsqu'il existe.

## Artefacts d'apprentissage

```text
context/learning/
├── profile.json
├── SKILLS_MATRIX.csv
├── LEARNING_JOURNAL.md
├── TEACH_BACK.md
└── RETENTION_PLAN.yaml
```

Une simple exposition à une technologie ne peut jamais produire le statut `ACQUIRED`. Ce statut exige une validation humaine ou une preuve d'évaluation explicite.

## Domaines prioritaires

Le contrat cible principalement Linux, Git, Bash/Python Ops, Terraform/OpenTofu, Ansible, CI/CD et conteneurs ; réseau, Kubernetes/Helm, sécurité, observabilité, fiabilité/rollback et documentation restent des compétences de support.

## Documentation progressive

Les documents explicatifs utilisent, lorsque pertinent, quatre profondeurs :

1. **Comprendre** — but, contexte, vocabulaire, risques, résultat attendu ;
2. **Utiliser** — prérequis, procédure, validation, preuves et rollback ;
3. **Approfondir** — architecture, compromis, sécurité, limites et références ;
4. **Diagnostiquer** — symptômes, contrôles, erreurs, récupération et preuves.

Un format de livrable imposé reste prioritaire. L'accessibilité ne doit jamais simplifier faussement un risque, une commande ou un prérequis critique.

## CLI

```powershell
python .\scripts\33_project_learning.py --project p5-devops --profile intensive
python .\scripts\33_project_learning.py --project p5-devops `
  --skill terraform --status VALIDATED --evidence evidence/terraform-validation.txt
```

`ACQUIRED` exige en plus `--human-validated`.
