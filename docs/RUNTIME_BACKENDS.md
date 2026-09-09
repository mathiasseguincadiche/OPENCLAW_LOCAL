# Backends d'inférence locale

## Décision Architecture V2

Le choix d'accélération GPU LLM pour l'Intel Arc B580 est arrêté : **Vulkan est l'unique voie supportée par le projet actif**.

Le dépôt ne maintient plus de campagne de sélection entre API GPU. Les validations restantes servent à vérifier que la voie Vulkan retenue fonctionne réellement sur la workstation cible, pas à choisir un autre backend.

## Flotte active V2

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Challenger de **modèle** hors routage :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite ne participe pas au choix du backend GPU. Il sert uniquement à une décision humaine séparée sur le spécialiste DevOps.

## Runtimes actifs

| ID | Usage | Endpoint | Statut |
|---|---|---|---|
| `ollama-vulkan` | profil OpenClaw nominal, multimodal, rollback | `127.0.0.1:11434` | supporté |
| `llama-cpp-vulkan` | runtime géré interne du profil hybride | `127.0.0.1:8081/v1` | supporté |
| `b580-hybrid` | profil OpenClaw explicite combinant les deux runtimes Vulkan | Ollama + llama.cpp local | supporté |

`llama-cpp-vulkan` est un runtime interne : il n'est pas exposé comme profil OpenClaw autonome. Les profils OpenClaw sélectionnables sont `ollama-vulkan` et `b580-hybrid`.

## Profil nominal : Ollama/Vulkan

Ollama reste le chemin nominal et le rollback parce qu'il fournit un parcours commun et simple pour :

- les trois modèles routés ;
- l'API locale ;
- la multimodalité Qwen/Gemma ;
- le démarrage et la récupération ;
- la vérification de base de la workstation.

API :

```text
http://127.0.0.1:11434
```

Le benchmark/qualification des modèles utilise 8192 tokens comme contexte nominal. L'orchestration OpenClaw utilise 16384 tokens selon le contrat agent.

## Runtime géré llama.cpp/Vulkan

Le runtime géré :

- utilise la release llama.cpp verrouillée dans `config/v1/runtime_versions.json` ;
- vérifie l'archive par SHA-256 avant exécution ;
- écoute sur `http://127.0.0.1:8081/v1` ;
- détecte explicitement l'Intel Arc B580 ;
- utilise `models_max=1`, `parallel=1`, `gpu_layers=auto` et `fit=on` ;
- utilise le contexte 8192 ;
- reste `--offline` ;
- suit son PID dans l'état géré ;
- réutilise les blobs GGUF locaux exposés par Ollama ;
- décharge explicitement les modèles entre smokes et changements de modèle.

Modèles gérés :

```text
gemma4:12b-it-q4_K_M
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

## Profil `b580-hybrid`

Le profil hybride reste **100 % Vulkan et 100 % local côté LLM** :

```text
qwen-max        -> Ollama/Vulkan
gemma-deep      -> llama.cpp/Vulkan
devstral-devops -> llama.cpp/Vulkan
image/PDF       -> Ollama/Vulkan
```

Le profil permet d'utiliser le runtime llama.cpp géré pour Gemma/Ministral sans perdre la voie multimodale Ollama. Il n'ajoute aucun provider LLM externe.

## Multimodalité

```text
imageModel/pdfModel
  -> ollama/qwen3.5:9b-q4_K_M
  -> fallback ollama/gemma4:12b-it-q4_K_M
```

Ministral 3 Reasoning reste text-only dans le contrat nominal. Le passage d'une entrée visuelle vers le spécialiste DevOps se fait par ingestion/handoff textuel avec provenance.

## Cycle opérateur

### Baseline nominale

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e -Backend ollama-vulkan
```

### Runtime Vulkan géré

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

### Profil hybride

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

### Rollback

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
```

## Ce qui reste à qualifier

Le choix Vulkan n'est plus un sujet de compétition. La qualification réelle doit néanmoins prouver :

1. B580 détectée et pilote enregistré ;
2. identités/digests des trois modèles routés ;
3. chargement des modèles attendus sur le runtime attendu ;
4. configuration OpenClaw valide ;
5. provider attendu prouvé agent par agent ;
6. tool-calling réel avec le spécialiste DevOps ;
7. réparation après erreur d'outil ;
8. multi-agent/E2E sans dépendance LLM externe ;
9. répétitions stables ;
10. contexte soutenable ;
11. comportement de récupération/rollback ;
12. revue humaine.

Ces contrôles peuvent mesurer TTFT, débit, VRAM/RAM ou temps de chargement comme **observabilité de la voie choisie**. Ils ne servent pas à rouvrir la sélection du backend.

## Politique de décision

`config/v1/runtime_backends.yaml` verrouille :

```text
gpu_llm_acceleration = vulkan
backend_choice_locked = true
default_backend       = ollama-vulkan
recommended_profile   = b580-hybrid
rollback_backend      = ollama-vulkan
```

`config/v1/qualification_policy.yaml` impose également :

```text
backend_recomparison_required = false
real_b580_runtime_evidence_required = true
```

Le dépôt conserve `no_automatic_promotion: true` : les preuves matérielles n'autorisent jamais à elles seules une promotion V1.

## Local-only

Tous les endpoints d'inférence gérés sont loopback. Si la voie locale échoue, la qualification échoue : aucun fallback vers un modèle LLM en ligne n'existe.

## Preuves

```text
<OPENCLAW_LOCAL_ROOT>\proofs\intel-vulkan\
<OPENCLAW_LOCAL_ROOT>\proofs\
<REPO>\benchmarks\results\
```

Les preuves doivent identifier sans ambiguïté le commit, le runtime, le modèle, le digest/quantification, le pilote et le protocole réellement utilisés.
