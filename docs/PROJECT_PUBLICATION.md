# Publication des projets utilisateurs

La publication d'un projet traité par OPENCLAW_LOCAL est distincte de la release de la plateforme elle-même. Un projet peut être `COMPLETE` localement sans être publié.

## Machine d'états

```text
LOCAL_IN_PROGRESS
       ↓
LOCAL_VALIDATED
       ↓
READY_TO_PUBLISH
       ↓
REMOTE_CREATED
       ↓
BRANCH_PUSHED
       ↓
PR_MR_OPEN
       ↓
CI_GREEN
       ↓
REMOTE_CLONE_VALIDATED
       ↓
RELEASE_CREATED (optionnel)
       ↓
PUBLISHED_AND_VERIFIED
```

Depuis `REMOTE_CLONE_VALIDATED`, un projet peut aller directement à `PUBLISHED_AND_VERIFIED` si une décision explicite et documentée indique qu'aucune release n'est nécessaire.

## Gates locaux

Avant `LOCAL_VALIDATED` :

- tests locaux verts ;
- documentation validée ;
- secret scan propre ;
- dependency scan revu ;
- `git status` revu ;
- règles ignore revues ;
- chemins locaux supprimés ;
- rollback documenté ;
- audit local indépendant.

Avant publication distante, le package local doit aussi être revu.

## Gates distants

La politique exige PR/MR, CI distante, clean clone et audit distant indépendant. `PUBLISHED_AND_VERIFIED` exige en plus l'URL canonique, le SHA publié, l'approbation de merge, la décision release/no-release et l'approbation humaine finale.

Les forges supportées sont GitHub et GitLab.

## Approbations humaines

Créer un dépôt distant, changer sa visibilité, merger, publier une release, modifier la protection de branche, réécrire l'historique ou finaliser une publication restent des actions humaines explicites.

La machine d'états **enregistre les preuves** ; elle n'implique jamais qu'une action distante a réellement été effectuée.

## CLI

```powershell
python .\scripts\34_project_publication.py --project p5-devops `
  --evidence-key local_tests_green --evidence-value true

python .\scripts\34_project_publication.py --project p5-devops `
  --target LOCAL_VALIDATED --actor auditeur-qualite
```

Les transitions sensibles utilisent `--human-approved`.
