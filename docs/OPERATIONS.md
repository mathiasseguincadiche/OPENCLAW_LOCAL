# Opérations

## Routine rapide

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

## Prendre en charge un projet

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --source 'C:\Projets\P5\repository' `
  --deliverable README

python .\scripts\31_sync_project_context.py `
  --project p5-devops `
  --agent all
```

Vérifier ensuite le snapshot d'un agent sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\p5-devops
```

## Recherche récente

Pour une information actuelle :

1. utiliser l'agent `expert-recherche` local ;
2. rechercher/fetcher des sources récentes ;
3. privilégier les sources officielles ;
4. laisser le modèle local synthétiser ;
5. ne considérer le cloud que si une raison autorisée reste démontrée.

La simple fraîcheur n'est pas un motif d'escalade cloud.

## Routage local-first

Plan local :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse le problème.'
```

LOCAL_DEEP :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce problème complexe.' `
  --deep-local-available
```

Une route cloud nécessite `--cloud`, un motif versionné, les preuves/préconditions du motif, un budget disponible, l'activation explicite de `OPENCLAW_LOCAL_CLOUD_ENABLED` et, pour l'exécution, la clé OpenRouter locale.

## Contrôle FinOps

Avant un appel cloud, `scripts/27_route_openclaw.py` vérifie la dépense projetée. Après un coût observé :

```powershell
python .\scripts\30_record_cloud_cost.py `
  --role expert-recherche `
  --model perplexity/sonar-pro-search `
  --reason deep_web_research `
  --project-id p5-devops `
  --cost-eur 0.08
```

Le ledger reste hors Git.

## Diagrammes

Prévisualiser puis rendre localement :

```powershell
python .\scripts\29_render_diagram.py architecture.d2 architecture.svg --dry-run
python .\scripts\29_render_diagram.py architecture.d2 architecture.svg
```

## Après changement de runtime, modèle ou pilote GPU

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification
```

Aucune ancienne qualification n'est réutilisée pour déclarer conforme un runtime, un backend ou un pilote différent.

## Après changement des contrats agents/routage

```powershell
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action e2e
```

Après changement des sources d'un Project Intake, resynchroniser explicitement le projet. Le synchroniseur refuse d'écraser un snapshot non géré.

## Diagnostic

1. vérifier les versions dans `runtime_versions.json` ;
2. vérifier `model_catalog.yaml` et les modèles réellement installés ;
3. vérifier le backend local et son endpoint loopback ;
4. vérifier `openclaw config validate --json` ;
5. vérifier la flotte `openclaw agents list --json` ;
6. vérifier le Gateway ;
7. exécuter `verify` puis `e2e` ;
8. comparer au dernier benchmark `devops-v2` ;
9. vérifier les preuves Web/locales ;
10. seulement ensuite considérer une escalade cloud.

Ne jamais masquer un défaut local par un fallback cloud automatique pendant un diagnostic.

Pour rollback, sauvegarde, désinstallation, VRAM, Gateway et rotation de secrets, voir `docs/TROUBLESHOOTING.md`.
