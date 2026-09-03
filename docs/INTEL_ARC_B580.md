# Intel Arc B580 — accélération IA locale

## But

Ce document décrit les chemins d'inférence locaux spécialisés de `OPENCLAW_LOCAL` pour l'**Intel Arc B580 12 Go**. L'objectif est d'utiliser des backends LLM mesurables et réversibles, pas d'activer toutes les API Intel disponibles.

## Flotte actuelle

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

La flotte a été redimensionnée après observation d'une pression mémoire/offload excessive avec la précédente classe 24–27B. Les nouveaux modèles restent **non qualifiés matériellement** tant qu'une nouvelle campagne B580 n'a pas produit ses preuves.

Le contexte nominal est 8192 tokens ; le 16K reste un stress de qualification.

## Chemins locaux

```text
OpenClaw
   |
   +--> Ollama / Vulkan (nominal et rollback)
   |
   +--> llama.cpp / SYCL / Level Zero (candidat)
   |
   +--> llama.cpp / Vulkan (candidat)
   |
   +--> profil b580-hybrid
          qwen-max        -> Ollama
          gemma-deep      -> llama.cpp/Vulkan
          devstral-devops -> llama.cpp/Vulkan
          image/PDF       -> Ollama
```

Qwen et Gemma portent le parcours multimodal. Qwen 2.5 Coder est text-only et reçoit un handoff textuel/structuré lorsque la source initiale est visuelle.

## Pourquoi SYCL/Level Zero

Pour les LLM GGUF, le chemin Intel spécialisé est le backend **SYCL de llama.cpp**, contraint au GPU via **Level Zero**. OpenCL, OpenVINO ou d'autres frameworks ne sont pas ajoutés au runtime principal sans besoin concret et protocole dédié.

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
parallel   : 1
context    : 8192
GPU layers : auto
```

L'archive n'est jamais exécutée avant validation de son SHA-256 versionné.

## Sources modèles

Le contrat actuel réutilise les sources GGUF effectives exposées par le stockage local lorsque cela est compatible. Toute source native alternative doit être explicitement verrouillée dans `runtime_versions.json` avec intégrité vérifiable ; aucun téléchargement implicite d'un autre modèle n'est accepté pendant un benchmark.

## Installation SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
```

Le setup :

1. lit le runtime verrouillé ;
2. télécharge uniquement le binaire géré si nécessaire ;
3. vérifie son SHA-256 ;
4. vérifie B580, `SYCL0` et Level Zero ;
5. résout les trois modèles requis ;
6. génère un preset mono-modèle actif (`models-max=1`) ;
7. démarre en loopback/offline, `parallel=1`, `gpu-layers=auto` ;
8. vérifie l'API ;
9. exécute des smokes déterministes ;
10. décharge explicitement entre modèles ;
11. conserve une preuve JSON.

Une erreur arrête le serveur candidat et interdit toute promotion.

## Pourquoi `models-max=1`

Même redimensionnée, la flotte ne doit pas garder trois modèles simultanément en VRAM sur une carte 12 Go. La politique est donc :

- un modèle actif à la fois sur les routeurs llama.cpp ;
- chargement/déchargement explicite ;
- orchestration séquentielle par défaut ;
- mesure des temps de changement de modèle ;
- aucune affirmation de résidence complète avant preuve.

## Vérification SYCL

```powershell
.\menu.ps1 -Action intel-sycl-verify
```

Le contrôle exige runtime, binaire, B580, processus suivi, API locale, trois modèles annoncés et smokes réussis. Les preuves sont conservées sous :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\
```

## Diagnostic direct SYCL

```powershell
.\menu.ps1 -Action intel-sycl-diagnose -Model qwen3.5:9b-q4_K_M
.\menu.ps1 -Action intel-sycl-diagnose -Model gemma3:12b-it-q4_K_M
.\menu.ps1 -Action intel-sycl-diagnose -Model qwen2.5-coder:14b-instruct-q4_K_M
```

Le diagnostic isole full/auto offload, comportement `fit` et CPU-only sans modifier automatiquement OpenClaw.

## Comparaison Ollama / SYCL

```powershell
.\menu.ps1 -Action intel-sycl-compare -Quick
.\menu.ps1 -Action intel-sycl-compare
```

Comparer le même modèle effectif et la même quantification avec :

- contexte 8192 pour la baseline ;
- température déterministe ;
- thinking désactivé lorsque le protocole de comparaison l'exige ;
- mêmes prompts ;
- durée murale ;
- TTFT ;
- prompt tok/s ;
- génération tok/s ;
- chargement/déchargement ;
- mémoire observée si disponible.

Le rapport conserve :

```text
PROMOTION_ALLOWED=false
```

La vitesse seule ne suffit pas.

## Backend llama.cpp/Vulkan

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

Le runtime géré Vulkan écoute sur `127.0.0.1:8081/v1`, utilise `models-max=1`, `parallel=1`, `gpu-layers=auto`, `fit=on`, contexte 8192 et reste offline.

Dans le profil hybride, il gère Gemma 3 12B et Qwen 2.5 Coder 14B. Le serveur SYCL suivi est arrêté avant Vulkan afin de ne pas créer une contention artificielle de VRAM.

## Basculer OpenClaw vers un candidat

SYCL :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl -DryRun
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl
.\menu.ps1 -Action e2e -Backend llama-cpp-sycl
```

Hybride :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Les images/PDF restent sur Ollama tant qu'un parcours multimodal llama.cpp n'est pas qualifié.

## Rollback

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
.\menu.ps1 -Action intel-sycl-stop
```

Les setups candidats ne modifient jamais automatiquement la sélection OpenClaw.

## Ce qui constitue une vraie validation B580

Une promotion exige au minimum :

- B580 et pilote exact enregistrés ;
- identité/digest/quantification des trois modèles ;
- modèle réellement chargé sur le backend attendu ;
- benchmark reproductible ;
- VRAM/RAM et offload observés lorsque disponibles ;
- stabilité de chargement/déchargement ;
- OpenClaw E2E ;
- tool-calling ;
- réparation après retour d'outil ;
- trois exécutions stables ;
- contexte soutenable ;
- revue humaine.

Le terme « optimisé B580 » ne doit être utilisé qu'après ces preuves. La CI valide les contrats logiciels ; elle ne remplace pas la qualification matérielle.

## État pré-V1

`ollama-vulkan` reste le nominal/rollback. SYCL, Vulkan et `b580-hybrid` restent des candidats jusqu'aux nouvelles mesures de cette flotte. Les anciennes preuves 24–27B restent historiques et ne peuvent pas être réutilisées comme attestation V1.
