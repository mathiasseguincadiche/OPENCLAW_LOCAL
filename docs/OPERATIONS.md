# Opérations

## Objectif

Ce runbook couvre l'exploitation quotidienne de `OPENCLAW_LOCAL` sur Windows 11. Le principe reste : **diagnostiquer et réparer le parcours local avant toute escalade cloud**.

## Routine rapide

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Résultat attendu : runtime conforme, Ollama local, trois modèles présents, huit agents configurés, Gateway joignable.

## Racine et stockage

Afficher la racine active :

```powershell
$env:OPENCLAW_LOCAL_ROOT
$env:OLLAMA_MODELS
$env:OPENCLAW_STATE_DIR
```

Par défaut, si `E:` existe :

```text
E:\AI\OpenClawLocal\
├── runtime\
├── models\ollama\
├── projects\
├── workspaces\
├── state\
└── proofs\
    └── logs\
```

`projects/` est la source de vérité des projets. `workspaces/` contient des snapshots gérés et reconstruisibles.

## Logs opérationnels automatiques

Toute action **réelle** lancée via `menu.ps1` est journalisée automatiquement dans :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\logs\
```

Le nom est horodaté et inclut l'action :

```text
20260828_142530123_install-full.log
20260828_151004772_audit.log
20260828_151115904_verify.log
20260828_153812441_qualification.log
```

Au démarrage, le menu affiche `LOG=<chemin>`. À la fin il inscrit `ACTION_RESULT=PASS` ou `ACTION_RESULT=FAIL`, arrête le transcript puis affiche `LOG_SAVED=<chemin>`.

Lister les derniers transcripts et les emplacements des preuves structurées :

```powershell
.\menu.ps1 -Action logs
```

Afficher les 100 dernières lignes du dernier transcript :

```powershell
$latest = Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs\logs\*.log" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
Get-Content -LiteralPath $latest.FullName -Tail 100
```

Suivre ce transcript depuis une seconde console :

```powershell
Get-Content -LiteralPath $latest.FullName -Tail 50 -Wait
```

Les `-DryRun` ne créent pas de transcript afin de conserver le contrat sans mutation. `-NoLog` permet de désactiver explicitement la journalisation automatique d'une action réelle.

Les transcripts complètent les preuves structurées ; ils ne les remplacent pas :

- E2E : `<OPENCLAW_LOCAL_ROOT>\proofs\openclaw_e2e_*.json` ;
- inventaire/benchmark : `<REPO>\benchmarks\results\*.json` ;
- console de l'action : `<OPENCLAW_LOCAL_ROOT>\proofs\logs\*.log`.

Avant partage, relire le transcript et ne jamais transmettre clé API, token Gateway, `.env` ou document privé.

## Prendre en charge un projet

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --source 'C:\Projets\P5\repository' `
  --deliverable README
```

Puis :

```powershell
python .\scripts\31_sync_project_context.py `
  --project p5-devops `
  --agent all
```

Le projet central est sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\p5-devops
```

Les snapshots agents sont sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\p5-devops
```

## Exécuter un projet

Voir l'état :

```powershell
python .\scripts\32_orchestrate_project.py --project p5-devops --action status
```

Lancer le parcours :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project p5-devops `
  --action run `
  --execute
```

Le run s'arrête sur un gate humain, un échec ou une limite de tentatives. Relancer la même commande reprend l'état persistant sans effacer l'historique.

## Recherche récente

Pour une donnée actuelle :

1. utiliser `expert-recherche` ;
2. rechercher/fetcher des sources récentes ;
3. privilégier les sources officielles ;
4. faire synthétiser localement ;
5. n'envisager le cloud que si un motif autorisé reste démontré.

La simple fraîcheur n'est pas un motif d'escalade LLM cloud.

## Routage local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse le problème.'
```

La flotte supportée reste exactement :

```text
qwen-max          -> qwen3.8:27b
gemma-deep        -> gemma4:26b
devstral-devops   -> devstral-small-2:24b
```

## Cloud et FinOps

Une route cloud nécessite :

- `--cloud` ;
- un motif versionné ;
- les préconditions du motif ;
- `OPENCLAW_LOCAL_CLOUD_ENABLED=true` ;
- un budget disponible ;
- `OPENROUTER_API_KEY` pour `--execute` ;
- une approbation humaine si le motif l'impose.

### Planification

La planification peut vérifier un coût proposé sans modifier le ledger.

### Exécution réelle

Juste avant l'appel réel, le routeur :

1. acquiert le verrou FinOps ;
2. relit le ledger ;
3. tient compte des réservations actives ;
4. vérifie les limites ;
5. crée une réservation append-only ;
6. lance ensuite OpenClaw.

Après obtention du coût réel :

```powershell
python .\scripts\30_record_cloud_cost.py `
  --role expert-recherche `
  --model perplexity/sonar-pro-search `
  --reason deep_web_research `
  --project-id p5-devops `
  --reservation-id '<reservation-id>' `
  --cost-eur 0.08
```

Le ledger reste hors Git sous `<OPENCLAW_LOCAL_ROOT>\state\finops\cloud-costs.jsonl`.

## Diagrammes

```powershell
python .\scripts\29_render_diagram.py architecture.d2 architecture.svg --dry-run
python .\scripts\29_render_diagram.py architecture.d2 architecture.svg
```

## Après changement de runtime, modèle, backend ou pilote GPU

Une ancienne qualification n'est pas réutilisée automatiquement.

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification
```

## Après changement des contrats agents/routage

```powershell
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action e2e
```

## Après changement des sources d'un projet

Ne pas modifier un snapshot agent comme source de vérité. Mettre à jour le projet central via le parcours prévu puis resynchroniser. Le synchroniseur refuse d'écraser un snapshot non géré.

## Diagnostic ordonné

1. dernier transcript sous `proofs\logs` ;
2. `runtime_versions.json` et versions observées ;
3. `OPENCLAW_LOCAL_ROOT`, `OLLAMA_MODELS`, `OPENCLAW_STATE_DIR` ;
4. `model_catalog.yaml` et `ollama list` ;
5. endpoint Ollama loopback ;
6. `openclaw config validate --json` ;
7. `openclaw agents list --json` ;
8. Gateway ;
9. `verify` puis `e2e` ;
10. dernier benchmark ;
11. preuves projet/Web ;
12. seulement ensuite, si la politique le permet, envisager le cloud.

Ne jamais masquer un défaut local par un fallback cloud automatique.

## Sauvegarde

Avant maintenance, sauvegarder au minimum les données non reconstruisibles :

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

`runtime/` et `workspaces/` sont normalement reconstruisibles et ne constituent pas la sauvegarde canonique des projets.

## Restauration

1. arrêter les opérations et le Gateway si nécessaire ;
2. restaurer `projects/`, `state/` et les preuves utiles depuis un backup cohérent ;
3. ne pas restaurer un runtime ancien sur un lock incompatible ;
4. réinstaller/réparer le runtime depuis Git si nécessaire ;
5. resynchroniser les workspaces ;
6. exécuter :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

7. vérifier un projet critique avec `--action status` et les hashes/provenances attendus.

Une sauvegarde n'est considérée utile qu'après au moins un test de restauration contrôlé.

## Références

Pour les incidents détaillés, rollback, mise à jour, désinstallation, GPU, Gateway et secrets, voir `docs/TROUBLESHOOTING.md`.
