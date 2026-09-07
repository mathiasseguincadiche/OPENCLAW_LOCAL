# Opérations

## Objectif

Ce runbook couvre l'exploitation quotidienne de `OPENCLAW_LOCAL` sur Windows 11. Le principe V2 est : **diagnostiquer et réparer le parcours local, sans escalade vers un modèle LLM cloud**.

## Routine rapide

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Résultat attendu : runtime conforme, Ollama local, exactement trois modèles routés requis, huit agents configurés et Gateway joignable.

## Flotte active V2

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

`devstral-devops` reste l'alias du spécialiste DevOps ; son runtime V2 est Ministral 3 14B Reasoning. Granite 4.2 8B est un challenger local séparé et non routé.

Le benchmark nominal reste 8192 tokens. Le full-agent OpenClaw nominal utilise 16384 tokens afin d'absorber le système, les outils et la réserve. Ces deux contrats ne doivent pas être confondus et aucune promotion 32K n'est automatique.

## Racine et stockage

Afficher les variables actives :

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

`projects/` est la source de vérité. `workspaces/` contient des snapshots gérés et reconstruisibles.

## Installation ou migration de flotte

Après mise à jour de Git :

```powershell
.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

`models` lit directement `config/v1/model_catalog.yaml`. Le challenger Granite n'est jamais téléchargé ou promu comme modèle routé implicitement.

Une ancienne identité qualifiée devient invalide dès qu'un runtime/digest ne correspond plus à la flotte active. Ne recopier aucun hash d'une ancienne qualification vers la nouvelle.

## Logs opérationnels

Toute action réelle via `menu.ps1` est journalisée sous :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\logs\
```

Lister les derniers transcripts :

```powershell
.\menu.ps1 -Action logs
```

Afficher la fin du dernier log :

```powershell
$latest = Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs\logs\*.log" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
Get-Content -LiteralPath $latest.FullName -Tail 100
```

Les transcripts complètent les preuves structurées ; ils ne les remplacent pas. Avant partage, retirer tout secret, token, `.env` ou document privé.

## E2E après changement de modèle ou backend

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le E2E doit prouver :

- huit agents ;
- provider et modèle attendus ;
- Gateway réellement utilisé ;
- tool-calling du spécialiste DevOps ;
- réparation après erreur d'outil ;
- stabilité des répétitions prévues ;
- absence de route LLM cloud.

Le spécialiste DevOps est text-only. Les PDF/images sont ingérés par les modèles multimodaux locaux Qwen/Gemma puis transmis sous forme textuelle/structurée au spécialiste.

## Qualification après migration

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

La migration V2 impose une **nouvelle qualification complète**. Les preuves historiques restent utiles pour le diagnostic mais ne qualifient ni les nouveaux runtimes ni leur backend.

Les seuils HARD-40M ne sont pas abaissés : 30 cas, dont 24 à 8K et 6 à 16K, et les trois modèles routés doivent réellement passer le protocole actif.

## Challenger Granite

Comparaison explicite :

```powershell
ollama pull granite4.2:8b-q4_K_M
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Cette comparaison ne modifie pas le routage. Toute éventuelle substitution de modèle exige une décision humaine et une PR dédiée.

## Backends Intel Arc

Chemins disponibles :

```text
ollama-vulkan    : nominal / rollback
llama-cpp-sycl   : candidat
llama-cpp-vulkan : candidat
b580-hybrid      : profil local mixte candidat
```

Cycle candidat :

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick

.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify

.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Aucun résultat historique ne doit être utilisé pour promouvoir automatiquement `b580-hybrid` avec la flotte V2.

Rollback :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
.\menu.ps1 -Action intel-sycl-stop
```

## Prendre en charge un projet

```powershell
python .\scripts\28_create_project.py `
  --id p5-devops `
  --title 'Projet P5 DevOps' `
  --intake 'C:\Projets\P5\consignes.pdf' `
  --source 'C:\Projets\P5\repository' `
  --deliverable README
```

Voir l'état puis exécuter :

```powershell
python .\scripts\32_orchestrate_project.py --project p5-devops --action status
python .\scripts\32_orchestrate_project.py --project p5-devops --action run --execute
```

Le run s'arrête sur un gate humain, un échec ou une limite de tentatives. Relancer reprend l'état persistant sans effacer l'historique.

## Routage local

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse le problème.'
```

La route nominale du rôle DevOps reste l'alias `devstral-devops`, résolu vers Ministral 3 14B Reasoning local.

Une demande `--cloud` est une erreur de politique en Architecture V2. Le routeur ne possède aucune destination LLM en ligne.

## Recherche Web

Pour une donnée actuelle : recherche/fetch Web, validation des sources, puis synthèse par le modèle local. La fraîcheur Web ne transforme jamais la requête en inférence LLM cloud.

## Après changement des contrats agents/routage

```powershell
.\menu.ps1 -Action deploy-agents -DryRun
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action e2e
```

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
10. dernier benchmark/qualification ;
11. preuves projet/Web ;
12. si le local reste en échec, corriger ou stopper : ne pas masquer la panne avec un modèle externe.

## Sauvegarde

Sauvegarder les données non reconstruisibles avant maintenance :

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

`runtime/` et `workspaces/` sont normalement reconstruisibles.

## Restauration

1. arrêter Gateway et runtimes candidats si nécessaire ;
2. restaurer `projects/`, `state/` et les `proofs/` utiles depuis un backup cohérent ;
3. ne jamais restaurer un runtime ancien sous un lock incompatible ;
4. réinstaller/réparer le runtime depuis Git ;
5. resynchroniser les workspaces ;
6. exécuter `audit`, `verify` puis `e2e` ;
7. vérifier les hashes/provenances des projets critiques.

Une sauvegarde n'est considérée utile qu'après un test de restauration contrôlé.

## Références

Pour les incidents détaillés, voir `docs/TROUBLESHOOTING.md`. Pour le protocole matériel, voir `docs/QUALIFICATION.md` et `docs/RUNTIME_BACKENDS.md`.
