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

## Runtime OpenClaw verrouillé

Le runtime supporté est **OpenClaw 2026.9.1** avec le plugin Parallel aligné sur **2026.9.1**.

Le lock conserve l'intégrité SRI du paquet npm et le SHA de release publié afin que `install-core` rejette des octets différents de l'artefact qualifié.

Après une modification du lock runtime, exécuter d'abord :

```powershell
.\menu.ps1 -Action install-core
openclaw --version
```

`configure-openclaw` vérifie ensuite la version verrouillée avant toute mutation. Il ne doit pas compenser une dérive de runtime en abaissant silencieusement les seuils de qualification.

La montée `2026.8.2 -> 2026.9.1` conserve les versions de schéma d'état publiées par OpenClaw (`state=15`, `agent=19`), mais reste traitée comme un changement de runtime complet : plugin Parallel, schéma vivant, admission full-agent et E2E doivent tous être revalidés.

## Flotte locale active

Les alias logiques restent stables afin de préserver les contrats, workspaces et états existants, mais leurs runtimes sont dimensionnés pour l'Intel Arc B580 12 Go :

```text
qwen-max          -> ollama/qwen3.5:9b-q4_K_M
gemma-deep        -> ollama/gemma3:12b-it-q4_K_M
devstral-devops   -> ollama/qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est un **alias de compatibilité** : son runtime actif est Qwen 2.5 Coder 14B. Aucun quatrième modèle local n'est supporté.

## Contrat de contexte : benchmark 8K, agent OpenClaw 16K

Le projet distingue deux notions qui ne doivent pas être confondues :

- **8192 tokens** restent le contexte nominal du benchmark direct B580 et du contrat HARD-40M ;
- **16384 tokens** sont la fenêtre d'exécution nominale du **full agent OpenClaw sur Ollama**, afin d'absorber le prompt système OpenClaw, le contrat du rôle et la surface d'outils autorisée.

Cette fenêtre OpenClaw 16K **n'est pas une promotion des résultats 16K HARD-40M** et ne constitue aucune preuve de performance ou de full-offload sur la B580. Les seuils HARD-40M, les cas 8K/16K et les critères de qualification restent inchangés.

OpenClaw 2026.9.1 considère désormais l'estimation de pression pré-prompt ordinaire comme un signal diagnostique : une estimation conservatrice trop haute n'entraîne pas à elle seule une compaction ou un rejet. Un vrai checkpoint de replay/compaction qui ne tient pas dans la fenêtre canonique peut toujours produire un `context_overflow (precheck)`, ce qui doit rester un échec visible et documenté.

Le provider Ollama de la stable 2026.9.1 utilise en amont une capacité locale par défaut supérieure et le setup automatique exige au moins 16K pour un modèle outillé. `OPENCLAW_LOCAL` conserve néanmoins **16K comme valeur nominale gérée** tant que la B580 n'a pas produit de preuve suffisante pour 32K. Un test 32K éventuel est un **candidat d'orchestration**, pas une promotion du benchmark ni une modification automatique du contrat HARD-40M.

Les trois modèles Ollama sont donc déclarés à `contextWindow=16384`, `contextTokens=16384` et `num_ctx=16384` dans le chemin full-agent nominal, tandis que les runners de benchmark continuent explicitement à exécuter leurs cas 8192/16384 selon le protocole de qualification.

Les anciens overrides `compaction.reserveTokens` et `reserveTokensFloor` ne sont pas réintroduits : le correctif agit sur la vraie capacité du full-agent et sur le volume réellement injecté, pas sur un contournement du precheck.

Les backends candidats `llama-cpp-sycl`, `llama-cpp-vulkan` et `b580-hybrid` conservent leur propre contrat de contexte tant qu'ils n'ont pas produit leur qualification B580.

## Budget du prompt runtime

Le contexte plus large n'est pas utilisé comme unique solution. La surface runtime est également bornée :

- le contrat compact `RUNTIME_CONTRACT.md` + le rôle sont injectés via `AGENTS.md` ;
- `CONTRACT.md` et `PEDAGOGY.md` complets restent disponibles à la demande mais ne sont pas auto-injectés ;
- `SOUL.md`, `USER.md`, `HEARTBEAT.md` et `IDENTITY.md` restent matérialisés dans chaque workspace mais sont exclus de l'injection automatique OpenClaw ;
- `AGENTS.md` reste plafonné à 6500 caractères et le bootstrap runtime géré à 8000 caractères ;
- chaque agent géré reçoit explicitement `skills: []` sur le chemin nominal afin de ne pas injecter des skill cards héritées sans décision de rôle ;
- les profils d'outils partent de `minimal` et réautorisent seulement les capacités nécessaires à chaque rôle ;
- `tools.toolSearch` en mode structuré `tools` diffère les schémas non essentiels derrière la recherche d'outils au lieu de tous les placer dans le prompt initial ;
- `experimental.localModelLean=true` reste activé pour les agents locaux.

La politique de sécurité ne change pas : workspace-only, `exec` soumis au contrat d'approbation, elevated désactivé, et rôles de revue non mutateurs.

## Contrat multimodal

- `qwen-max` et `gemma-deep` acceptent texte + image dans le parcours Ollama ;
- `devstral-devops` est **text-only** ;
- `imageModel` et `pdfModel` utilisent `qwen-max`, avec `gemma-deep` en fallback local ;
- lorsqu'une tâche DevOps provient d'un PDF ou d'une image, l'ingestion/multimodalité est effectuée avant le handoff textuel vers le spécialiste DevOps.

Aucun document privé n'est envoyé automatiquement à un provider cloud.

## Contrat de schéma OpenClaw

Le générateur produit encore le roster sous la surface d'entrée compatible :

```text
agents.list[]
```

OpenClaw 2026.9.x persiste ce roster sous sa représentation canonique :

```text
agents.entries.<agent-id>
```

Le roster est explicitement déclaré `agents.ownership=explicit`, sans marqueur legacy `default=true`. `chef-operations` est déclaré comme propriétaire ambiant et de session via `agents.defaults.systemAgent.agentId` et `agents.defaults.sessionStore.agentId`.

Le E2E accepte `agents.entries` et la surface de compatibilité `agents.list` pour lire l'état, sans modifier le nombre ni l'identité des huit agents.

Une montée de version OpenClaw est un changement de contrat : mettre à jour le lock et son intégrité, examiner le schéma vivant, adapter le générateur puis repasser CI, admission runtime et E2E.

## Générer et appliquer la configuration

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le parcours :

1. vérifie le backend sélectionné ;
2. exige la version OpenClaw verrouillée ;
3. converge le plugin Parallel vers sa version verrouillée ;
4. crée la baseline OpenClaw si nécessaire ;
5. capture le schéma vivant avec `openclaw config schema` ;
6. déploie les huit workspaces gérés ;
7. génère le patch depuis les contrats ;
8. exécute `openclaw config patch --dry-run` ;
9. applique le patch uniquement si la validation réussit ;
10. exécute `openclaw config validate --json` ;
11. vérifie `openclaw agents list --json` ;
12. sur `ollama-vulkan`, exécute un **vrai prompt full-agent** sur Qwen 3.5, Gemma 3 et Qwen 2.5 Coder avant d'annoncer le PASS.

Chaque contrôle d'admission sauvegarde son payload sous `proofs/openclaw_prompt_admission_*.json`. Si OpenClaw refuse encore le prompt, la configuration échoue immédiatement avec l'évidence, au lieu de laisser l'opérateur découvrir le même défaut au E2E suivant. Lorsque le runtime renvoie `systemPromptReport`, les dimensions système/outils/skills sont également affichées.

Les listes gérées sont remplacées intentionnellement via :

```text
--replace-path models.providers
--replace-path agents.list
```

Le patch nominal Ollama configure notamment :

- Gateway local sur loopback ;
- Ollama sur `http://127.0.0.1:11434` ;
- exactement trois modèles locaux ;
- benchmark direct nominal 8192 ;
- full-agent OpenClaw Ollama 16384 ;
- huit agents ;
- ownership explicite ;
- `skills: []` par agent nominal ;
- `experimental.localModelLean=true` ;
- profils d'outils minimaux et Tool Search structuré ;
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

Le gate d'admission de `configure-openclaw` réduit fortement les boucles de diagnostic, mais ne remplace pas le E2E : le E2E reste nécessaire pour les huit rôles et les parcours d'outils réels.

## Promotion

Un succès d'admission ou E2E ne promeut automatiquement ni modèle, ni backend, ni V1. La décision reste fondée sur la qualification matérielle, les preuves hashées et la revue humaine.
