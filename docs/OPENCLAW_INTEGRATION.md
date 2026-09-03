# Intégration OpenClaw

## Objectif

`OPENCLAW_LOCAL` matérialise huit rôles versionnés dans OpenClaw, avec workspaces séparés, outils bornés, projets synchronisés et routage strictement local-first. Aucun fallback cloud silencieux ni secret n'est injecté dans la configuration.

## Sources de vérité

- `config/v1/runtime_versions.json` : versions des runtimes locaux ;
- `config/v1/model_catalog.yaml` : exactement trois modèles locaux supportés ;
- `config/v1/model_routing.yaml` : routes nominales et fallbacks dans la flotte fermée ;
- `config/v1/runtime_backends.yaml` : profils Ollama, SYCL, Vulkan et hybride ;
- `config/v1/tool_policy.yaml` : permissions par rôle ;
- `config/v1/web_policy.yaml` : Web local-first ;
- `config/v1/document_ingestion_policy.yaml` : PDF/images/Office/texte ;
- `agents/*` : identité et contrat des huit rôles ;
- `src/clawlocal/openclaw_config.py` : génération du patch OpenClaw.

## Flotte locale active

Les alias logiques restent stables afin de préserver les contrats, workspaces et états existants, mais leurs runtimes sont dimensionnés pour l'Intel Arc B580 12 Go :

```text
qwen-max          -> ollama/qwen3.5:9b-q4_K_M
gemma-deep        -> ollama/gemma3:12b-it-q4_K_M
devstral-devops   -> ollama/qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est un **alias de compatibilité** : son runtime actif est Qwen 2.5 Coder 14B. Aucun quatrième modèle local n'est supporté.

## Contrat de contexte

Le contexte nominal OpenClaw est volontairement fixé à **8192 tokens** pour les trois modèles. Le 16K reste une cible de stress dans la qualification matérielle ; il n'est pas promu en contexte nominal sans preuve réelle de stabilité, latence et consommation mémoire.

## Contrat multimodal

- `qwen-max` et `gemma-deep` acceptent texte + image dans le parcours Ollama ;
- `devstral-devops` est **text-only** ;
- `imageModel` et `pdfModel` utilisent `qwen-max`, avec `gemma-deep` en fallback local ;
- lorsqu'une tâche DevOps provient d'un PDF ou d'une image, l'ingestion/multimodalité est effectuée avant le handoff textuel vers le spécialiste DevOps.

Aucun document privé n'est envoyé automatiquement à un provider cloud.

## Contrat de schéma OpenClaw

La configuration est générée pour la version OpenClaw verrouillée dans `config/v1/runtime_versions.json`. Les huit rôles sont matérialisés dans :

```text
agents.list[]
```

Chaque entrée contient notamment son `id`, son workspace, son modèle et sa politique d'outils. `chef-operations` est explicitement l'agent par défaut.

Une montée de version OpenClaw est un changement de contrat : mettre à jour le lock, examiner le schéma vivant, adapter le générateur puis repasser CI, dry-run et E2E.

## Générer et appliquer la configuration

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le parcours :

1. vérifie le backend sélectionné ;
2. crée la baseline OpenClaw si nécessaire ;
3. capture le schéma vivant avec `openclaw config schema` ;
4. déploie les huit workspaces gérés ;
5. génère le patch depuis les contrats ;
6. exécute `openclaw config patch --dry-run` ;
7. applique le patch uniquement si la validation réussit ;
8. exécute `openclaw config validate --json` ;
9. vérifie `openclaw agents list --json`.

Le patch nominal configure notamment :

- Gateway local sur loopback ;
- Ollama sur `http://127.0.0.1:11434` ;
- exactement trois modèles locaux ;
- contexte nominal 8192 ;
- huit agents ;
- `tools.fs.workspaceOnly=true` ;
- `tools.exec.mode=ask` ;
- elevated désactivé ;
- Web local-first ;
- aucun provider LLM cloud sur le chemin nominal.

## Workspaces et projets

Les modèles Ollama sont stockés sous :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Les rôles disposent de workspaces séparés :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>
```

Le projet central reste sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>
```

Les workspaces sont des snapshots jetables et ne remplacent jamais le projet central.

## Document Ingestion et Artifact Exchange

L'ingestion construit des représentations locales traçables sans modifier les originaux : PDF via l'outil `pdf`, images via `view_image`, Office via extraction locale déterministe, texte/code via normalisation locale.

Les sorties des tâches sont versionnées sous `context/exchange/`. Une sortie `PASS` peut être propagée aux dépendants ; une sortie `FAIL` reste historique et ne devient jamais une entrée valide. Provenance et SHA-256 sont conservés.

## Routage nominal

```text
Chef opérations       -> qwen-max
Expert recherche      -> qwen-max + Web
Architecte solutions  -> gemma-deep
Ingénieur DevOps      -> devstral-devops
Ingénieur sécurité    -> qwen-max
Release/Forges        -> qwen-max
Rédacteur technique   -> gemma-deep
Auditeur qualité      -> gemma-deep
                         -> qwen-max si producteur Gemma
```

La séparation producteur/auditeur change de famille lorsque cela est praticable.

## Backends locaux

Trois moteurs sont qualifiables, plus un profil mixte :

- `ollama-vulkan` : chemin nominal et rollback ;
- `llama-cpp-sycl` : candidat Intel Arc ;
- `llama-cpp-vulkan` : candidat Intel Arc ;
- `b580-hybrid` : Qwen sur Ollama, Gemma et Qwen Coder sur llama.cpp/Vulkan.

La migration de flotte **invalide toute conclusion de performance antérieure** pour le choix final du backend. Les nouvelles mesures doivent être produites sur la B580 avec les trois nouveaux runtimes avant toute promotion.

## Gate E2E

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le test doit prouver les huit agents, le provider local attendu, le modèle primaire conforme au catalogue, le vrai tool-calling, la réparation après erreur d'outil, la stabilité et l'absence de dépendance cloud nominale.

## Promotion

Un succès E2E ne promeut automatiquement ni modèle, ni backend, ni V1. La décision reste fondée sur la qualification matérielle, les preuves hashées et la revue humaine.
