# Reprendre un projet

Après fermeture de PowerShell, redémarrage Windows ou interruption, le projet persiste.

## Routine

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

Puis, si l'état l'autorise :

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action run --execute
```

Ne recréez pas un projet portant le même objectif simplement parce qu'une session a été fermée. Reprendre l'état existant préserve le plan, les versions et les preuves.