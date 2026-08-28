# Commandes — référence rapide

```powershell
# Plateforme
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action logs
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun

# Agent direct
python .\scripts\27_route_openclaw.py --agent <agent> --message "<mission>"
python .\scripts\27_route_openclaw.py --agent <agent> --message "<mission>" --execute

# Projet
python .\scripts\32_orchestrate_project.py --project <id> --action status
python .\scripts\32_orchestrate_project.py --project <id> --action run --execute
python .\scripts\32_orchestrate_project.py --project <id> --action resolve --clarification-id <id> --answer "<réponse>"
python .\scripts\32_orchestrate_project.py --project <id> --action complete --human-approved
```

Toujours vérifier les paramètres exacts dans les fiches spécialisées avant une action destructrice ou distante.