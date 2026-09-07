# Backends d'inférence locale

## Objectif

Le choix du modèle et le choix du backend sont deux axes distincts. `OPENCLAW_LOCAL` conserve plusieurs moteurs **strictement locaux** afin de mesurer ce qui fonctionne réellement sur l'Intel Arc B580 12 Go.

La migration vers Architecture V2 **réinitialise la décision de performance** : aucun benchmark d'une ancienne flotte ne qualifie les nouveaux modèles.

## Flotte active V2

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Challenger benchmark hors routage :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Le benchmark nominal utilise 8192 tokens. Le full-agent OpenClaw nominal utilise 16384 tokens. Le second contrat ne constitue pas une promotion du premier.

## Backends déclarés

| ID | Provider OpenClaw | Accélération | Endpoint | Statut |
|---|---|---|---|---|
| `ollama-vulkan` | `ollama` | Vulkan | `127.0.0.1:11434` | nominal / rollback |
| `llama-cpp-sycl` | `intel-sycl` | SYCL -> Level Zero | `127.0.0.1:8080/v1` | candidat |
| `llama-cpp-vulkan` | `intel-vulkan` | Vulkan | `127.0.0.1:8081/v1` | candidat |
| `b580-hybrid` | mixte local | par modèle | Ollama + llama.cpp local | profil candidat |

`nominal` signifie chemin d'installation et de rollback sûr. Cela ne signifie pas qu'Ollama est le moteur le plus rapide pour tous les modèles V2.

## Profil B580 hybride candidat

Le profil mixte ne combine que des moteurs locaux. La répartition concrète est gouvernée par `runtime_versions.json`, `runtime_backends.yaml` et les scripts de configuration. Le runtime Vulkan géré déclare actuellement comme modèles gérés :

```text
gemma4:12b-it-q4_K_M
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Qwen peut rester sur Ollama/Vulkan pendant que Gemma/Ministral sont évalués sur llama.cpp/Vulkan. Cette répartition est une **hypothèse d'exploitation à requalifier**, pas un résultat déjà démontré.

Le profil n'ajoute aucun provider LLM externe.

## Mesures historiques

Des mesures B580 produites avec d'autres modèles peuvent rester utiles pour comprendre la pression mémoire, l'offload et la variabilité des backends. Elles sont **historiques seulement** et ne doivent jamais être copiées dans une attestation de qualification V2.

## Ollama/Vulkan

Ollama reste le chemin nominal et le rollback parce qu'il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- multimodalité Qwen/Gemma ;
- démarrage et récupération ;
- conservation d'un chemin de référence commun aux trois modèles.

API :

```text
http://127.0.0.1:11434
```

Le benchmark direct conserve 8192 tokens. La configuration full-agent OpenClaw gère 16384 tokens pour les trois modèles routés.

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

Les modèles doivent être chargés et mesurés avec leurs identités/quantifications exactes. Un résultat produit avec un ancien artefact ne qualifie pas le runtime V2.

## llama.cpp/Vulkan géré

Le runtime Vulkan candidat :

- utilise la release verrouillée dans `runtime_versions.json` ;
- écoute sur `http://127.0.0.1:8081/v1` ;
- détecte l'Intel Arc B580 ;
- utilise `models_max=1`, `parallel=1`, `gpu_layers=auto` et `fit=on` selon le lanceur ;
- utilise le contexte 8192 ;
- reste `--offline` ;
- suit son PID dans l'état géré ;
- charge Gemma 4 12B et Ministral 3 14B Reasoning dans le profil hybride actuel ;
- décharge explicitement les modèles entre smokes/switches.

Le setup Vulkan arrête le routeur SYCL suivi avant de démarrer afin d'éviter une contention B580 entre deux runtimes llama.cpp.

## Multimodalité

Le profil hybride garde le parcours PDF/images sur les modèles locaux multimodaux :

```text
imageModel/pdfModel
  -> ollama/qwen3.5:9b-q4_K_M
  -> fallback ollama/gemma4:12b-it-q4_K_M
```

Ministral 3 Reasoning reste text-only dans le contrat nominal. Le passage d'une entrée visuelle vers le spécialiste DevOps se fait par ingestion/handoff textuel avec provenance.

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
- contexte benchmark 8K puis stress 16K ;
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

Avant toute promotion, il faut des preuves portant sur **la flotte V2** :

1. B580 détectée et pilote enregistré ;
2. identités/digests des trois modèles routés ;
3. chargement des modèles attendus sur chaque backend ;
4. benchmark isolé reproductible ;
5. configuration OpenClaw valide ;
6. provider attendu prouvé agent par agent ;
7. tool-calling réel avec le spécialiste DevOps ;
8. réparation après erreur d'outil ;
9. multi-agent/E2E sans dépendance LLM externe ;
10. répétitions stables ;
11. contexte soutenable mesuré ;
12. revue humaine.

Le dépôt conserve `default_backend: ollama-vulkan` et `no_automatic_promotion: true` jusqu'à décision humaine.

## Local-only

Tous les endpoints d'inférence gérés sont loopback. Les profils backend n'ont aucune fonction d'escalade vers un modèle en ligne. Si les backends locaux échouent, la qualification échoue : elle ne bascule pas ailleurs.

## Preuves

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-sycl\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan\
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan-probe\
<OPENCLAW_LOCAL_ROOT>\proofs\
<REPO>\benchmarks\results\
```

Les preuves doivent identifier sans ambiguïté le commit, le backend, le modèle, le digest/quantification, le pilote et le protocole réellement utilisés.
