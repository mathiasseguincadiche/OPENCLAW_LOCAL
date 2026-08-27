# Opérations

## Routine rapide

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

## Après changement de runtime, modèle ou pilote GPU

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification
```

Aucune ancienne qualification n'est réutilisée pour déclarer conforme un runtime ou un pilote différent.

## Après changement des contrats agents/routage

```powershell
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action e2e
```

## Routage local-first

Planifier une requête sans l'exécuter :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse le problème.'
```

Le cloud ne peut être demandé qu'avec `--cloud`, un motif autorisé, l'activation explicite de `OPENCLAW_LOCAL_CLOUD_ENABLED` et, pour l'exécution, la clé OpenRouter locale.

## Diagnostic

1. vérifier le runtime dans `config/v1/runtime_versions.json` ;
2. vérifier le modèle réellement installé ;
3. vérifier Ollama en loopback ;
4. vérifier `openclaw config validate --json` ;
5. vérifier la flotte `openclaw agents list --json` ;
6. vérifier le Gateway ;
7. exécuter `verify` puis `e2e` ;
8. comparer au dernier benchmark ;
9. seulement ensuite considérer une escalade cloud.

Ne jamais masquer un défaut local par un fallback cloud automatique pendant un diagnostic.

Pour les séquences détaillées de mise à jour, rollback, sauvegarde, désinstallation, VRAM, GPU, Gateway, modèles et rotation de secrets, voir `docs/TROUBLESHOOTING.md`.
