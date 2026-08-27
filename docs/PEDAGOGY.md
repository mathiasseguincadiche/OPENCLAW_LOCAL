# Pédagogie et apprentissage projet

OPENCLAW_LOCAL ne doit pas seulement produire un livrable : il doit aussi permettre à l'utilisateur de **comprendre ce qui a été fait et de pouvoir le défendre**.

La livraison reste prioritaire. La pédagogie ne doit pas bloquer un incident, une correction urgente ou un livrable déjà compris.

## Profils

| Profil | Exécution | Apprentissage | Usage |
| --- | ---: | ---: | --- |
| `efficient` | 90 % | 10 % | tâche connue, accélération |
| `balanced` | 70 % | 30 % | profil par défaut |
| `intensive` | 60 % | 40 % | formation, soutenance, évaluation |

Les modes disponibles sont `guided`, `assisted`, `autonomous` et `evaluation`.

## Artefacts

Chaque projet initialise :

```text
context/learning/
├── SKILLS_MATRIX.csv
├── LEARNING_JOURNAL.md
├── TEACH_BACK.md
├── RETENTION_PLAN.yaml
└── learning_profile.json
```

### SKILLS_MATRIX.csv

Suit une compétence uniquement lorsqu'il existe une preuve pratique. Une exposition à un concept ne suffit jamais pour le marquer `ACQUIRED`.

### LEARNING_JOURNAL.md

Conserve les apprentissages réellement utiles. Il n'est pas conçu comme un rapport quotidien obligatoire.

### TEACH_BACK.md

Aux jalons importants, l'utilisateur peut reformuler le concept, expliquer son utilité, sa limite principale et citer une preuve réellement observée.

### RETENTION_PLAN.yaml

Permet de planifier des révisions ciblées, par défaut à 7 et 30 jours, uniquement pour les compétences qui méritent d'être retenues.

## Spécialisation Ops/DevOps

Le contrat met l'accent sur Linux, Git, Bash/Python Ops, Terraform/OpenTofu, Ansible, CI/CD et conteneurs, avec Kubernetes/Helm, sécurité, observabilité, fiabilité/rollback et documentation comme compétences de soutien.
