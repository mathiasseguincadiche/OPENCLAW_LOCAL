# Guide utilisateur OPENCLAW_LOCAL

Ce répertoire est le **mode d'emploi opérationnel** de la plateforme. Il répond d'abord à la question : **« qu'est-ce que je veux obtenir et comment dois-je m'y prendre ? »**. Il fait partie du même parcours documentaire que le reste du projet.

Il n'existe pas de guide séparé selon le niveau du lecteur : une personne qui débute et une personne expérimentée utilisent les mêmes documents. La profondeur augmente progressivement selon l'étape atteinte.

Commencez par le **[Parcours de lecture unique](../PARCOURS_LECTURE.md)** si vous découvrez le projet.

## Ordre du guide

```text
00_DEMARRER
   ↓
01_METHODE_DE_TRAVAIL
   ↓
02_AGENTS
   ↓
03_PARCOURS_PRATIQUES
   ↓
04_WORKFLOW_PROJET
   ↓
05_GERER_UN_PROJET
   ↓
06_RECETTES_ET_MODELES
   ↓
07_DIAGNOSTIC
   ↓
08_REFERENCE_RAPIDE
```

Vous pouvez revenir vers une section précédente à tout moment, mais aucune partie n'est réservée à un public particulier.

## Contrat d'utilisation

Pour chaque démarche :

```text
COMPRENDRE L'OBJECTIF
→ VÉRIFIER LES PRÉREQUIS
→ EXÉCUTER L'ACTION
→ OBSERVER LE RÉSULTAT ATTENDU
→ TROUVER LA PREUVE / VALIDATION
→ GO si conforme
→ STOP + DIAGNOSTIC sinon
→ CONTINUER / APPROFONDIR
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

Dans ces cas, utilisez `07_DIAGNOSTIC/` et la documentation associée avant de reprendre.

## Choisir quoi faire

| Besoin | Section |
|---|---|
| comprendre les repères | `00_DEMARRER/` |
| savoir comment aborder un travail | `01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md` |
| choisir un rôle | `02_AGENTS/README.md` |
| accomplir une tâche concrète | `03_PARCOURS_PRATIQUES/` |
| comprendre une étape du workflow | `04_WORKFLOW_PROJET/` |
| gérer un projet dans le temps | `05_GERER_UN_PROJET/` |
| copier un modèle de demande | `06_RECETTES_ET_MODELES/` |
| diagnostiquer un blocage | `07_DIAGNOSTIC/` |
| retrouver vite une commande ou un statut | `08_REFERENCE_RAPIDE/` |

## Arbre de décision opérationnel

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
→ collecter état / log / preuve
→ 07_DIAGNOSTIC/
→ corriger la cause
→ reprendre à l'étape documentée
```

## Quel agent ?

- je ne sais pas par où commencer → `chef-operations`
- recherche factuelle/récente → `expert-recherche`
- conception/architecture → `architecte-solutions`
- CI/CD, infra, scripts, code Ops → `ingenieur-devops`
- risques/hardening → `ingenieur-securite`
- Git/PR/release/package → `ingenieur-release-forges`
- documentation → `redacteur-technique`
- contrôle indépendant → `auditeur-qualite`

Ces rôles sont des responsabilités techniques de la plateforme, pas des catégories de lecteurs.

## À lire ensuite

Suivez simplement le [Parcours de lecture unique](../PARCOURS_LECTURE.md) pour passer de l'utilisation à l'architecture, puis aux contrats, preuves, qualification et mécanismes DevOps.

Références utiles en cas de besoin immédiat :

- [Opérations](../OPERATIONS.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
- [Architecture](../ARCHITECTURE.md)
