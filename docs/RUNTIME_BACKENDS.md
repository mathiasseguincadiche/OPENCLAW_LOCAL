# Backends d'inférence locale

## Objectif

La plateforme ne lie pas définitivement les trois modèles supportés à un seul backend GPU. Le backend est un axe d'exploitation distinct du choix du modèle et du rôle.

Le chemin quotidien reste **Ollama/Vulkan** tant qu'une preuve réelle sur la workstation ne justifie pas une promotion. Le chemin **llama.cpp/SYCL/Level Zero** est désormais implémenté comme candidat géré pour exploiter plus directement l'Intel Arc B580.

## Backends déclarés

| ID | Provider OpenClaw | Accélération | Statut |
|---|---|---|---|
| `ollama-vulkan` | `ollama` | Vulkan | nominal |
| `llama-cpp-sycl` | `intel-sycl` | SYCL → Level Zero | candidat géré B580 |
| `llama-cpp-vulkan` | non promu | Vulkan | candidat opérateur |

Le mot **nominal** signifie « chemin d'installation et d'intégration actuel », pas « vainqueur de performance ».

## Flotte indépendante du backend

```text
Modèles supportés
  +-- LOCAL_MAX        -> qwen-max        -> qwen3.8:27b
  +-- LOCAL_DEEP       -> gemma-deep      -> gemma4:26b
  +-- LOCAL_SPECIALIST -> devstral-devops -> devstral-small-2:24b

Backends texte
  +-- Ollama / Vulkan
  +-- llama.cpp / SYCL / Level Zero / Intel Arc B580

Multimodal
  +-- Ollama uniquement tant que le chemin SYCL mmproj n'est pas qualifié
```

Changer de backend texte ne réécrit ni les huit rôles, ni le Project Orchestrator, ni les politiques d'escalade.

## Ollama/Vulkan

Ollama reste le chemin nominal car il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- intégration OpenClaw ;
- multimodalité déjà intégrée ;
- exploitation quotidienne ;
- rollback immédiat.

L'API reste liée à `127.0.0.1:11434`. Les modèles sont stockés sous `<OPENCLAW_LOCAL_ROOT>\models\ollama` via `OLLAMA_MODELS`.

## llama.cpp/SYCL/Level Zero

Le candidat Intel est maintenant géré par le dépôt :

- release llama.cpp verrouillée dans `runtime_versions.json` ;
- archive Windows SYCL officielle vérifiée par SHA-256 avant extraction ;
- aucun toolkit oneAPI complet requis pour exécuter le binaire distribué ;
- `ONEAPI_DEVICE_SELECTOR=level_zero:gpu` ;
- device exigé : `SYCL0` ;
- détection explicite de `Intel Arc B580` par `llama-server --list-devices` ;
- écoute loopback uniquement sur `127.0.0.1:8080` ;
- mode `--offline` ;
- `--gpu-layers all` ;
- `--models-max 1` ;
- routeur multi-modèles avec chargement/déchargement à la demande ;
- réutilisation des blobs GGUF déjà possédés par Ollama plutôt qu'un deuxième téléchargement des poids ;
- API OpenAI-compatible `/v1` exposée à OpenClaw sous le provider distinct `intel-sycl`.

`models-max=1` est volontaire : les trois modèles font environ 24 à 27B de paramètres et la B580 dispose de 12 Go de VRAM. Charger plusieurs gros modèles simultanément serait contraire à l'objectif de stabilité mémoire.

## Intégration OpenClaw

La bascule est explicite :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl
```

Le renderer produit alors :

- modèles **texte** des huit agents → `intel-sycl/<runtime_id>` ;
- `imageModel` et `pdfModel` → restent `ollama/...` ;
- provider `intel-sycl` → `http://127.0.0.1:8080/v1` avec `api: openai-completions` ;
- profil de compatibilité outils `llamacpp`.

La configuration refuse la bascule si le serveur Intel n'est pas joignable ou si l'un des trois modèles n'est pas annoncé.

Rollback :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
```

## Cycle opérateur Intel

```powershell
# installer le runtime verrouillé, prouver B580/SYCL/Level Zero,
# démarrer le routeur et tester les 3 modèles
.\menu.ps1 -Action intel-sycl-setup

# refaire les contrôles sans réinstaller
.\menu.ps1 -Action intel-sycl-verify

# comparaison courte
.\menu.ps1 -Action intel-sycl-compare -Quick

# comparaison complète
.\menu.ps1 -Action intel-sycl-compare

# après preuves seulement : bascule texte OpenClaw
.\menu.ps1 -Action configure-openclaw -Backend llama-cpp-sycl
.\menu.ps1 -Action e2e

# rollback configuration puis arrêt du candidat
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-sycl-stop
```

## Protocole de comparaison

Comparer les **mêmes runtime IDs** sur :

- durée murale ;
- chargement du modèle quand le backend l'expose ;
- prompt tokens/seconde ;
- génération tokens/seconde ;
- stabilité ;
- erreurs ou sorties vides ;
- changement de modèle ;
- consommation VRAM/RAM disponible dans les preuves machine ;
- tool-calling OpenClaw ;
- contextes réellement qualifiés ;
- simplicité de démarrage, mise à jour et récupération.

Le runner `scripts/28_compare_local_backends.py` produit un JSON sous `benchmarks/results/` et écrit toujours `promotion_allowed: false`. Un gain de débit ne constitue donc jamais une promotion automatique.

## Conditions de promotion SYCL

Le backend ne peut être considéré comme candidat de production qu'après preuve de :

1. B580 détectée ;
2. `SYCL0` détecté sous `level_zero:gpu` ;
3. trois modèles chargeables ;
4. comparaison reproductible avec Ollama ;
5. configuration OpenClaw valide ;
6. tool-calling réel ;
7. réparation après retour d'outil ;
8. multi-agent/E2E sans erreur de changement de modèle ;
9. trois exécutions stables ;
10. revue humaine.

La promotion ne doit jamais être déduite du nom « XMX », d'un TOPS théorique ou d'un benchmark externe.

## Preuves

Les preuves Intel locales sont placées sous :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\
```

Elles contiennent notamment :

- release et SHA attendus ;
- binaire réellement lancé ;
- PID ;
- selector Level Zero ;
- sortie de détection B580/SYCL ;
- modèles annoncés ;
- smoke-tests ;
- logs stdout/stderr du serveur.

Les résultats de comparaison restent sous `benchmarks/results/` et hors Git selon la politique de qualification.
