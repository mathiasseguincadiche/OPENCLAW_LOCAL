# Intel Arc B580 — accélération IA locale

## But

Ce document décrit la voie d'inférence **strictement locale** de `OPENCLAW_LOCAL` pour l'Intel Arc B580 12 Go.

**Décision V2 : Vulkan est l'unique API d'accélération GPU LLM supportée par le projet actif.** La qualification matérielle doit maintenant prouver que ce chemin fonctionne correctement sur la workstation réelle ; elle ne sert plus à sélectionner une autre API GPU.

## Flotte Architecture V2

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Les trois modèles routés sont Q4_K_M. Ils restent **non qualifiés matériellement** tant que la B580 réelle n'a pas produit les preuves V2 requises.

Challenger de modèle local hors routage :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite n'est ni un quatrième modèle routé, ni un fallback, et ne modifie pas la décision Vulkan.

## Contextes

```text
8192  -> qualification/HARD-40M nominal
16384 -> orchestration full-agent OpenClaw nominale
>16K  -> non promu sans qualification dédiée
```

Les six cas HARD-40M à 16K restent du stress ciblé. Aucune montée automatique à 32K n'est autorisée.

## Chemins Vulkan actifs

```text
OpenClaw
   |
   +--> ollama-vulkan
   |      trois modèles + image/PDF
   |
   +--> b580-hybrid
          qwen-max        -> Ollama/Vulkan
          gemma-deep      -> llama.cpp/Vulkan
          devstral-devops -> llama.cpp/Vulkan
          image/PDF       -> Ollama/Vulkan
```

Le runtime `llama-cpp-vulkan` est un composant géré interne du profil hybride, pas un profil OpenClaw autonome.

Aucun chemin d'échec ne bascule vers un modèle LLM en ligne.

## Runtime llama.cpp/Vulkan verrouillé

Le contrat courant est défini dans `config/v1/runtime_versions.json` :

```text
source     : ggml-org/llama.cpp
release    : b10621
endpoint   : http://127.0.0.1:8081/v1
models-max : 1
parallel   : 1
context    : 8192
GPU layers : auto
fit        : on
mode       : offline
```

L'archive est vérifiée par SHA-256 avant exécution. Le runtime détecte la B580 via la liste des devices Vulkan et suit son PID dans l'état géré.

## Sources modèles

Le runtime géré réutilise les blobs GGUF locaux réellement référencés par Ollama. Il ne télécharge pas implicitement une autre variante pendant la qualification.

Dans le profil hybride, llama.cpp/Vulkan gère :

```text
gemma4:12b-it-q4_K_M
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Qwen 3.5 reste sur Ollama/Vulkan. Les identités exactes et quantifications doivent être capturées dans les preuves matérielles.

## Pourquoi `models-max=1`

La workstation cible dispose de 12 Go de VRAM. La politique du runtime géré est donc :

- un modèle llama.cpp actif à la fois ;
- chargement/déchargement explicite ;
- `parallel=1` ;
- `gpu_layers=auto` et `fit=on` ;
- aucune affirmation de résidence complète sans preuve réelle.

## Installation et vérification du runtime Vulkan géré

Dry-run :

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
```

Installation/démarrage :

```powershell
.\menu.ps1 -Action intel-vulkan-setup
```

Vérification :

```powershell
.\menu.ps1 -Action intel-vulkan-verify
```

Le setup :

1. lit le runtime verrouillé ;
2. télécharge l'archive gérée si nécessaire ;
3. vérifie son SHA-256 ;
4. vérifie la B580 et le device Vulkan ;
5. résout les blobs GGUF locaux ;
6. génère un preset mono-modèle ;
7. démarre en loopback/offline ;
8. vérifie l'API ;
9. exécute les smokes Gemma + Ministral ;
10. décharge explicitement entre modèles ;
11. conserve une preuve JSON.

Une erreur arrête le runtime candidat et fait échouer le contrôle.

Preuves :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan\
```

## OpenClaw nominal

Le profil nominal reste :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e -Backend ollama-vulkan
```

C'est aussi le chemin de rollback.

## Profil B580 hybride Vulkan

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

L'E2E doit notamment prouver que le spécialiste DevOps est réellement servi par `intel-vulkan`, qu'un vrai tool-call fonctionne et qu'une erreur d'outil est réparée sans fallback de provider.

## Multimodalité

Les images/PDF restent sur Ollama/Vulkan via :

```text
qwen3.5:9b-q4_K_M
gemma4:12b-it-q4_K_M
```

Ministral 3 Reasoning reste text-only dans le contrat nominal. Le handoff depuis une source visuelle reste textuel, structuré et traçable.

## Rollback

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
```

Le setup du runtime géré ne modifie jamais automatiquement la sélection OpenClaw.

## Challenger Ministral / Granite

La comparaison de **modèles** reste séparée de la décision backend :

```powershell
ollama pull granite4.2:8b-q4_K_M
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Elle porte sur coding, tool-calling natif, réparation après erreur et adéquation à l'usage DevOps. Elle ne change jamais automatiquement le routage.

## Ce qui constitue une vraie validation B580

La qualification doit au minimum enregistrer :

- B580 et pilote exact ;
- commit Git exact ;
- identité/digest/quantification des trois modèles ;
- runtime réellement utilisé ;
- chargement des modèles attendus ;
- VRAM/RAM et offload lorsque disponibles ;
- stabilité de chargement/déchargement ;
- OpenClaw E2E ;
- tool-calling ;
- réparation après retour d'outil ;
- trois exécutions stables ;
- contexte soutenable ;
- comportement après redémarrage ;
- revue humaine.

TTFT, débit et mémoire peuvent être enregistrés comme mesures opérationnelles. **Ils ne rouvrent pas le choix de l'API GPU.**

La CI valide les contrats logiciels ; elle ne remplace pas la qualification matérielle.

## État pré-V1

`ollama-vulkan` reste nominal/rollback et `b580-hybrid` est le profil Vulkan géré à valider sur la workstation réelle. V1 reste bloquée tant que les preuves réelles et l'approbation humaine ne sont pas complètes.
