# Installation Windows 11

## Préconditions minimales

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet disponible pour installer les runtimes manquants ;
- pilote Intel Arc à jour avant la qualification matérielle.

Python, Node.js, OpenClaw et Ollama n'ont plus besoin d'être préinstallés manuellement : le bootstrap les contrôle à partir de `config/v1/runtime_versions.json`.

## 1. Prévisualiser l'installation

```powershell
.\menu.ps1 -Action install-full -DryRun
```

Le dry-run n'installe rien, ne télécharge rien et ne modifie aucune variable persistante.

## 2. Installation complète

```powershell
.\menu.ps1 -Action install-full
```

Le parcours effectue dans l'ordre :

1. validation Windows 11 x64 / PowerShell ;
2. Python préféré verrouillé ;
3. Node.js isolé et vérifié par SHA-256 ;
4. tarball OpenClaw exact vérifié par intégrité SHA-512/SRI ;
5. Ollama Windows ;
6. environnement Python isolé `clawlocal` ;
7. variables utilisateur locales et PATH ;
8. démarrage/vérification Ollama ;
9. téléchargement explicite des modèles requis ;
10. baseline OpenClaw ;
11. déploiement des huit workspaces ;
12. génération + dry-run + application du patch OpenClaw ;
13. installation/démarrage du Gateway local ;
14. vérification finale du parcours local.

Le runtime géré est placé par défaut sous :

```text
E:\AI\OpenClawLocal
```

si `E:` existe, sinon sous `%LOCALAPPDATA%\OpenClawLocal`. `OPENCLAW_LOCAL_ROOT` peut imposer un autre emplacement avant l'installation.

## Installation du runtime seulement

```powershell
.\menu.ps1 -Action install-core -DryRun
.\menu.ps1 -Action install-core
```

Cette action installe/répare le runtime verrouillé sans télécharger les modèles ni modifier la flotte OpenClaw.

## Dérive volontaire d'Ollama

Par défaut, une version Ollama différente du lock provoque un arrêt afin de préserver la reproductibilité. Pour conserver explicitement une version déjà installée :

```powershell
.\menu.ps1 -Action install-core -AllowRuntimeDrift
```

Cela ne qualifie pas la version différente. Une nouvelle exécution benchmark + E2E + qualification reste obligatoire.

## Vérifications après installation

Ouvrir un nouveau PowerShell puis :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

La qualification matérielle complète vient ensuite :

```powershell
.\menu.ps1 -Action qualification
```

## Ollama

Le backend local écoute sur `http://127.0.0.1:11434`. Ne pas ajouter `/v1` : OpenClaw utilise l'API Ollama native pour conserver le tool-calling. Ne pas exposer Ollama sur le LAN sans besoin explicite et revue de sécurité.

## OpenClaw

La flotte est générée depuis les contrats Git du dépôt et appliquée avec `openclaw config patch --dry-run` avant toute écriture réelle. Les huit agents utilisent uniquement des fallbacks locaux persistants.

Le cloud n'est jamais activé par l'installation. `OPENCLAW_LOCAL_CLOUD_ENABLED=false` est la valeur initiale et aucune clé OpenRouter n'est créée ni enregistrée dans Git.

Voir aussi :

- `docs/OPENCLAW_INTEGRATION.md` ;
- `docs/TROUBLESHOOTING.md` ;
- `docs/QUALIFICATION.md`.
