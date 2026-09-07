# Installation Windows 11

## Préconditions

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap, les mises à jour, le téléchargement initial des modèles et les outils Web explicitement utilisés ;
- pilote Intel Arc à jour avant la qualification matérielle.

Python, Node.js, OpenClaw, Ollama et llama.cpp sont contrôlés par les locks versionnés du dépôt.

Architecture V2 est **LLM local-only** : aucun modèle LLM cloud ni fournisseur d'inférence LLM en ligne n'est utilisé par le parcours supporté. Les outils Web peuvent fournir des sources publiques, mais le raisonnement reste exécuté localement.

## Emplacement géré

Si `OPENCLAW_LOCAL_ROOT` n'est pas défini, `E:\AI\OpenClawLocal` est utilisé lorsque `E:` existe, sinon `%LOCALAPPDATA%\OpenClawLocal`.

La racine des modèles Ollama est :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Les scripts configurent `OLLAMA_MODELS` vers cette racine.

## Flotte opérationnelle Architecture V2

Les trois modèles requis et routés sont :

```text
qwen3.5:9b-q4_K_M
gemma4:12b-it-q4_K_M
hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Ils sont Q4_K_M. Les alias logiques restent :

```text
qwen-max        -> qwen3.5:9b-q4_K_M
gemma-deep      -> gemma4:12b-it-q4_K_M
devstral-devops -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Le benchmark direct utilise **8192 tokens** comme contexte nominal. Le full-agent OpenClaw utilise séparément **16384 tokens** comme fenêtre nominale d'orchestration. Les cas 16K du HARD-40M restent du stress benchmark ; le 16K OpenClaw ne constitue pas une promotion du benchmark. Aucune promotion automatique à 32768 n'est autorisée.

## Challenger local séparé

Le dépôt déclare également :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite 4.2 8B est un **challenger de benchmark uniquement** pour le spécialiste DevOps. Il n'est ni routé, ni fallback, ni compté parmi les trois modèles opérationnels, et il ne peut jamais être promu automatiquement.

Il n'est pas téléchargé par le parcours normal des trois modèles routés. Avant la comparaison dédiée :

```powershell
ollama pull granite4.2:8b-q4_K_M
```

Sa présence locale ne modifie pas le routage OpenClaw. Une éventuelle promotion exige des preuves B580 et une décision humaine explicite dans une modification ultérieure du catalogue/routage.

## Nouvelle installation

Depuis PowerShell 7 :

```powershell
git clone https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL.git
cd OPENCLAW_LOCAL

.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Le parcours complet :

1. installe/vérifie les runtimes verrouillés ;
2. crée le Python géré ;
3. configure la racine locale et `OLLAMA_MODELS` ;
4. démarre/vérifie Ollama sur loopback ;
5. télécharge exactement les trois modèles routés ;
6. génère la configuration OpenClaw local-only ;
7. déploie les huit workspaces agents ;
8. vérifie le Gateway et le parcours local.

Aucun échec local ne déclenche une bascule vers un modèle LLM en ligne.

## Migration d'une installation existante

```powershell
git checkout main
git pull

.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Les anciens modèles présents sur disque peuvent rester temporairement pour diagnostic ou historique, mais ils ne sont plus supportés, routés ni considérés comme fallback.

## Installation des modèles routés uniquement

Dry-run :

```powershell
.\scripts\windows\03_pull_models.ps1 -DryRun
```

Réel :

```powershell
.\scripts\windows\03_pull_models.ps1
```

Le script lit `config/v1/model_catalog.yaml` et télécharge uniquement les entrées requises de `models:`. Les entrées `benchmark_challengers:` sont volontairement exclues.

## Vérification locale

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le smoke minimal appelle Ollama sur loopback, utilise le Python géré pour les contrôles d'identité et affiche les métriques `/api/ps` lorsqu'elles sont disponibles. Il ne vaut pas qualification matérielle.

## OpenClaw

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action deploy-agents
```

Le backend nominal/rollback reste `ollama-vulkan` jusqu'à décision explicite fondée sur mesures.

Pour le profil hybride candidat :

```powershell
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
```

Dans le profil hybride actuel, Qwen reste sur Ollama/Vulkan et Gemma 4 + Ministral 3 Reasoning sont évalués sur llama.cpp/Vulkan. Cette répartition est un candidat de qualification, pas un résultat déjà démontré.

## Intel SYCL

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Le routeur utilise un modèle à la fois, `parallel=1`, `gpu_layers=auto` et contexte benchmark 8192.

## Qualification des trois modèles routés

```powershell
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Les trois modèles sont obligatoires. Le HARD-40M conserve 30 cas, dont 24 à 8K et 6 à 16K, avec les seuils existants. Aucun PASS n'est inféré de la seule installation des modèles.

## Comparaison Ministral / Granite

Après installation explicite de Granite :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Cette comparaison produit une preuve de sélection locale mais ne change jamais automatiquement la flotte et ne peut pas contourner un échec HARD-40M.

## Golden Projects

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

## Désinstallation / nettoyage

Avant de supprimer des modèles :

1. vérifier les trois modèles routés ;
2. vérifier `audit`/`verify` ;
3. conserver les preuves historiques utiles ;
4. ne pas supprimer `proofs/`, les états de qualification ou les projets utilisateur ;
5. ne supprimer Granite qu'après conservation de sa preuve comparative si elle a été utilisée pour une décision.

## Qualification B580

La CI prouve les contrats logiciels ; elle ne prouve ni la résidence VRAM, ni le débit, ni la stabilité matérielle de la nouvelle flotte. Ces affirmations restent interdites tant qu'un run réel sur l'Intel Arc B580 n'a pas produit ses preuves avec le commit, les digests/quantifications, le backend, le pilote et les contextes correspondants.
