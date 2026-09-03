# Backends d'inférence locale

## Objectif

Le choix du modèle et le choix du backend sont deux axes distincts. `OPENCLAW_LOCAL` conserve plusieurs moteurs locaux afin de mesurer ce qui fonctionne réellement sur l'Intel Arc B580 12 Go.

La migration de flotte vers des modèles Q4_K_M plus petits **réinitialise la décision de performance** : aucun benchmark de l'ancienne flotte 24–27B ne qualifie les nouveaux modèles.

## Flotte active

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

Le contexte nominal est 8192 tokens. Le 16K reste un stress de qualification.

## Backends déclarés

| ID | Provider OpenClaw | Accélération | Endpoint | Statut |
|---|---|---|---|---|
| `ollama-vulkan` | `ollama` | Vulkan | `127.0.0.1:11434` | nominal / rollback |
| `llama-cpp-sycl` | `intel-sycl` | SYCL → Level Zero | `127.0.0.1:8080/v1` | candidat |
| `llama-cpp-vulkan` | `intel-vulkan` | Vulkan | `127.0.0.1:8081/v1` | candidat |
| `b580-hybrid` | mixte local | par modèle | Ollama + `8081/v1` | profil candidat |

`nominal` signifie ici chemin d'installation et de rollback sûr. Cela ne signifie pas qu'Ollama est le moteur le plus rapide pour tous les nouveaux modèles.

## Profil B580 hybride candidat

```text
qwen-max        -> Ollama / Vulkan
gemma-deep      -> llama.cpp / Vulkan
devstral-devops -> llama.cpp / Vulkan
image/PDF       -> Ollama
```

OpenClaw expose alors simultanément un provider `ollama` et un provider `intel-vulkan`. Le profil n'ajoute aucun provider cloud.

Le choix conserve Qwen sur Ollama et Gemma/Qwen Coder sur Vulkan comme **hypothèse d'exploitation à requalifier**, pas comme résultat déjà démontré pour la nouvelle flotte.

## Mesures historiques de la flotte retirée

Des mesures B580 ont été obtenues auparavant avec une flotte constituée de modèles de classe **24–27B**. Elles ont servi à montrer deux choses utiles :

1. un backend unique n'est pas nécessairement optimal pour tous les modèles ;
2. cette classe de taille peut provoquer une pression mémoire/offload excessive sur une B580 12 Go.

Ces mesures sont désormais **historiques seulement**. Elles ne doivent pas être copiées dans une attestation de qualification de la flotte actuelle et ne permettent pas de promouvoir `b580-hybrid` avec les nouveaux runtimes. Les IDs retirés restent consultables dans l'historique Git et les anciennes preuves, pas dans les surfaces actives.

## Ollama/Vulkan

Ollama reste le chemin nominal et le rollback parce qu'il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- multimodalité Qwen/Gemma ;
- démarrage et récupération ;
- conservation d'un chemin de référence commun aux trois modèles.

L'API reste liée à :

```text
http://127.0.0.1:11434
```

Le contexte nominal exposé à OpenClaw est 8192.

## llama.cpp/SYCL/Level Zero

Le chemin SYCL reste géré et qualifiable :

- release llama.cpp verrouillée dans `runtime_versions.json` ;
- archive vérifiée par SHA-256 ;
- `ONEAPI_DEVICE_SELECTOR=level_zero:gpu` ;
- device B580 détecté ;
- endpoint `127.0.0.1:8080/v1` ;
- `--offline` ;
- `gpu_layers=auto` ;
- `models_max=1` ;
- `parallel=1` ;
- contexte 8192 ;
- unload explicite entre modèles.

Les trois modèles actuels doivent être chargés et mesurés avec leurs identités/quantifications exactes. Un résultat produit avec un ancien artefact ne qualifie pas le runtime actuel.

## llama.cpp/Vulkan géré

Le runtime Vulkan candidat :

- utilise la release verrouillée dans `runtime_versions.json` ;
- écoute sur `http://127.0.0.1:8081/v1` ;
- détecte l'Intel Arc B580 ;
- utilise `models_max=1`, `parallel=1`, `gpu_layers=auto` et `fit=on` ;
- utilise le contexte 8192 ;
- reste `--offline` ;
- suit son PID dans l'état géré ;
- charge `gemma3:12b-it-q4_K_M` et `qwen2.5-coder:14b-instruct-q4_K_M` dans le profil hybride ;
- décharge explicitement les modèles entre smokes/switches.

Le setup Vulkan arrête le routeur SYCL suivi avant de démarrer afin d'éviter une contention B580 entre deux runtimes llama.cpp.

## Multimodalité

Le profil hybride garde PDF/images sur Ollama :

```text
imageModel/pdfModel
  -> ollama/qwen3.5:9b-q4_K_M
  -> fallback ollama/gemma3:12b-it-q4_K_M
```

Qwen 2.5 Coder 14B reste text-only. Le passage d'une entrée visuelle vers le spécialiste DevOps se fait par ingestion/handoff textuel avec provenance.

## Protocole de comparaison

Comparer, autant que possible, le **même modèle effectif et la même quantification** sur les backends :

- TTFT ;
- durée murale ;
- tokens/s ;
- prompt tokens/s ;
- VRAM/RAM ;
- chargement du modèle ;
- stabilité ;
- changement de modèle ;
- isolation mémoire entre backends ;
- tool-calling OpenClaw ;
- contexte 8K puis stress 16K ;
- simplicité d'exploitation et rollback.

Le runner de comparaison conserve `promotion_allowed: false`. Une comparaison n'autorise jamais à elle seule une bascule de production.

## Cycle opérateur recommandé

### Baseline Ollama

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e -Backend ollama-vulkan
```

### Qualification SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

### Qualification Vulkan

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

### E2E hybride

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

### Rollback

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
.\menu.ps1 -Action intel-sycl-stop
```

## Conditions de promotion du profil hybride

Avant toute promotion, il faut de nouvelles preuves portant sur **la flotte actuelle** :

1. B580 détectée et pilote enregistré ;
2. identités/digests des trois nouveaux modèles ;
3. chargement des modèles attendus sur chaque backend ;
4. benchmark isolé reproductible ;
5. configuration OpenClaw valide ;
6. provider attendu prouvé agent par agent ;
7. tool-calling réel avec Qwen 2.5 Coder/Vulkan ;
8. réparation après erreur d'outil ;
9. multi-agent/E2E sans fallback cloud ;
10. trois runs stables ;
11. contexte soutenable mesuré ;
12. revue humaine.

Le dépôt conserve `default_backend: ollama-vulkan` et `no_automatic_promotion: true` jusqu'à décision humaine.

## Preuves

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan-probe\
<OPENCLAW_LOCAL_ROOT>\proofs\
<REPO>\benchmarks\results\
```

Les preuves doivent identifier sans ambiguïté le commit, le backend, le modèle, le digest/quantification, le pilote et le protocole réellement utilisés.
