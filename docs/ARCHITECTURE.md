# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` gère la plateforme IA local-first sous Windows 11 Pro. Il reprend l'ADN de `openclaw_openrouter` — OpenClaw, huit rôles, projets, preuves, validation et gouvernance — en remplaçant le cloud comme chemin nominal par des modèles locaux. WSL2 Ubuntu reste un environnement DevOps/Linux externe : il peut héberger des dépôts et outils Linux, mais il n'est pas l'hôte du runtime IA nominal.

```text
HOST Windows 11 Pro
|
+-- OPENCLAW_LOCAL runtime
|    +-- Python / venv clawlocal
|    +-- Node.js isolé
|    +-- OpenClaw
|    +-- backend IA natif Windows
|
+-- Project Intake durci
|    +-- archive canonique hors projet
|    +-- scan secrets / refus symlinks
|    +-- SHA-256 / MIME / manifest / rapport
|    +-- copie projet et archive read-only / ACL Windows
|
+-- Project Orchestrator
|    +-- ANALYZE / CLARIFY / PLAN / ASSIGN
|    +-- EXECUTE / VALIDATE / REVIEW / PACKAGE
|    +-- remediation + COMPLETE sous validation humaine
|
+-- Capacités projet héritées/améliorées de V7
|    +-- pédagogie efficient/balanced/intensive
|    +-- documentation Comprendre/Utiliser/Approfondir/Diagnostiquer
|    +-- publication GitHub/GitLab gouvernée
|    +-- télémétrie locale privacy-safe
|
+-- OpenClaw / Gateway loopback
|    +-- 8 agents matérialisés
|    +-- 8 workspaces gérés
|    +-- snapshots projet protégés
|    +-- politiques outils par rôle
|    +-- web_search / web_fetch
|    +-- browser pour expert-recherche
|
+-- Pool local
|    +-- LOCAL_FAST
|    |    +-- Qwen 3.5 9B
|    |    +-- Gemma 4 12B
|    +-- LOCAL_DEEP candidats
|         +-- Qwen 3.5 27B
|         +-- SERA 14B
|
+-- Backends
|    +-- Ollama/Vulkan (nominal V0.2)
|    +-- llama.cpp/SYCL (candidat)
|    +-- llama.cpp/Vulkan (candidat)
|
+-- clawlocal control plane
|    +-- contrats / routage / FinOps
|    +-- Project Orchestrator
|    +-- publication / apprentissage / télémétrie
|    +-- writer architecture borné
|    +-- qualification / preuves
|
+-- OpenRouter (optionnel)
|    +-- escalade explicite uniquement
|
+-- WSL2 Ubuntu (externe)
     +-- outils et projets DevOps/Linux
```

## Flux projet principal

```text
consignes + cahier des charges + sources + livrables
                         |
                         v
                Project Intake durci
                         |
                         v
                 Project Orchestrator
                         |
                    ANALYZE
                         |
               ambiguïté bloquante ?
                  |             |
                 oui           non
                  |             |
                  v             |
               CLARIFY <--------+
                  |
                  v
                 PLAN
                  |
                  v
                ASSIGN
                  |
                  v
                EXECUTE
                  |
        +---------+----------+
        |                    |
        v                    v
   agents locaux        expert recherche
                        LOCAL + WEB
        |                    |
        +---------+----------+
                  |
                  v
               VALIDATE
                  |
             PASS ? -- non --> IN_PROGRESS/remediation
                  |
                 oui
                  v
                REVIEW
                  |
             PASS ? -- non --> IN_PROGRESS/remediation
                  |
                 oui
                  v
               PACKAGE
                  |
                  v
          APPROBATION HUMAINE
                  |
                  v
               COMPLETE
                  |
            si publication
                  v
        publication state machine
```

Le cloud n'est **pas** une étape automatique de ce flux. Si une tâche locale justifie une escalade, celle-ci passe par le routeur existant, ses préconditions et FinOps.

## Séparation control plane / agents

Le Project Orchestrator et les modules `clawlocal` constituent un **control plane déterministe** :

- ils contrôlent les états ;
- vérifient les artefacts et preuves ;
- valident les dépendances de tâches ;
- synchronisent les snapshots ;
- lancent OpenClaw ;
- collectent les sorties ;
- conservent les preuves ;
- refusent les transitions invalides ;
- bornent les écritures spécialisées ;
- gouvernent la publication et la télémétrie.

Les modèles restent responsables du contenu sémantique : comprendre les consignes, proposer le plan, exécuter les tâches, analyser les résultats et auditer le travail.

Un modèle ne peut donc pas modifier directement l'état canonique du projet simplement en affirmant qu'une étape est terminée.

## Intake et sources de confiance

Le Project Intake crée une archive canonique sous `state/intake/<project>/<timestamp>/`, puis une copie gérée dans `projects/<id>/intake/`. SHA-256, MIME, manifest et rapport d'ingestion sont conservés. Les documents entrants sont non fiables ; les symlinks sont interdits dans l'Intake et les secrets évidents bloquent la création.

Le dépôt ou les fichiers sous `sources/` restent la vérité de travail pour le code. Les snapshots agents n'autorisent jamais un document entrant à redéfinir les permissions des rôles.

## Pédagogie et documentation

Le contexte projet embarque un profil pédagogique et un profil documentaire. Le profil pédagogique module la part d'explication sans empêcher la livraison. La documentation progressive conserve quatre profondeurs : Comprendre, Utiliser, Approfondir et Diagnostiquer.

Ces éléments sont des **capacités d'accompagnement**, pas des gates artificiels de livraison sauf lorsqu'un projet ou une évaluation les exige explicitement.

## Publication projet

La publication du projet utilisateur possède une machine d'états indépendante de la machine `INTAKE_READY -> COMPLETE`. Elle enregistre les checks locaux, les preuves distantes, la CI, le clone propre, l'audit indépendant, l'URL canonique et le SHA publié.

Le rôle Release/Forge prépare et vérifie ; les opérations distantes sensibles conservent une approbation humaine.

## Permissions spécialisées

L'Ingénieur sécurité est read-only vis-à-vis des modifications de sources : il audite et renvoie les corrections au producteur.

L'Architecte ne dispose pas de droits génériques `write/edit/apply_patch`. Le control plane lui fournit un writer `architecture_scoped` exclusivement pour :

```text
context/architecture/
diagrams/
```

Cela permet de produire ADR et schémas sans ouvrir l'ensemble du workspace à l'écriture architecturale.

## Télémétrie opérationnelle

La télémétrie projet est append-only dans `evidence/telemetry/runs.jsonl`. Elle stocke uniquement des métadonnées et mesures observées : agent, modèle, backend, route, durée et, lorsque disponibles, TTFT, débit, tokens, VRAM/RAM, outils, retries, passage LOCAL_DEEP et coût cloud.

Prompts, réponses, secrets et documents privés sont explicitement exclus.

## Sorties de tâches

Chaque tâche possède un packet dans `context/tasks/<task-id>.json`.

Le workspace de l'agent utilise des racines namespacées :

```text
work/<task-id>
deliverables/<task-id>
evidence/<task-id>
diagrams/<task-id>
```

La collecte centrale produit des runs immuables :

```text
deliverables/tasks/<task-id>/<agent-id>/run-001/
deliverables/tasks/<task-id>/<agent-id>/run-002/
```

La correction d'une tâche ne détruit donc pas la preuve de l'essai précédent.

## Sources de vérité

- `config/v1/platform.yaml` : mode de déploiement et contrats liés ;
- `model_catalog.yaml` : modèles et identifiants runtime ;
- `model_routing.yaml` : routes par agent ;
- `project_policy.yaml` : structure projet et contrats liés ;
- `orchestration_policy.yaml` : transitions et gates du Project Orchestrator ;
- `intake_policy.yaml` : intégrité et immutabilité de l'Intake ;
- `pedagogy_policy.yaml` : profils d'apprentissage ;
- `accessibility_policy.yaml` : profondeur documentaire ;
- `publication_policy.yaml` : publication d'un projet utilisateur ;
- `telemetry_policy.yaml` : métriques opérationnelles ;
- `web_policy.yaml` : recherche Web local-first ;
- `runtime_backends.yaml` : backends d'inférence ;
- `budget_policy.yaml` : limites FinOps ;
- `diagram_policy.yaml` : rendu de schémas ;
- `qualification_policy.yaml` : suites, seuils et règles de promotion ;
- `agents/*` : comportements humainement lisibles ;
- `runtime_versions.json` : versions runtime supportées/préférées.

Le runtime local reste un **état observé**. Les contrats Git décrivent l'état attendu mais ne constituent pas une preuve matérielle.

## Modes de routage

1. **LOCAL_FAST** : parcours quotidien ;
2. **LOCAL + WEB** : recherche/fetch Internet puis raisonnement local ;
3. **LOCAL_DEEP** : modèle plus lourd/offload explicitement disponible ;
4. **LOCAL_SPECIALIST** : modèle spécialisé explicitement qualifié ;
5. **CLOUD_ESCALATION** : dernier niveau, sous motif, préconditions et budget.

Le cloud n'apparaît pas dans les fallbacks persistants OpenClaw et le Project Orchestrator ne l'active pas automatiquement.

## Découplage modèle / backend

Un alias modèle et un backend d'inférence sont deux axes indépendants. Le projet doit pouvoir comparer Ollama/Vulkan et llama.cpp sans réécrire les huit rôles ni les politiques de projet.

## Contrôles de sécurité structurants

- endpoints locaux en loopback ;
- Intake immuable avec preuves d'intégrité ;
- contenus entrants non fiables ;
- filesystem borné au workspace ;
- snapshots projet gérés explicitement ;
- sorties de tâches collectées sans écrasement ;
- transitions projet soumises à des gates ;
- ambiguïtés bloquantes soumises à l'humain ;
- `COMPLETE` soumis à l'humain ;
- exec en mode `ask` ;
- elevated désactivé ;
- sécurité/audit sans mutation directe des sources ;
- architecture via writer borné ;
- recherche Web considérée comme entrée non fiable ;
- publication distante gouvernée ;
- télémétrie sans contenu privé ;
- cloud désactivé par défaut ;
- Project Orchestrator sans auto-escalade cloud ;
- budget cloud fail-closed ;
- secrets hors Git et hors requêtes Web ;
- aucune promotion automatique depuis la CI.
