# Backends d'inférence locale

## Objectif

La plateforme ne lie pas les trois modèles supportés à un backend GPU unique. Le backend est un axe d'exploitation distinct du choix du modèle et du rôle.

Le chemin installé par défaut reste **Ollama/Vulkan**. Les mesures réelles effectuées sur l'Intel Arc B580 ont toutefois montré qu'un backend global unique est sous-optimal. Le dépôt expose donc un profil candidat explicite **`b580-hybrid`** :

- Qwen 3.8 27B → Ollama/Vulkan ;
- Gemma 4 26B → llama.cpp/Vulkan ;
- Devstral Small 2 24B → llama.cpp/Vulkan ;
- image/PDF → Ollama ;
- aucun fallback cloud silencieux ;
- rollback explicite vers Ollama.

Le profil hybride reste candidat tant que son E2E OpenClaw réel n'est pas validé. Il n'est jamais activé automatiquement.

## Backends déclarés

| ID | Provider OpenClaw | Accélération | Endpoint | Statut |
|---|---|---|---|---|
| `ollama-vulkan` | `ollama` | Vulkan | `127.0.0.1:11434` | nominal / rollback |
| `llama-cpp-sycl` | `intel-sycl` | SYCL → Level Zero | `127.0.0.1:8080/v1` | qualification B580 |
| `llama-cpp-vulkan` | `intel-vulkan` | Vulkan | `127.0.0.1:8081/v1` | candidat géré Gemma/Devstral |
| `b580-hybrid` | mixte local | par modèle | Ollama + `8081/v1` | profil candidat mesuré |

Le mot **nominal** signifie « chemin d'installation et rollback sûr », pas « vainqueur de performance pour tous les modèles ».

## Résultat du benchmark B580 isolé

Le protocole de comparaison décharge explicitement Ollama avant le cas llama.cpp et vérifie `/api/ps`; les résultats exploitables portent `GPU_MEMORY_ISOLATION=true`.

Mesures observées sur le scénario DevOps structuré :

| Modèle | Ollama/Vulkan | llama.cpp/SYCL | llama.cpp/Vulkan | Backend mesuré le plus rapide |
|---|---:|---:|---:|---|
| Qwen 3.8 27B | 8.27 tok/s | 5.00 tok/s | 6.29 tok/s | Ollama/Vulkan |
| Gemma 4 26B | 14.03 tok/s | 34.94 tok/s | 36.08 tok/s | llama.cpp/Vulkan |
| Devstral Small 2 24B | 7.77 tok/s | 7.51 tok/s | 8.96 tok/s | llama.cpp/Vulkan |

Ces chiffres constituent une preuve locale pour cette workstation et ce protocole, pas une promesse générale de performance sur toutes les machines.

## Flotte indépendante du backend

```text
Modèles supportés
  +-- LOCAL_MAX        -> qwen-max        -> qwen3.8:27b
  +-- LOCAL_DEEP       -> gemma-deep      -> gemma4:26b
  +-- LOCAL_SPECIALIST -> devstral-devops -> devstral-small-2:24b

Profil B580 hybride texte
  +-- qwen-max        -> Ollama / Vulkan
  +-- gemma-deep      -> llama.cpp / Vulkan
  +-- devstral-devops -> llama.cpp / Vulkan

Multimodal
  +-- Ollama uniquement
```

Changer de profil ne réécrit ni les huit rôles, ni le Project Orchestrator, ni les politiques d'escalade.

## Ollama/Vulkan

Ollama reste le chemin nominal et de rollback car il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- multimodalité ;
- Qwen, qui reste le plus rapide sur le benchmark isolé ;
- récupération immédiate si un runtime candidat échoue.

L'API reste liée à `127.0.0.1:11434`.

## llama.cpp/SYCL/Level Zero

Le chemin SYCL reste géré et qualifiable :

- llama.cpp `b10621` verrouillé par SHA-256 ;
- `ONEAPI_DEVICE_SELECTOR=level_zero:gpu` ;
- device exigé : `SYCL0` ;
- B580 détectée via `--list-devices` ;
- endpoint `127.0.0.1:8080/v1` ;
- `--offline` ;
- `--gpu-layers auto` + `--fit on` ;
- `models_max=1` ;
- `parallel=1` ;
- contexte initial 8192 ;
- unload explicite entre modèles ;
- Devstral utilise un GGUF llama.cpp natif Q4_K_M verrouillé par SHA-256.

SYCL reste utile pour qualification et comparaison, mais n'est plus le candidat prioritaire du profil B580 mesuré.

## llama.cpp/Vulkan géré

Le runtime Vulkan de production candidate utilise la même release llama.cpp `b10621` que SYCL, avec l'archive Windows Vulkan officielle vérifiée par SHA-256.

Contrat :

- endpoint : `http://127.0.0.1:8081/v1` ;
- device B580 détecté dynamiquement (`Vulkan0` sur la workstation qualifiée) ;
- `models_max=1` ;
- `parallel=1` ;
- `gpu_layers=auto` ;
- `fit=on` ;
- contexte 8192 ;
- `--offline` ;
- PID suivi dans l'état géré ;
- Gemma + Devstral seulement ;
- Qwen reste volontairement sur Ollama ;
- mêmes sources GGUF effectives que le chemin llama.cpp/SYCL ;
- unload explicite après chaque smoke/switch.

Le setup Vulkan arrête le routeur SYCL suivi avant de démarrer afin d'éviter une contention de VRAM entre deux runtimes llama.cpp.

## Profil `b580-hybrid`

Le renderer OpenClaw configure deux providers locaux simultanés :

```text
ollama
  baseUrl -> http://127.0.0.1:11434
  qwen3.8:27b
  gemma4:26b (multimodal / rollback local)
  devstral-small-2:24b (rollback local)

intel-vulkan
  baseUrl -> http://127.0.0.1:8081/v1
  gemma4:26B
  devstral-small-2:24B
```

Routage texte :

```text
qwen-max        -> ollama/qwen3.8:27b
gemma-deep      -> intel-vulkan/gemma4:26B
devstral-devops -> intel-vulkan/devstral-small-2:24B
```

Les `imageModel` et `pdfModel` restent systématiquement sur Ollama. Le profil n'ajoute aucun provider cloud.

## Cycle opérateur recommandé

### Qualification SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

### Qualification Vulkan géré

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

### Bascule hybride explicite

Uniquement après succès des deux commandes précédentes :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

L'E2E doit prouver :

- provider primaire attendu agent par agent ;
- Qwen réellement servi par Ollama ;
- agents Gemma/Devstral réellement servis par `intel-vulkan` ;
- tool-calling réel Devstral/Vulkan ;
- réparation après erreur outil ;
- trois runs stables ;
- aucune escalade cloud.

### Rollback

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
```

## Protocole de comparaison

Comparer les mêmes modèles et le même scénario sur :

- durée murale ;
- chargement du modèle ;
- prompt tokens/seconde ;
- génération tokens/seconde ;
- stabilité ;
- changement de modèle ;
- isolation VRAM entre backends ;
- tool-calling OpenClaw ;
- contextes réellement qualifiés ;
- simplicité de démarrage, mise à jour et récupération.

Le runner `scripts/28_compare_local_backends.py` écrit toujours `promotion_allowed: false`. Le probe Vulkan accepte uniquement une baseline schema `1.5.0` portant `gpu_memory_isolation_between_backends=true`.

## Conditions de promotion du profil hybride

Le profil `b580-hybrid` ne peut devenir nominal qu'après preuve de :

1. B580 détectée ;
2. runtime Vulkan géré et intègre ;
3. Gemma + Devstral chargeables sur Vulkan ;
4. benchmark isolé reproductible ;
5. configuration OpenClaw valide ;
6. provider attendu prouvé pour chaque rôle ;
7. tool-calling Devstral/Vulkan réel ;
8. réparation après retour d'outil ;
9. multi-agent/E2E sans fallback cloud ;
10. trois exécutions stables ;
11. revue humaine.

Le dépôt conserve `default_backend: ollama-vulkan` et `no_automatic_promotion: true` jusqu'à cette décision humaine.

## Preuves

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan-probe\
<repo>\benchmarks\results\
```

Les preuves contiennent release, SHA, binaire, PID, device, modèles, smokes et logs stdout/stderr. Les résultats de qualification restent locaux/hors Git selon la politique du projet.
