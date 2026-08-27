# Troubleshooting OPENCLAW_LOCAL

Ce runbook suit une règle : diagnostiquer le parcours local avant toute escalade cloud. Un problème local ne doit jamais être masqué par un fallback distant.

## Ordre de diagnostic

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw config validate --json
openclaw agents list --json
openclaw gateway status --deep --json
ollama list
```

Ensuite seulement : benchmark, E2E, inventaire et qualification.

## PowerShell ou commandes introuvables

Vérifier :

```powershell
$PSVersionTable.PSVersion
Get-Command python -ErrorAction SilentlyContinue
Get-Command ollama -ErrorAction SilentlyContinue
Get-Command openclaw -ErrorAction SilentlyContinue
$env:OPENCLAW_LOCAL_ROOT
$env:OPENCLAW_STATE_DIR
```

Après `install-core`, fermer puis rouvrir PowerShell si un ancien shell n'a pas récupéré le PATH utilisateur.

## Runtime verrouillé différent

La source de vérité est `config/v1/runtime_versions.json`.

```powershell
Get-Content .\config\v1\runtime_versions.json
python --version
ollama --version
openclaw --version
```

Le bootstrap refuse par défaut une dérive Ollama déjà installée. `-AllowRuntimeDrift` doit être un choix explicite et implique une nouvelle qualification ; il ne transforme pas une version différente en version validée.

## Ollama ne répond pas

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
ollama list
```

Puis :

```powershell
.\menu.ps1 -Action configure-local
```

Ne jamais remplacer l'URL native par `http://127.0.0.1:11434/v1` : le projet dépend de l'API Ollama native pour le tool-calling.

## Modèle absent

```powershell
ollama list
.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
```

Le benchmark ne télécharge aucun modèle implicitement. Un tag manquant doit être corrigé dans le catalogue via Pull Request s'il a réellement changé ; ne substituez pas silencieusement un autre modèle.

## OpenClaw invalide

```powershell
openclaw config file
openclaw config validate --json
openclaw doctor
```

Pour régénérer le patch géré :

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le script exécute d'abord le dry-run natif `config patch`; une configuration qui ne passe pas le schéma n'est pas appliquée.

## Gateway indisponible

```powershell
openclaw gateway status --deep --json
openclaw gateway start --json
openclaw gateway status --require-rpc --json
```

Si aucun service n'est installé :

```powershell
openclaw gateway install --runtime node --force --json
openclaw gateway start --json
```

La configuration gérée impose `gateway.mode=local` et `bind=loopback`.

## Agent absent ou mauvais workspace

```powershell
openclaw agents list --json
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action deploy-agents
.\menu.ps1 -Action configure-openclaw
```

Le projet refuse d'écraser un workspace existant sans marqueur `.openclaw-local-managed`. Si le chemin contient des données importantes, sauvegardez-le et déplacez-le manuellement avant de reprendre.

## Tool-calling en échec

Distinguer trois couches :

1. modèle Ollama répond-il à une inférence simple ?
2. `openclaw agent exec` obtient-il de vrais appels d'outils ?
3. l'agent configuré possède-t-il la permission correspondante ?

Exécuter :

```powershell
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

Pour les rôles autorisés à exécuter des commandes, `tools.exec.mode=ask` exige une approbation humaine hors allowlist. Les rôles de revue refusent explicitement `exec` et les mutations de fichiers ; ce comportement est attendu.

## Réparation après erreur d'outil en échec

Le gate E2E crée volontairement un scénario avec fichier absent. Vérifier la preuve locale :

```powershell
Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs" | Sort-Object LastWriteTime -Descending
```

Ne modifiez pas la politique de qualification pour faire passer artificiellement un modèle. Conservez l'échec comme preuve, identifiez le modèle, la version OpenClaw, Ollama et le pilote GPU, puis ouvrez une PR de correction.

## GPU Intel Arc non utilisé ou débit anormal

Commencer par l'inventaire :

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
```

Comparer : pilote, version Ollama, modèle exact, contexte demandé, TTFT et tokens/s. Ne concluez pas à une accélération GPU à partir du seul nom de la carte détectée. Les résultats de `Win32_VideoController.AdapterRAM` peuvent être approximatifs ; le profil matériel versionné reste la référence documentaire et le benchmark réel la preuve opérationnelle.

## VRAM insuffisante / contexte trop grand

Le patch OpenClaw reste volontairement à 16K avant promotion. Si 16K échoue :

- ne pas augmenter le contexte ;
- collecter le benchmark ;
- vérifier les autres processus GPU ;
- tester 8K ;
- conserver le verdict `NOT_READY` si les seuils ne sont pas atteints.

32K reste optionnel jusqu'à preuve matérielle.

## Cloud refusé

C'est le comportement normal si l'un de ces éléments manque :

```text
OPENCLAW_LOCAL_CLOUD_ENABLED=true
motif d'escalade versionné
rôle autorisé
OPENROUTER_API_KEY pour une exécution réelle
```

Planifier une route sans l'exécuter :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'test' `
  --cloud `
  --reason web_freshness
```

## Rotation de la clé OpenRouter

La clé n'est jamais écrite dans Git ni dans le renderer.

```powershell
Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
$env:OPENROUTER_API_KEY = '<nouvelle-cle>'
```

Si elle est persistée par votre propre gestionnaire de secrets, faites la rotation dans ce gestionnaire, puis redémarrez le Gateway pour que le nouveau processus récupère l'environnement.

## Sauvegarde avant maintenance

Sauvegarder au minimum l'état runtime local avant une opération destructive :

```powershell
$root = $env:OPENCLAW_LOCAL_ROOT
Copy-Item "$root\state" "$root\backup\state-$(Get-Date -Format yyyyMMdd-HHmmss)" -Recurse
```

Les workspaces gérés peuvent être régénérés depuis Git. Les données personnelles, sessions et secrets ne doivent pas être rapatriés dans le dépôt public.

## Mise à jour

1. `git pull` ;
2. lire `CHANGELOG.md` et `config/v1/runtime_versions.json` ;
3. `install-core -DryRun` ;
4. sauvegarder l'état ;
5. exécuter `install-core` ;
6. `configure-openclaw` ;
7. `verify` ;
8. `e2e` ;
9. benchmark/qualification si un runtime, modèle ou pilote a changé.

## Rollback

Le dépôt ne déclare jamais un nouveau runtime qualifié sans preuve. Si une mise à jour casse le parcours local :

1. conserver les preuves/logs ;
2. revenir au commit/tag Git connu ;
3. restaurer le lock runtime correspondant ;
4. réexécuter `install-core` et `configure-openclaw` ;
5. restaurer l'état sauvegardé seulement si le format reste compatible ;
6. refaire `verify` et `e2e`.

## Désinstallation

Arrêter et retirer le service Gateway avant de supprimer le runtime :

```powershell
openclaw gateway stop --force --json
openclaw gateway uninstall --json
```

Ensuite sauvegarder ce qui doit l'être et supprimer volontairement `<OPENCLAW_LOCAL_ROOT>`. Le dépôt n'automatise pas la suppression de l'état utilisateur afin d'éviter une perte de données silencieuse.

## Preuves à joindre à un diagnostic

Sans secrets :

- commit Git ;
- `config/v1/runtime_versions.json` ;
- dernier inventaire JSON ;
- dernier benchmark/evaluation JSON ;
- preuve E2E JSON ;
- versions OpenClaw/Ollama/Python/PowerShell ;
- pilote GPU ;
- message d'erreur exact.

Ne joignez jamais `.env`, clés API, tokens Gateway ou données privées de sessions.
