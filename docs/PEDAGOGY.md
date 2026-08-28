# Pédagogie et apprentissage projet

OPENCLAW_LOCAL ne doit pas seulement produire un livrable : il doit aussi permettre à l'utilisateur de **comprendre précisément ce qui a été fait, pourquoi cela fonctionne, comment le vérifier et comment le défendre**.

La pédagogie est **transversale** : elle s'applique aux huit agents, à toutes les phases de l'orchestrateur et à tous les modèles routés. Elle n'est donc pas réservée au Rédacteur technique. Le contrat commun `agents/_shared/PEDAGOGY.md` est injecté dans le `AGENTS.md` effectif de chaque workspace avant le contrat spécifique du rôle.

Cette couche reste active avec les trois modèles locaux supportés — Qwen 3.8 27B, Gemma 4 26B et Devstral Small 2 24B — et reste attachée au rôle si une escalade cloud explicite est exceptionnellement utilisée.

La livraison reste prioritaire. La pédagogie ne doit pas bloquer un incident, une correction urgente ou un livrable déjà compris, et elle ne doit pas transformer une tâche simple en cours inutilement long.

## Exigence de qualité

Toute production destinée à un humain doit viser simultanément :

- exactitude technique ;
- compréhension accessible à un débutant ;
- prérequis et vocabulaire explicites ;
- résultat attendu et validation objective ;
- risques, limites et rollback lorsque pertinents ;
- profondeur technique suffisante pour un utilisateur avancé ;
- ton professionnel, jamais infantilisant ;
- absence de fausse simplification.

L'objectif n'est pas de supprimer la complexité réelle, mais de la rendre progressive et compréhensible.

## Profondeurs progressives

Lorsque le sujet le justifie, la documentation et les explications suivent quatre profondeurs :

1. **Comprendre** — objectif, contexte, problème résolu, vocabulaire essentiel, risques principaux et résultat attendu ;
2. **Utiliser** — prérequis, droits, procédure, résultats attendus, validation, preuves et rollback ;
3. **Approfondir** — architecture, mécanismes, décisions, compromis, sécurité, limites et sources de vérité ;
4. **Diagnostiquer** — symptômes, vérifications, erreurs fréquentes, conditions d'arrêt, récupération et preuves.

Ces profondeurs ne doivent pas forcément apparaître comme quatre sections dans chaque réponse. L'agent les applique proportionnellement au besoin.

## Responsabilité des huit agents

| Agent | Responsabilité pédagogique principale |
| --- | --- |
| Chef des opérations | objectifs, prérequis, critères de compréhension, dépendances, critères de fin |
| Expert recherche | définitions, mécanismes, limites, sources, niveau de confiance |
| Architecte solutions | choix, alternatives, compromis, complexité utile, réversibilité |
| Ingénieur DevOps | commandes, effets, résultats attendus, preuves, rollback, diagnostic |
| Ingénieur sécurité | risques, scénarios, contrôles, limites, risque résiduel |
| Release / Forges | état de publication, Git/CI/versionnement, preuves distantes, rollback |
| Rédacteur technique | documentation progressive canonique et fidèle techniquement |
| Auditeur qualité | compréhension, actionnabilité, prérequis, fidélité et profondeur suffisante |

L'Auditeur doit signaler un livrable techniquement correct mais incompréhensible, non actionnable ou trompeusement simplifié.

## Profils

| Profil | Exécution | Apprentissage | Usage |
| --- | ---: | ---: | --- |
| `efficient` | 90 % | 10 % | tâche connue, accélération |
| `balanced` | 70 % | 30 % | profil par défaut |
| `intensive` | 60 % | 40 % | formation, soutenance, évaluation |

Les modes disponibles sont `guided`, `assisted`, `autonomous` et `evaluation`.

Le profil sélectionné ne désactive jamais l'exigence de clarté et d'exactitude ; il règle l'intensité de l'accompagnement et des objectifs d'apprentissage.

## Artefacts

Chaque projet initialise :

```text
context/learning/
├── LEARNING_CONTRACT.json
├── SKILLS_MATRIX.csv
├── LEARNING_JOURNAL.md
├── TEACH_BACK.md
├── RETENTION_PLAN.yaml
├── learning_profile.json
└── evaluations/

context/documentation_profile.json
```

Ces fichiers sont copiés avec `context/` dans les snapshots des huit agents. Chaque agent peut donc adapter son accompagnement au profil du projet sans dépendre d'une mémoire implicite.

### LEARNING_CONTRACT.json

Décrit le profil, le mode, les objectifs, les compétences ciblées, les preuves et le verdict d'apprentissage. Le verdict technique reste distinct du verdict pédagogique.

### SKILLS_MATRIX.csv

Suit une compétence uniquement lorsqu'il existe une preuve pratique. Une exposition à un concept ne suffit jamais pour le marquer `ACQUIRED`.

### LEARNING_JOURNAL.md

Conserve les apprentissages réellement utiles. Il n'est pas conçu comme un rapport quotidien obligatoire.

### TEACH_BACK.md

Aux jalons importants, l'utilisateur peut reformuler le concept, expliquer son utilité, sa limite principale et citer une preuve réellement observée.

### RETENTION_PLAN.yaml

Permet de planifier des révisions ciblées, par défaut à 7 et 30 jours, uniquement pour les compétences qui méritent d'être retenues.

## Incident et tâche routinière

Une tâche routinière doit rester efficace : l'agent exécute puis explique les éléments réellement utiles. Lors d'un incident, la correction ou la sécurisation passe d'abord si nécessaire ; le débrief pédagogique vient ensuite avec la cause, le diagnostic, la correction, la validation et la prévention.

Les quiz systématiques sont interdits et une solution directe reste autorisée lorsque l'utilisateur la demande.

## Spécialisation Ops/DevOps

Le contrat met l'accent sur Linux, Git, Bash/Python Ops, Terraform/OpenTofu, Ansible, CI/CD et conteneurs, avec Kubernetes/Helm, sécurité, observabilité, fiabilité/rollback et documentation comme compétences de soutien.

## Anti-régression

`scripts/46_validate_transversal_pedagogy.py` vérifie notamment :

- l'existence et le contenu du contrat partagé ;
- son injection dans les huit workspaces ;
- l'activation des politiques pédagogie/accessibilité ;
- les responsabilités des huit rôles ;
- la présence du contexte d'apprentissage dans les cinq phases de l'orchestrateur ;
- l'audit pédagogique en validation/revue ;
- la couverture des trois modèles locaux supportés ;
- l'exécution du gate dans CI et Release.

Le test PowerShell déploie en plus réellement les huit workspaces dans un environnement temporaire et vérifie que leur `AGENTS.md` effectif contient la couche pédagogique transversale.
