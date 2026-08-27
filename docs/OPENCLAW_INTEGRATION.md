# Intégration OpenClaw

## Objectif

`OPENCLAW_LOCAL` matérialise huit rôles versionnés dans OpenClaw. La configuration générée privilégie les modèles locaux, active les outils Web et documentaires du parcours nominal et n'incorpore aucun fallback cloud silencieux ni secret.

## Sources de vérité

- `config/v1/model_catalog.yaml` : modèles locaux et routes cloud connues ;
- `config/v1/model_routing.yaml` : routes LOCAL_FAST, LOCAL_DEEP, spécialiste et escalade cloud ;
- `config/v1/tool_policy.yaml` : posture outils par rôle ;
- `config/v1/web_policy.yaml` : recherche/fetch Web local-first ;
- `config/v1/project_policy.yaml` : Project Intake et snapshots ;
- `config/v1/document_ingestion_policy.yaml` : PDF/images/Office/texte et couverture documentaire ;
- `config/v1/artifact_exchange_policy.yaml` : propagation versionnée des productions entre tâches ;
- `config/v1/budget_policy.yaml` : garde-fous FinOps ;
- `agents/*` : contrat, identité et posture de chaque agent ;
- `src/clawlocal/openclaw_config.py` : rendu du patch OpenClaw ;
- `src/clawlocal/runtime.py` : pont entre décision `clawlocal` et référence modèle OpenClaw.

## Générer le patch sans l'appliquer

```powershell
$root = if ($env:OPENCLAW_LOCAL_ROOT) {
  $env:OPENCLAW_LOCAL_ROOT
} else {
  'E:\AI\OpenClawLocal'
}

python .\scripts\26_render_openclaw_config.py `
  --platform-root $root `
  --output .\openclaw.local.patch.json
```

Le patch configure notamment :

- Gateway local sur loopback ;
- API Ollama native `http://127.0.0.1:11434` ;
- modèles Ollama lus depuis `model_catalog.yaml` ;
- contexte conservateur de 16K avant qualification ;
- métadonnées `text` / `image` pour les modèles concernés ;
- `imageModel` local Qwen avec fallback local Gemma ;
- `pdfModel` local Qwen avec fallback local Gemma ;
- limites PDF explicites `pdfMaxBytesMb` et `pdfMaxPages` ;
- huit entrées `agents.entries` avec workspaces séparés ;
- outils `pdf` et `view_image` autorisés pour les huit rôles sans élargir leurs droits d'écriture ;
- fallbacks persistants uniquement entre modèles locaux ;
- `tools.fs.workspaceOnly=true` ;
- `tools.exec.mode=ask` ;
- mode elevated désactivé ;
- `web_search` et `web_fetch` activés ;
- navigateur supplémentaire pour `expert-recherche`.

## Appliquer la configuration

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le parcours réel :

1. crée la baseline OpenClaw si nécessaire ;
2. déploie les workspaces gérés ;
3. génère le patch ;
4. lance `openclaw config patch --dry-run` ;
5. applique le patch seulement si la validation réussit ;
6. exécute `openclaw config validate --json` ;
7. vérifie la flotte avec `openclaw agents list --json`.

## Workspaces et projets

Chaque rôle reçoit un workspace distinct :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>
```

Le déploiement assemble les contrats `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `TOOLS.md` et `HEARTBEAT.md`. Un marqueur `.openclaw-local-managed` empêche l'écrasement d'un workspace non géré.

Pour un projet, `scripts/31_sync_project_context.py` crée en plus un snapshot protégé sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\<project-id>
```

Le snapshot contient `intake/`, `sources/` et `context/`. `context/ingestion/` fournit les représentations documentaires locales et `context/exchange/` transporte les sorties versionnées des tâches amont. Les workspaces restent jetables : le projet central demeure la source de vérité et l'orchestrateur resynchronise les agents concernés après chaque tentative.

Voir `docs/PROJECT_INTAKE.md` et `docs/DOCUMENT_INGESTION_AND_EXCHANGE.md`.

## Documents multimodaux

Lors de la création d'un projet, `scripts/28_create_project.py` construit `context/ingestion/index.json` :

```text
intake/original.pdf
        ↓
SHA-256 + MIME + document_id
        ↓
context/ingestion/<document-id>/
        ├── metadata.json
        └── tool.md / extracted.md
```

- PDF : l'agent utilise `pdf`; les documents longs sont parcourus par tranches et le chemin local peut exploiter le fallback vision pour les pages scannées/pauvres en texte ;
- images : l'agent utilise `view_image` ;
- DOCX/PPTX/XLSX : extraction locale déterministe des parties XML utiles ;
- texte/code : normalisation locale ;
- format inconnu : inventaire puis déclaration explicite `UNREADABLE` si aucun outil compatible n'est disponible.

L'analyse du Chef doit rendre `source_coverage[]` avec une entrée par document. Un index absent/périmé ou une couverture incomplète bloque l'analyse. Les originaux sous `intake/` ne sont jamais modifiés par cette couche.

## Artifact Exchange

Lorsqu'une tâche termine une tentative, ses sorties collectées sont conservées dans l'historique central et publiées dans :

```text
context/exchange/<task-id>/self/run-001/
```

Si la tentative est `PASS`, elles sont également propagées aux tâches dépendantes :

```text
context/exchange/<consumer>/dependencies/<producer>/run-001/
```

Chaque bundle contient un `manifest.json`, les SHA-256 individuels et un digest agrégé. Les consommateurs lisent ces bundles mais ne les modifient jamais en place. Une correction crée `run-002`, `run-003`, etc. Les agents impactés sont resynchronisés automatiquement depuis le projet central.

Les transitions vers validation/revue/packaging/completion sont fail-closed si l'échange attendu est absent ou corrompu.

## Routage runtime

Plan local sans exécution :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Diagnostique ce manifeste Kubernetes.'
```

LOCAL_DEEP lorsqu'un candidat qualifié est réellement disponible :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce problème complexe.' `
  --deep-local-available
```

Le simple fait qu'un modèle existe dans le catalogue ne suffit pas à le rendre disponible : l'opérateur doit avoir importé et qualifié la route correspondante.

## Recherche Internet récente

Une information récente ne déclenche pas OpenRouter par défaut. Le parcours nominal est :

```text
expert-recherche local
      ↓
web_search / web_fetch / browser si nécessaire
      ↓
sources récentes
      ↓
synthèse locale
```

Voir `docs/WEB_LOCAL_FIRST.md`.

## Escalade cloud explicite

Après une tentative Web locale réellement effectuée :

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
$env:OPENROUTER_API_KEY = '<secret local, jamais Git>'

python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis la recherche à partir des sources déjà collectées.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops `
  --execute
```

Le routeur refuse une escalade si :

- le cloud n'est pas activé ;
- le budget n'est pas validé ;
- le motif est absent ou inconnu ;
- le rôle n'est pas autorisé ;
- une précondition n'est pas démontrée ;
- une approbation humaine requise manque.

`web_freshness_only` est un motif explicitement interdit. La Document Ingestion elle-même n'est jamais un motif d'escalade cloud automatique.

## SERA et autres backends

`sera-devops` reste un candidat optionnel. Son import GGUF et son backend doivent être qualifiés séparément.

Les backends `llama-cpp-sycl` et `llama-cpp-vulkan` sont eux aussi des candidats : le renderer nominal V0.2 reste Ollama tant que la comparaison B580 n'a pas produit de preuve en faveur d'un autre backend.

## Gate E2E réel

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le test vérifie :

- les huit agents via le Gateway ;
- preuve `provider=ollama` sur le parcours nominal ;
- modèle primaire lu depuis le catalogue ;
- un vrai appel d'outil d'écriture ;
- une erreur d'outil contrôlée suivie d'une réparation ;
- trois exécutions locales stables ;
- absence de dépendance cloud sur le parcours nominal.

Les contrats CI vérifient en plus le câblage `pdf`/`view_image`, `imageModel`/`pdfModel`, la couverture documentaire et l'Artifact Exchange. Leur qualité sémantique réelle sur PDF/images doit toutefois être qualifiée sur la workstation avec les vrais modèles locaux : GitHub CI ne possède ni l'Arc B580 ni les modèles Ollama de la machine.

Les preuves sont écrites sous `<OPENCLAW_LOCAL_ROOT>\proofs\` et restent hors Git.

## Promotion

Un succès E2E ne promeut pas automatiquement un modèle. La promotion exige encore la qualification matérielle, la stabilité, la revue humaine et les critères de `config/v1/qualification_policy.yaml`.
