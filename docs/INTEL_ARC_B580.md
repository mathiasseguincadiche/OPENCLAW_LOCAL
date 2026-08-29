# Intel Arc B580 — accélération IA locale

## But

Ce document décrit le chemin spécialisé Intel de `OPENCLAW_LOCAL` pour la **Intel Arc B580 12 Go**.

L'objectif n'est pas de cocher toutes les API Intel disponibles. L'objectif est d'utiliser un backend LLM capable d'exploiter la carte de façon pertinente, mesurable et réversible :

```text
OpenClaw
   │
   ├── texte ─────> provider intel-sycl
   │                  │
   │                  v
   │              llama-server
   │                  │
   │                  v
   │                 SYCL
   │                  │
   │                  v
   │              Level Zero
   │                  │
   │                  v
   │            Intel Arc B580 / XMX
   │
   └── image/PDF --> Ollama/Vulkan (tant que mmproj SYCL non qualifié)
```

## Pourquoi SYCL/Level Zero

La B580 expose des moteurs matriciels XMX et plusieurs API de calcul. Pour les LLM GGUF de cette plateforme, le chemin spécialisé choisi est le backend **SYCL de llama.cpp**, contraint au GPU via **Level Zero**.

OpenCL, OpenVINO et IPEX ne sont pas ajoutés au runtime LLM principal simplement parce qu'ils existent : ils répondent à d'autres charges ou frameworks. Ils pourront être évalués séparément si un besoin concret le justifie.

## Runtime verrouillé

La version est définie dans `config/v1/runtime_versions.json` :

```text
source     : ggml-org/llama.cpp
release    : b10621
asset      : llama-b10621-bin-win-sycl-x64.zip
device     : SYCL0
selector   : level_zero:gpu
endpoint   : http://127.0.0.1:8080/v1
models-max : 1
```

L'archive n'est jamais exécutée avant validation de son SHA-256 versionné.

## Réutilisation des modèles Ollama

La plateforme ne duplique pas automatiquement les dizaines de Go de poids.

Pour chacun des trois modèles requis, le setup exécute :

```powershell
ollama show <model> --modelfile
```

La ligne `FROM` doit pointer vers un fichier local existant. Ce fichier GGUF devient la source du preset llama.cpp. Si ce contrat n'est pas satisfait, le setup échoue au lieu de télécharger silencieusement un autre modèle.

## Installation et démarrage

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
```

Cette action :

1. lit le runtime verrouillé ;
2. télécharge uniquement l'archive binaire si elle manque ;
3. vérifie son SHA-256 ;
4. extrait le runtime dans un répertoire versionné ;
5. exécute `llama-server --list-devices` sous `ONEAPI_DEVICE_SELECTOR=level_zero:gpu` ;
6. exige `SYCL0` et une Intel Arc B580 ;
7. résout les trois GGUF Ollama ;
8. génère le preset multi-modèles ;
9. lance le serveur en loopback, offline, `models-max=1`, `gpu-layers=all` ;
10. vérifie `/v1/models` ;
11. exécute un smoke-test `/v1/chat/completions` pour les trois modèles ;
12. conserve une preuve JSON.

Une erreur à n'importe quelle étape arrête le serveur candidat.

## Pourquoi `models-max=1`

Les trois modèles sont de l'ordre de 24 à 27B. La B580 possède 12 Go de VRAM.

La politique choisie est donc :

- un seul modèle lourd actif à la fois ;
- chargement/déchargement par le routeur llama-server ;
- aucune tentative de garder simultanément les trois modèles en mémoire ;
- orchestration séquentielle par défaut conservée.

Cette politique limite la pression VRAM/RAM et correspond au contrat actuel du Project Orchestrator (`max_parallel_tasks=1`).

## Vérification

```powershell
.\menu.ps1 -Action intel-sycl-verify
```

Le contrôle exige :

- runtime présent ;
- binaire exécutable ;
- B580 visible sous SYCL/Level Zero ;
- processus serveur suivi ;
- API locale disponible ;
- trois modèles annoncés ;
- trois smoke-tests réussis.

Une preuve est écrite dans :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\verify_*.json
```

## Comparaison avec Ollama/Vulkan

Diagnostic rapide :

```powershell
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Comparaison complète :

```powershell
.\menu.ps1 -Action intel-sycl-compare
```

Le protocole utilise :

- mêmes runtime IDs ;
- même contexte 8192 ;
- température 0 ;
- Qwen thinking désactivé uniquement pour rendre la comparaison backend plus comparable ;
- mêmes prompts ;
- durée murale ;
- prompt tok/s ;
- génération tok/s ;
- répétitions versionnées dans la preuve.

Le rapport indique toujours :

```text
PROMOTION_ALLOWED=false
```

La vitesse seule ne suffit pas.

## Basculer OpenClaw

Après setup, verify et comparaison :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl -DryRun
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl
.\menu.ps1 -Action e2e
```

Les modèles texte des huit agents passent alors au provider `intel-sycl`.

Les modèles image/PDF restent sur Ollama. Cette séparation est volontaire tant que la chaîne multimodale llama.cpp/SYCL n'a pas ses propres preuves matérielles.

## Rollback

Configuration :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
```

Arrêt du serveur candidat :

```powershell
.\menu.ps1 -Action intel-sycl-stop
```

Le setup Intel ne modifie jamais OpenClaw de lui-même.

## Ce qui constitue une vraie validation XMX

Le projet ne prétend pas mesurer directement le taux d'occupation de chaque unité XMX. Une validation opérationnelle exige au minimum :

- B580 vue par le backend SYCL sous Level Zero ;
- kernels GPU réellement utilisables sans fallback d'échec ;
- performance mesurée par rapport à Vulkan ;
- stabilité de chargement/déchargement ;
- OpenClaw E2E ;
- tool-calling ;
- réparation après retour d'outil ;
- trois exécutions stables ;
- revue humaine.

Le terme « optimisé B580 » ne doit être utilisé qu'après ces preuves, pas à partir des seuls TOPS théoriques.

## Limite actuelle importante

Le routeur multi-modèles change de modèle à la demande. Avant promotion, le test E2E doit donc inclure des appels successifs entre agents utilisant des modèles différents et vérifier qu'aucun changement de modèle n'interrompt une requête active.

C'est précisément la raison pour laquelle `llama-cpp-sycl` reste **candidat** même après son installation réussie.
