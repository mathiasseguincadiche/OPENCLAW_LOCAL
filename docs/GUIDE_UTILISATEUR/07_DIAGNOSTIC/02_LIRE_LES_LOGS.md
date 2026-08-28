# Lire les logs

## Logs menu

```powershell
.\menu.ps1 -Action logs
```

Les transcripts sont sous `<OPENCLAW_LOCAL_ROOT>\proofs\logs`.

## Lecture rapide

```powershell
$latest = Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs\logs\*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName -Tail 100
```

## Ordre de lecture

1. action et timestamp ;
2. dernière étape `OK` ;
3. premier message d'erreur ;
4. stack/commande en cause ;
5. `ACTION_RESULT`.

Les erreurs secondaires de nettoyage sont parfois une conséquence : cherchez d'abord la première cause qui a fait échouer l'action.