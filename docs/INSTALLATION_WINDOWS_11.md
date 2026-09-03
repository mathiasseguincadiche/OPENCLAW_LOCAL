# Installation Windows 11

## Préconditions

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap et les trois modèles ;
- pilote Intel Arc à jour avant la qualification matérielle.

Python, Node.js, OpenClaw, Ollama et llama.cpp sont contrôlés par les locks versionnés du dépôt.

## Emplacement géré

Si `OPENCLAW_LOCAL_ROOT` n'est pas défini :

```text
E:\AI\OpenClawLocal
```

est utilisé lorsque `E:` existe, sinon :

```text
%LOCALAPPDATA%\OpenClawLocal
```

La racine des modèles Ollama est gérée sous :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Les scripts configurent `OLLAMA_MODELS` vers cette racine afin d'éviter un cache ambigu.

## Flotte installée

Les trois modèles requis sont :

```text
qwen3.5:9b-q4_K_M
gemma3:12b-it-q4_K_M
qwen2.5-coder:14b-instruct-q4_K_M
```

Ils sont tous Q4_K_M et le contexte nominal OPENCLAW_LOCAL est 8192 tokens. Le 16384 reste réservé aux tests de qualification.

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
3. configure la racine locale ;
4. configure `OLLAMA_MODELS` ;
5. démarre/vérifie Ollama ;
6. télécharge exactement les trois modèles du catalogue ;
7. génère la configuration OpenClaw ;
8. déploie les huit workspaces agents ;
9. vérifie le Gateway et le parcours local.

## Migration d'une installation existante

Après mise à jour de `main` :

```powershell
git checkout main
git pull

.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
```

Puis :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Les anciens modèles présents sur disque peuvent rester temporairement dans le cache pour rollback/diagnostic. Ils ne sont plus supportés ni routés par le catalogue actif. Ne les supprimer qu'après validation de la nouvelle flotte si l'espace disque l'exige.

## Installation des modèles uniquement

Dry-run :

```powershell
.\scripts\windows\03_pull_models.ps1 -DryRun
```

Réel :

```powershell
.\scripts\windows\03_pull_models.ps1
```

Le script lit `config/v1/model_catalog.yaml`. Il ne doit pas contenir une liste parallèle de modèles codée en dur.

## Vérification locale

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le smoke minimal doit :

- appeler Ollama sur loopback ;
- vérifier qu'un modèle requis répond ;
- utiliser le Python géré pour les contrôles d'identité ;
- afficher les métriques `/api/ps` lorsque disponibles ;
- ne jamais déclarer une qualification matérielle à partir du smoke seul.

## OpenClaw

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action deploy-agents
```

Le backend nominal reste `ollama-vulkan` jusqu'à promotion explicite d'un candidat mesuré.

Pour le profil hybride :

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
```

Ce profil est candidat et réversible ; il ne doit pas être activé automatiquement à partir d'un benchmark.

## Intel SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Le routeur utilise un modèle à la fois, `parallel=1`, `gpu_layers=auto` et contexte nominal 8192. Les trois runtimes sont comparés autant que possible avec les mêmes GGUF effectifs et le même contexte.

## Qualification

Après installation et E2E :

```powershell
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Les trois modèles sont obligatoires. Aucun PASS n'est inféré de leur seule installation.

## Golden Projects

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

## Désinstallation / nettoyage

La suppression manuelle des anciens modèles n'est pas requise par la migration. Si elle devient nécessaire pour libérer de l'espace, vérifier d'abord :

1. que les trois nouveaux modèles sont présents ;
2. que `verify` passe ;
3. que les preuves historiques nécessaires ont été conservées ;
4. qu'aucun rollback actif ne référence l'ancien cache.

Le dossier `proofs/`, les états de qualification et les projets utilisateur ne doivent pas être supprimés lors d'un simple nettoyage de modèles.
