# Installation Windows 11

## Préconditions

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap et les trois modèles ;
- pilote Intel Arc à jour avant la qualification matérielle.

Python, Node.js, OpenClaw et Ollama sont contrôlés par le bootstrap à partir de `config/v1/runtime_versions.json`.

## Emplacement par défaut

Si `E:` existe, la plateforme utilise :

```text
E:\AI\OpenClawLocal
```

Sinon :

```text
%LOCALAPPDATA%\OpenClawLocal
```

`OPENCLAW_LOCAL_ROOT` permet de choisir une autre racine avant l'installation.

L'arborescence opérationnelle est :

```text
<OPENCLAW_LOCAL_ROOT>\
├── runtime\
├── models\
│   └── ollama\
├── projects\
├── workspaces\
├── state\
└── proofs\
    └── logs\
```

`OLLAMA_MODELS` est configuré sur `<OPENCLAW_LOCAL_ROOT>\models\ollama` **avant le téléchargement des modèles** afin d'éviter un stockage implicite dans le profil utilisateur du disque système.

## Journalisation automatique

Toute action **réelle** exécutée via `menu.ps1` crée automatiquement un transcript PowerShell sous :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\logs\
```

Exemple :

```text
20260828_142530123_install-full.log
20260828_151004772_audit.log
20260828_151115904_verify.log
20260828_153812441_qualification.log
```

Le chemin est affiché dès le début sous la forme `LOG=<chemin>` puis, à la fermeture, `LOG_SAVED=<chemin>`. Le transcript contient aussi `ACTION_RESULT=PASS` ou `ACTION_RESULT=FAIL`.

Les `-DryRun` ne créent volontairement aucun transcript afin de conserver le contrat sans mutation. La journalisation automatique peut être désactivée explicitement avec `-NoLog` si nécessaire.

Afficher les derniers logs et emplacements de preuves :

```powershell
.\menu.ps1 -Action logs
```

## 1. Prévisualiser

```powershell
.\menu.ps1 -Action install-full -DryRun
```

Le dry-run ne télécharge rien, n'installe rien, ne modifie aucune variable persistante et ne crée pas de transcript automatique.

## 2. Installation complète

```powershell
.\menu.ps1 -Action install-full
```

Le parcours effectue dans l'ordre :

1. validation Windows 11 x64 / PowerShell ;
2. Python verrouillé ;
3. Node.js isolé et vérifié ;
4. OpenClaw exact et vérifié ;
5. Ollama Windows ;
6. environnement Python `clawlocal` ;
7. variables utilisateur et PATH ;
8. configuration du stockage Ollama ;
9. démarrage/vérification Ollama ;
10. téléchargement des trois modèles requis ;
11. baseline OpenClaw ;
12. déploiement des huit workspaces ;
13. génération, dry-run et application du patch OpenClaw ;
14. installation/démarrage du Gateway local ;
15. vérification finale du parcours local.

Le transcript de cette exécution reste disponible même si l'installation échoue avant la fin, ce qui permet de transmettre l'erreur exacte sans relancer aveuglément le parcours.

Après la première installation, fermer puis rouvrir PowerShell.

## 3. Vérifier les emplacements

```powershell
$env:OPENCLAW_LOCAL_ROOT
$env:OLLAMA_MODELS
$env:OPENCLAW_STATE_DIR
```

Avec `E:` disponible, les valeurs attendues sont :

```text
OPENCLAW_LOCAL_ROOT = E:\AI\OpenClawLocal
OLLAMA_MODELS       = E:\AI\OpenClawLocal\models\ollama
OPENCLAW_STATE_DIR  = E:\AI\OpenClawLocal\state
```

## 4. Vérifier l'installation

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

Chaque action réelle possède son propre transcript sous `proofs\logs`. Le test E2E conserve en plus sa preuve JSON structurée sous `proofs`.

Résultat attendu :

- runtime conforme ;
- Ollama loopback ;
- exactement trois modèles supportés ;
- huit agents ;
- Gateway joignable ;
- inférence locale ;
- tool-calling et réparation E2E ;
- aucune dépendance cloud nominale.

## 5. Qualifier la workstation

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Les trois modèles sont obligatoires :

```text
qwen3.8:27b
gemma4:26b
devstral-small-2:24b
```

Le transcript `qualification` capture la console de la campagne complète. Les résultats structurés d'inventaire et benchmark restent sous `benchmarks\results` dans le dépôt.

Un succès automatique mène au maximum à `READY_FOR_MANUAL_QUALIFICATION`.

## Installation du runtime seulement

```powershell
.\menu.ps1 -Action install-core -DryRun
.\menu.ps1 -Action install-core
```

Cette action installe/répare le runtime verrouillé sans télécharger la flotte. Avant un téléchargement manuel ultérieur, exécuter :

```powershell
.\menu.ps1 -Action configure-local
.\menu.ps1 -Action models
```

Cela garantit que `OLLAMA_MODELS` est appliqué avant les `ollama pull`.

## Dérive volontaire d'Ollama

```powershell
.\menu.ps1 -Action install-core -AllowRuntimeDrift
```

Cette option conserve explicitement une version déjà installée différente du lock. Elle impose une nouvelle qualification et ne transforme pas cette version en runtime validé.

## Ollama

L'API locale est :

```text
http://127.0.0.1:11434
```

Ne pas ajouter `/v1` au endpoint utilisé par le projet. Ne pas exposer Ollama sur le LAN sans besoin explicite et revue de sécurité.

Si l'emplacement `OLLAMA_MODELS` change, `configure-local` redémarre le serveur Ollama afin que le nouveau processus hérite de la valeur configurée avant tout téléchargement.

## OpenClaw

La flotte est générée depuis les contrats Git et appliquée avec un dry-run avant écriture réelle. Les fallbacks persistants restent uniquement dans les trois modèles locaux supportés.

Le cloud reste désactivé après installation :

```text
OPENCLAW_LOCAL_CLOUD_ENABLED=false
```

Aucune clé OpenRouter n'est créée ni stockée dans Git.

## Données à protéger

Priorité de sauvegarde :

```text
projects\
state\
proofs\        (y compris proofs\logs si les diagnostics doivent être conservés)
```

`runtime\` et `workspaces\` sont reconstruisibles. Les modèles peuvent être retéléchargés.

Avant de partager un transcript, vérifier qu'il ne contient pas de secret saisi ou affiché par un outil externe. Ne jamais transmettre `.env`, `OPENROUTER_API_KEY`, token Gateway ou document privé.

Voir aussi :

- `docs/OPERATIONS.md` ;
- `docs/TROUBLESHOOTING.md` ;
- `docs/OPENCLAW_INTEGRATION.md` ;
- `docs/QUALIFICATION.md`.
