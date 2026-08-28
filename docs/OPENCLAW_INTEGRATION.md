# Intégration OpenClaw

## Objectif

`OPENCLAW_LOCAL` matérialise huit rôles versionnés dans OpenClaw, avec workspaces séparés, outils bornés, projets synchronisés et routage strictement local-first. Aucun fallback cloud silencieux ni secret n'est injecté dans la configuration.

## Sources de vérité

- `config/v1/runtime_versions.json` : version OpenClaw verrouillée ;
- `config/v1/model_catalog.yaml` : exactement trois modèles locaux supportés ;
- `config/v1/model_routing.yaml` : route nominale et fallbacks dans cette flotte fermée ;
- `config/v1/tool_policy.yaml` : permissions par rôle ;
- `config/v1/web_policy.yaml` : Web local-first ;
- `config/v1/project_policy.yaml` : projets et snapshots ;
- `config/v1/document_ingestion_policy.yaml` : PDF/images/Office/texte ;
- `config/v1/artifact_exchange_policy.yaml` : échange versionné ;
- `config/v1/budget_policy.yaml` : FinOps ;
- `agents/*` : identité et contrat des huit rôles ;
- `src/clawlocal/openclaw_config.py` : génération du patch ;
- `src/clawlocal/runtime.py` : résolution des modèles.

## Flotte locale

```text
qwen-max          -> ollama/qwen3.8:27b
gemma-deep        -> ollama/gemma4:26b
devstral-devops   -> ollama/devstral-small-2:24b
```

Aucun quatrième modèle, petit modèle ou candidat legacy n'est supporté.

## Contrat de schéma OpenClaw

La configuration est générée pour la version OpenClaw **réellement verrouillée** dans `config/v1/runtime_versions.json`.

Pour `2026.7.1-2`, les huit rôles sont matérialisés dans :

```text
agents.list[]
```

Chaque entrée contient notamment son `id`, son workspace, son modèle et sa politique d'outils. `chef-operations` est marqué `default: true` afin de ne pas dépendre implicitement de l'ordre de la liste.

Les modèles du provider Ollama utilisent uniquement des clés acceptées par le schéma OpenClaw verrouillé. Les métadonnées propres à `OPENCLAW_LOCAL` restent dans les contrats du dépôt et ne sont pas injectées arbitrairement dans `models.providers.ollama.models[]`.

Une montée de version OpenClaw doit donc être traitée comme un changement de contrat : mettre à jour le runtime lock, examiner le schéma vivant, adapter le générateur et repasser CI + dry-run + E2E.

## Générer le patch

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
- les trois modèles lus depuis `model_catalog.yaml` ;
- contexte prudent avant qualification ;
- `imageModel` et `pdfModel` locaux ;
- huit entrées dans `agents.list` ;
- `chef-operations` comme agent par défaut explicite ;
- workspaces séparés ;
- outils documentaires ;
- fallbacks persistants uniquement dans la flotte supportée ;
- `tools.fs.workspaceOnly=true` ;
- `tools.exec.mode=ask` ;
- elevated désactivé ;
- `web_search` / `web_fetch` ;
- navigateur supplémentaire pour l'Expert recherche.

## Appliquer la configuration

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le parcours :

1. crée la baseline OpenClaw si nécessaire ;
2. capture le schéma vivant avec `openclaw config schema` ;
3. conserve ce schéma sous `<OPENCLAW_LOCAL_ROOT>\runtime\generated\openclaw.schema.json` ;
4. déploie les workspaces gérés ;
5. génère le patch ;
6. exécute `openclaw config patch --dry-run` ;
7. applique uniquement si la validation réussit ;
8. exécute `openclaw config validate --json` ;
9. vérifie `openclaw agents list --json`.

Le transcript affiche `OPENCLAW_SCHEMA=<chemin>` afin que le schéma exact puisse être joint à un diagnostic futur.

## Stockage et workspaces

Les modèles Ollama sont stockés sous :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Chaque rôle dispose de :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>
```

Le déploiement assemble `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md` et le contrat pédagogique partagé. Le marqueur `.openclaw-local-managed` protège les dossiers non gérés.

## Projets et snapshots

Le projet central reste sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>
```

Le snapshot agent est sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\<project-id>
```

`scripts/31_sync_project_context.py` synchronise les données autorisées. Les workspaces restent jetables : ils ne remplacent jamais le projet central.

Le snapshot inclut notamment `intake/`, `sources/`, `context/`, les représentations `context/ingestion/` et les bundles `context/exchange/` destinés à la tâche.

## Document Ingestion

Lors de la création d'un projet, `scripts/28_create_project.py` construit `context/ingestion/index.json`.

```text
intake/original.pdf
        |
        v
SHA-256 + MIME + document_id
        |
        v
context/ingestion/<document-id>/
        +-- metadata.json
        +-- tool.md / extracted.md
```

- PDF : outil `pdf`, lecture bornée et fallback vision lorsque nécessaire ;
- images : `view_image` ;
- DOCX/PPTX/XLSX : extraction locale déterministe ;
- texte/code : normalisation locale ;
- format inconnu : inventaire puis `UNREADABLE` si aucun outil compatible n'est disponible.

L'analyse doit fournir `source_coverage[]`. Un index absent, périmé ou une couverture incomplète bloque l'avancement.

## Artifact Exchange

Après chaque tentative, les sorties sont conservées :

```text
context/exchange/<task-id>/self/run-001/
```

Après `PASS`, elles sont propagées aux dépendants :

```text
context/exchange/<consumer>/dependencies/<producer>/run-001/
```

Chaque bundle contient provenance, tentative, fichiers, SHA-256 et digest agrégé. Les consommateurs ne modifient jamais un bundle en place.

Une correction produit `run-002`, puis les agents affectés sont resynchronisés depuis le projet central. Les transitions vers validation, revue, packaging et completion sont fail-closed si l'échange requis est absent ou corrompu.

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

Les champs de tier servent à exprimer la spécialité et aux diagnostics ; ils ne permettent jamais de sortir de la flotte des trois alias supportés.

## Recherche Internet

```text
expert-recherche local
      -> web_search / web_fetch / browser si nécessaire
      -> sources récentes
      -> synthèse locale
```

La fraîcheur seule n'est pas un motif d'escalade LLM cloud.

## Escalade cloud explicite

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
$env:OPENROUTER_API_KEY = '<secret-local>'

python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Approfondis la recherche à partir des sources collectées.' `
  --cloud `
  --reason deep_web_research `
  --local-web-attempted `
  --project-id p5-devops `
  --execute
```

Une exécution réelle est refusée si une précondition manque. Juste avant l'appel, le routeur effectue une **réservation FinOps atomique**. Le coût observé est ensuite réglé avec l'identifiant de réservation lorsque disponible.

## Backends

- `ollama-vulkan` : chemin nominal avant qualification ;
- `llama-cpp-sycl` : candidat ;
- `llama-cpp-vulkan` : candidat.

Le changement de backend ne change ni les huit rôles ni la flotte supportée. Il exige import, configuration, benchmark et E2E.

## Gate E2E

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le test vérifie notamment les huit agents, le provider local, le modèle primaire conforme au catalogue, le vrai tool-calling, la réparation après erreur d'outil, la stabilité et l'absence de dépendance cloud nominale.

Les preuves restent sous `<OPENCLAW_LOCAL_ROOT>\proofs\`.

## Promotion

Un succès E2E ne modifie pas automatiquement un modèle ou un backend. La décision finale reste fondée sur la qualification matérielle et la revue humaine.
