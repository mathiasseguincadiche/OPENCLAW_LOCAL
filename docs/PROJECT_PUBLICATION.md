# Publication gouvernée d'un projet utilisateur

Cette machine d'états concerne **le projet traité par OPENCLAW_LOCAL**, pas la publication de la plateforme elle-même.

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

## Checks avant publication

Avant `LOCAL_VALIDATED`, le contrat exige :

- tests locaux verts ;
- documentation validée ;
- scan de secrets propre ;
- dépendances revues ;
- `git status` revu ;
- règles d'ignore revues ;
- chemins locaux retirés ;
- rollback documenté.

## Gates humains

Les étapes créant une ressource distante, ouvrant une PR/MR, créant une release ou déclarant le projet publié exigent une approbation humaine explicite.

## Commande

```powershell
python .\scripts\33_project_publication.py `
  --project p5-devops `
  --action status
```

Enregistrer une preuve :

```powershell
python .\scripts\33_project_publication.py `
  --project p5-devops `
  --action evidence `
  --key local_tests_green `
  --value true
```

Faire avancer l'état :

```powershell
python .\scripts\33_project_publication.py `
  --project p5-devops `
  --action transition `
  --target LOCAL_VALIDATED `
  --reason 'tests et contrôles locaux validés'
```

Les preuves distantes (`remote_ci_green`, clone propre, audit indépendant, SHA publié) doivent être enregistrées avant `PUBLISHED_AND_VERIFIED`.
