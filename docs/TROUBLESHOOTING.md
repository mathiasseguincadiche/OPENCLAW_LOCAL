# Troubleshooting OPENCLAW_LOCAL

Ce runbook suit une règle simple : **diagnostiquer le parcours local avant toute escalade cloud**. Un défaut local ne doit jamais être masqué par un fallback distant.

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

## Variables et stockage

```powershell
$env:OPENCLAW_LOCAL_ROOT
$env:OPENCLAW_STATE_DIR
$env:OLLAMA_MODELS
```

Avec le réglage par défaut sur `E:` :

```text
E:\AI\OpenClawLocal\
├── runtime\
├── models\ollama\
├── projects\
├── workspaces\
├── state\
└── proofs\
```

Si `OLLAMA_MODELS` ne pointe pas vers `<OPENCLAW_LOCAL_ROOT>\models\ollama`, exécuter :

```powershell
.\menu.ps1 -Action configure-local
```

Le script persiste la variable et redémarre le serveur Ollama lorsqu'un changement d'emplacement l'exige.

## PowerShell ou commandes introuvables

```powershell
$PSVersionTable.PSVersion
Get-Command python -ErrorAction SilentlyContinue
Get-Command ollama -ErrorAction SilentlyContinue
Get-Command openclaw -ErrorAction SilentlyContinue
```

Après une première installation, fermer puis rouvrir PowerShell pour récupérer le PATH utilisateur.

## Runtime différent du lock

La source de vérité est `config/v1/runtime_versions.json`.

```powershell
Get-Content .\config\v1\runtime_versions.json
python --version
ollama --version
openclaw --version
```

`-AllowRuntimeDrift` est un choix explicite. Il ne transforme jamais une version différente en version qualifiée : benchmark, E2E et qualification doivent être refaits.

## Ollama ne répond pas

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
ollama list
```

Puis :

```powershell
.\menu.ps1 -Action configure-local
```

Ne pas remplacer l'URL native par `/v1` : le projet utilise l'API Ollama native.

## Modèles stockés sur le mauvais disque

1. vérifier `$env:OLLAMA_MODELS` ;
2. exécuter `configure-local` ;
3. vérifier que le serveur Ollama a été redémarré si la valeur a changé ;
4. télécharger les modèles uniquement après cette configuration :

```powershell
.\menu.ps1 -Action models
```

Ne pas déplacer manuellement un répertoire de modèles pendant qu'Ollama fonctionne.

## Modèle absent

```powershell
ollama list
.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
```

La flotte attendue contient exactement trois modèles : Qwen 3.8 27B, Gemma 4 26B et Devstral Small 2 24B. Ne pas substituer silencieusement un autre runtime.

## OpenClaw invalide

```powershell
openclaw config file
openclaw config validate --json
openclaw doctor
```

Puis :

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le patch est validé en dry-run avant application.

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

La configuration gérée impose le mode local et le bind loopback.

## Agent absent ou mauvais workspace

```powershell
openclaw agents list --json
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action deploy-agents
.\menu.ps1 -Action configure-openclaw
```

Un workspace existant sans marqueur `.openclaw-local-managed` n'est pas écrasé. Sauvegarder ou déplacer manuellement les données concernées avant de reprendre.

## Projet incohérent entre agents

Le projet central est la source de vérité. Ne pas corriger directement plusieurs workspaces.

Vérifier :

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
python .\scripts\43_project_exchange.py --project <id>
```

Puis resynchroniser si nécessaire :

```powershell
python .\scripts\31_sync_project_context.py --project <id> --agent all
```

Un changement amont validé doit être propagé via l'Artifact Exchange et les dépendances du plan, pas par copie manuelle entre agents.

## Tool-calling en échec

Distinguer :

1. Ollama répond-il à une inférence simple ?
2. OpenClaw obtient-il un vrai appel d'outil ?
3. le rôle possède-t-il l'autorisation correspondante ?

```powershell
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

`tools.exec.mode=ask` exige une approbation hors allowlist. Sécurité et Audit refusent les mutations par conception.

## Réparation après erreur d'outil en échec

Le gate E2E provoque volontairement une erreur contrôlée.

```powershell
Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs" | Sort-Object LastWriteTime -Descending
```

Conserver l'échec comme preuve. Ne pas affaiblir la politique de qualification pour le masquer.

## GPU Intel Arc non utilisé ou débit anormal

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
```

Comparer : pilote, backend, runtime exact, contexte, TTFT, tokens/s, VRAM/RAM lorsque réellement mesurées. Le nom de la carte détectée ne prouve pas l'accélération effective.

## VRAM insuffisante / contexte trop grand

Si 16K échoue :

- ne pas augmenter le contexte ;
- collecter la preuve ;
- fermer les processus GPU inutiles ;
- tester 8K ;
- conserver `NOT_READY` si les seuils requis échouent.

32K et plus restent hors qualification nominale tant qu'ils ne sont pas prouvés.

## Cloud refusé

Le refus est normal si un élément manque :

```text
OPENCLAW_LOCAL_CLOUD_ENABLED=true
motif versionné
rôle autorisé
préconditions du motif
budget disponible
OPENROUTER_API_KEY pour --execute
approbation humaine si requise
```

Une exécution réelle crée en plus une réservation FinOps atomique juste avant l'appel.

## Réservation FinOps bloquée

Vérifier le ledger :

```text
<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl
```

Une réservation active compte dans les limites. Elle est clôturée par `settlement` ou `release`, ou cesse de bloquer après son TTL. Ne pas éditer manuellement le ledger pour contourner une limite.

## Rotation de la clé OpenRouter

```powershell
Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
$env:OPENROUTER_API_KEY = '<nouvelle-cle>'
```

La clé ne doit jamais entrer dans Git, les prompts publiables ou les preuves.

## Sauvegarde avant maintenance

Sauvegarder au minimum les données non reconstruisibles :

```powershell
$root = $env:OPENCLAW_LOCAL_ROOT
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$backup = Join-Path $root "backup\$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null

foreach ($name in @('projects', 'state', 'proofs')) {
  $source = Join-Path $root $name
  if (Test-Path -LiteralPath $source) {
    Copy-Item $source (Join-Path $backup $name) -Recurse
  }
}
```

`runtime/` et `workspaces/` sont reconstruisibles. Les modèles peuvent être retéléchargés ; les sauvegarder est optionnel selon le coût de téléchargement et l'espace disponible.

## Test de restauration

Une sauvegarde doit être restaurable.

1. utiliser une copie de test ou une fenêtre de maintenance ;
2. restaurer `projects/`, `state/` et les preuves nécessaires ;
3. réparer le runtime depuis le commit/tag connu plutôt que restaurer un runtime incompatible ;
4. resynchroniser les workspaces ;
5. exécuter :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

6. vérifier un projet critique avec `--action status` et l'Artifact Exchange.

## Mise à jour

1. sauvegarder `projects/`, `state/`, `proofs/` ;
2. `git pull` ;
3. lire `CHANGELOG.md` et `runtime_versions.json` ;
4. `install-core -DryRun` ;
5. `install-core` ;
6. `configure-local` ;
7. `configure-openclaw` ;
8. `verify` ;
9. `e2e` ;
10. benchmark/qualification si runtime, modèle, backend ou pilote a changé.

## Rollback

1. conserver les logs et preuves de l'échec ;
2. revenir au commit/tag Git connu ;
3. utiliser le runtime lock correspondant ;
4. réinstaller/réparer le runtime ;
5. restaurer `state/` uniquement si le format est compatible ;
6. resynchroniser les workspaces ;
7. refaire `audit`, `verify` et `e2e`.

Ne jamais écraser les projets centraux avec un ancien snapshot de workspace.

## Désinstallation

```powershell
openclaw gateway stop --force --json
openclaw gateway uninstall --json
```

Sauvegarder ensuite les données à conserver avant de supprimer volontairement `<OPENCLAW_LOCAL_ROOT>`. La suppression de l'état utilisateur n'est pas automatisée.

## Preuves à joindre à un diagnostic

Sans secrets :

- commit Git ;
- runtime lock ;
- inventaire ;
- benchmark/evaluation ;
- preuve E2E ;
- versions OpenClaw/Ollama/Python/PowerShell ;
- pilote GPU ;
- backend ;
- message d'erreur exact.

Ne jamais joindre `.env`, clés API, tokens Gateway ou documents privés.
