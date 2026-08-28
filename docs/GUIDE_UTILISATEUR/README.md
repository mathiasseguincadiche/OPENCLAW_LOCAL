# Guide utilisateur OPENCLAW_LOCAL

Ce répertoire est le **mode d'emploi opérationnel** de la plateforme. Il répond d'abord à la question : **« qu'est-ce que je veux obtenir et comment dois-je m'y prendre ? »**

## Choisir son chemin

| Je veux… | Commencer par |
|---|---|
| comprendre le système | `00_DEMARRER/` |
| savoir comment aborder n'importe quel travail | `01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md` |
| choisir un rôle | `02_AGENTS/README.md` |
| accomplir une tâche concrète | `03_PARCOURS_PRATIQUES/` |
| comprendre une étape du workflow | `04_WORKFLOW_PROJET/` |
| gérer un projet dans le temps | `05_GERER_UN_PROJET/` |
| copier un modèle de demande | `06_RECETTES_ET_MODELES/` |
| diagnostiquer un blocage | `07_DIAGNOSTIC/` |
| retrouver vite une commande ou un statut | `08_REFERENCE_RAPIDE/` |

## Arbre de décision

```text
Besoin ponctuel ?
├─ oui → appeler directement l'agent adapté
└─ non / plusieurs étapes / plusieurs fichiers / plusieurs rôles
   → créer ou reprendre un projet orchestré
      → analyser → clarifier → planifier → exécuter
      → valider → revoir → packager → approuver
```

## Quel agent ?

- je ne sais pas par où commencer → `chef-operations`
- recherche factuelle/récente → `expert-recherche`, puis `03_PARCOURS_PRATIQUES/07_FAIRE_UNE_RECHERCHE_WEB.md` ; pour une tâche orchestrée, utiliser au besoin `06_RECETTES_ET_MODELES/08_MODELE_PREUVE_WEB.md`
- conception/architecture → `architecte-solutions`
- CI/CD, infra, scripts, code Ops → `ingenieur-devops`
- risques/hardening → `ingenieur-securite`
- Git/PR/release/package → `ingenieur-release-forges`
- documentation → `redacteur-technique`
- contrôle indépendant → `auditeur-qualite`

La documentation technique historique reste la référence de niveau 3. Ce guide explique **comment l'utiliser pour travailler**.
