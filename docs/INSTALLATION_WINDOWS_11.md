# Installation Windows 11

## Préconditions

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap et les trois modèles routés ;
- pilote Intel Arc à jour avant la qualification matérielle.

Python, Node.js, OpenClaw, Ollama et llama.cpp sont contrôlés par les locks versionnés du dépôt.

## Emplacement géré

Si `OPENCLAW_LOCAL_ROOT` n'est pas défini, `E:\AI\OpenClawLocal` est utilisé lorsque `E:` existe, sinon `%LOCALAPPDATA%\OpenClawLocal`.

La racine des modèles Ollama est :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Les scripts configurent `OLLAMA_MODELS` vers cette racine.

## Flotte opérationnelle installée

Les trois modèles requis et routés sont :

```text
qwen3.5:9b-q4_K_M
gemma3:12b-it-q4_K_M
qwen2.5-coder:14b-instruct-q4_K_M
```

Ils sont Q4_K_M. Le contexte nominal OPENCLAW_LOCAL est 8192 tokens ; 16384 reste réservé au stress de qualification.

## Challenger de benchmark séparé

La plateforme déclare également :

```text
ministral-3:14b-instruct-2512-q4_K_M
```

comme challenger obligatoire de `gemma-deep` pour la comparaison de sélection, notamment sur le tool-calling natif.

Ce modèle **n'est pas installé par `install-full` ni par `03_pull_models.ps1`**, car il n'appartient pas à la flotte routée. Il doit être installé explicitement avant le benchmark challenger :

```powershell
ollama pull ministral-3:14b-instruct-2512-q4_K_M
```

Sa présence locale ne modifie pas le routage OpenClaw et ne déclenche aucune promotion.

## Nouvelle installation

Depuis PowerShell 7 :

```powershell
git clone https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL.git
cd OPENCLAW_LOCAL

.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Le parcours complet :

1. installe/vérifie les runtimes verrouillés ;
2. crée le Python géré ;
3. configure la racine locale et `OLLAMA_MODELS` ;
4. démarre/vérifie Ollama ;
5. télécharge exactement les trois modèles routés ;
6. génère la configuration OpenClaw ;
7. déploie les huit workspaces agents ;
8. vérifie le Gateway et le parcours local.

## Migration d'une installation existante

```powershell
git checkout main
git pull

.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Les anciens modèles présents sur disque peuvent rester temporairement pour diagnostic, mais ils ne sont plus supportés ni routés.

## Installation des modèles routés uniquement

Dry-run :

```powershell
.\scripts\windows\03_pull_models.ps1 -DryRun
```

Réel :

```powershell
.\scripts\windows\03_pull_models.ps1
```

Le script lit `config/v1/model_catalog.yaml` et ne télécharge que les entrées de `models:` requises. Les entrées `benchmark_challengers:` sont volontairement exclues.

## Vérification locale

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le smoke minimal appelle Ollama sur loopback, utilise le Python géré pour les contrôles d'identité et affiche les métriques `/api/ps` lorsque disponibles. Il ne vaut pas qualification matérielle.

## OpenClaw

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action deploy-agents
```

Le backend nominal reste `ollama-vulkan` jusqu'à décision explicite fondée sur mesures.

Pour le profil hybride :

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
```

## Intel SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Le routeur utilise un modèle à la fois, `parallel=1`, `gpu_layers=auto` et contexte nominal 8192.

## Qualification des trois modèles routés

```powershell
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Les trois modèles sont obligatoires. Aucun PASS n'est inféré de leur seule installation.

## Comparaison obligatoire Gemma / Ministral

Après installation explicite du challenger :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Cette comparaison produit une preuve de sélection mais ne change jamais automatiquement la flotte.

## Golden Projects

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

## Désinstallation / nettoyage

Avant de supprimer des modèles :

1. vérifier les trois modèles routés ;
2. vérifier `audit`/`verify` ;
3. conserver les preuves historiques utiles ;
4. ne pas supprimer `proofs/`, les états de qualification ou les projets utilisateur ;
5. ne supprimer le challenger qu'après avoir conservé sa preuve comparative si elle a été utilisée pour une décision.
