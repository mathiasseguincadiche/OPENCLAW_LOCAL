# Intégration OpenClaw

## Objectif

`OPENCLAW_LOCAL` matérialise réellement les huit rôles versionnés dans OpenClaw. La configuration générée n'active aucun fallback cloud silencieux et ne contient aucun secret.

## Sources de vérité

- `config/v1/model_catalog.yaml` : modèles locaux et routes cloud connues ;
- `config/v1/model_routing.yaml` : route locale primaire, fallback local et escalade cloud par rôle ;
- `config/v1/tool_policy.yaml` : posture outils par rôle ;
- `agents/*` : contrat, identité et posture de chaque agent ;
- `src/clawlocal/openclaw_config.py` : rendu du patch OpenClaw ;
- `src/clawlocal/runtime.py` : pont entre décision `clawlocal` et référence modèle OpenClaw.

## Générer le patch sans l'appliquer

```powershell
$root = if ($env:OPENCLAW_LOCAL_ROOT) { $env:OPENCLAW_LOCAL_ROOT } else { 'E:\AI\OpenClawLocal' }
python .\scripts\26_render_openclaw_config.py `
  --platform-root $root `
  --output .\openclaw.local.patch.json
```

Le patch configure :

- Gateway local sur loopback ;
- API Ollama native `http://127.0.0.1:11434` ;
- Qwen et Gemma avec un contexte conservateur de 16K avant qualification ;
- huit entrées `agents.entries` avec workspaces séparés ;
- fallbacks persistants uniquement entre modèles locaux ;
- `tools.fs.workspaceOnly=true` ;
- `tools.exec.mode=ask` ;
- mode elevated désactivé.

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

## Workspaces gérés

Chaque rôle reçoit un workspace distinct dans :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>
```

Le déploiement assemble :

- `AGENTS.md` = contrat partagé + contrat du rôle ;
- `SOUL.md` ;
- `IDENTITY.md` ;
- `TOOLS.md` ;
- `HEARTBEAT.md` ;
- un `USER.md` public neutre ne contenant aucune donnée personnelle.

Un marqueur `.openclaw-local-managed` protège les répertoires. Le script refuse d'écraser un workspace existant qui n'est pas marqué comme géré par ce projet.

## Routage runtime

Plan local, sans exécution :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Diagnostique ce manifeste Kubernetes.'
```

Exécution locale :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Diagnostique ce manifeste Kubernetes.' `
  --execute
```

Escalade cloud explicite :

```powershell
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'true'
$env:OPENROUTER_API_KEY = '<secret local, jamais Git>'
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Vérifie une information très récente.' `
  --cloud `
  --reason web_freshness `
  --execute
```

L'escalade est refusée si le cloud n'est pas activé, si le motif est absent/inconnu ou si le rôle n'est pas autorisé pour ce motif.

## SERA

`sera-devops` reste un candidat optionnel. Le renderer ne le place pas automatiquement dans la configuration OpenClaw, car son import GGUF et son backend doivent être qualifiés séparément. Il ne peut pas devenir une route active par simple présence dans le catalogue.

## Gate E2E réel

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le test réel vérifie :

- les huit agents via le Gateway ;
- preuve `provider=ollama` sur le parcours nominal ;
- un vrai appel d'outil d'écriture avec `agent exec` ;
- une erreur d'outil contrôlée suivie d'une réparation ;
- trois exécutions locales stables ;
- absence de dépendance cloud sur le parcours nominal.

Les preuves sont écrites sous `<OPENCLAW_LOCAL_ROOT>\proofs\` et restent hors Git.

## Promotion

Un succès E2E ne promeut pas automatiquement un modèle. La promotion exige toujours la qualification matérielle, la revue humaine et les critères de `config/v1/qualification_policy.yaml`.
