# Guide utilisateur OPENCLAW_LOCAL

Ce répertoire est le **mode d'emploi opérationnel** de la plateforme. Il répond d'abord à la question : **« qu'est-ce que je veux obtenir et comment dois-je m'y prendre ? »**

Pour choisir d'abord un parcours selon votre rôle, utilisez le **[Parcours de lecture](../PARCOURS_LECTURE.md)**.

## Choisir son chemin

| Profil / besoin | Commencer par | Résultat attendu |
|---|---|---|
| **Débutant** — comprendre les repères | `00_DEMARRER/` | savoir ce que fait la plateforme et où aller ensuite |
| **Opérateur** — accomplir un travail ou exploiter la plateforme | `01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md`, puis `03_PARCOURS_PRATIQUES/` | exécuter une démarche complète avec résultat et preuve |
| **Mainteneur** — comprendre un workflow ou gérer un projet dans le temps | `04_WORKFLOW_PROJET/` puis `05_GERER_UN_PROJET/` | modifier ou reprendre sans contourner les états et contrats |
| **Expert / auditeur** — retrouver rapidement statuts, artefacts et diagnostic | `08_REFERENCE_RAPIDE/` et `07_DIAGNOSTIC/` | vérifier un état, retrouver une preuve et expliquer un STOP/FAIL |
| choisir un rôle | `02_AGENTS/README.md` | sélectionner l'agent adapté au besoin |
| copier un modèle de demande | `06_RECETTES_ET_MODELES/` | produire une entrée structurée et réutilisable |

## Contrat d'utilisation

Pour chaque démarche, appliquez ce cycle :

```text
PRÉREQUIS
→ ACTION
→ RÉSULTAT ATTENDU
→ PREUVE / VALIDATION
→ GO si conforme
→ STOP + DIAGNOSTIC sinon
```

### Résultat attendu

À la fin d'un parcours pratique, vous devez pouvoir dire :

- ce qui a été demandé ;
- quel agent ou workflow a été utilisé ;
- quel résultat a été produit ;
- quelle preuve permet de le valider ;
- quelle étape vient ensuite.

### Critère STOP

Arrêtez la progression lorsque :

- une commande ou une étape retourne `FAIL`, `NON CONFORME` ou un état inattendu ;
- une preuve obligatoire manque ;
- un prérequis n'est pas satisfait ;
- le résultat observé ne correspond pas au résultat attendu.

Dans ces cas, utilisez `07_DIAGNOSTIC/` et la documentation technique associée avant de reprendre.

### À lire ensuite

- parcours par profil : [Parcours de lecture](../PARCOURS_LECTURE.md) ;
- exploitation système : [Opérations](../OPERATIONS.md) ;
- dépannage détaillé : [Troubleshooting](../TROUBLESHOOTING.md) ;
- architecture et contrats : [Architecture](../ARCHITECTURE.md).

## Arbre de décision

```text
Besoin ponctuel ?
├─ oui → appeler directement l'agent adapté
└─ non / plusieurs étapes / plusieurs fichiers / plusieurs rôles
   → créer ou reprendre un projet orchestré
      → analyser → clarifier → planifier → exécuter
      → valider → revoir → packager → approuver
```

Si une étape échoue :

```text
STOP
→ ne pas improviser de contournement
→ collecter état/log/preuve
→ 07_DIAGNOSTIC/
→ corriger la cause
→ reprendre à l'étape documentée
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

La documentation technique de niveau 3 reste la référence pour les contrats et l'implémentation. Ce guide explique **comment l'utiliser pour travailler**, avec des points d'arrêt explicites plutôt qu'une progression implicite.
