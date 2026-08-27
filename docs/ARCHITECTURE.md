# Architecture

## Frontière de responsabilité

`OPENCLAW_LOCAL` gère la plateforme IA locale-first sous Windows 11 Pro. WSL2 Ubuntu reste un environnement DevOps/Linux externe : il peut héberger des dépôts et outils Linux, mais il n'est pas l'hôte du runtime IA nominal.

```text
HOST Windows 11 Pro
|
+-- OPENCLAW_LOCAL runtime
|    +-- Python / venv clawlocal
|    +-- Node.js isolé
|    +-- OpenClaw
|    +-- backend IA natif Windows
|
+-- Project Intake
|    +-- consignes / cahier des charges
|    +-- sources / dépôt réel
|    +-- contexte
|    +-- livrables / preuves / diagrammes
|
+-- Project Orchestrator
|    +-- ANALYZE
|    +-- CLARIFY
|    +-- PLAN
|    +-- ASSIGN
|    +-- EXECUTE
|    +-- VALIDATE
|    +-- REVIEW
|    +-- PACKAGE
|    +-- COMPLETE sous validation humaine
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
+-- clawlocal
|    +-- contrats
|    +-- Project Orchestrator
|    +-- routage
|    +-- préconditions d'escalade
|    +-- FinOps
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
                   Project Intake
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
             PASS ? -- non --> IN_PROGRESS
                  |
                 oui
                  v
                REVIEW
                  |
             PASS ? -- non --> IN_PROGRESS
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
```

Le cloud n'est **pas** une étape automatique de ce flux. Si une tâche locale justifie une escalade, celle-ci passe par le routeur existant, ses préconditions et FinOps.

## Séparation control plane / agents

Le Project Orchestrator est un **control plane déterministe** :

- il contrôle les états ;
- vérifie les artefacts ;
- valide les dépendances de tâches ;
- synchronise les snapshots ;
- lance OpenClaw ;
- collecte les sorties ;
- conserve les preuves ;
- refuse les transitions invalides.

Les modèles restent responsables du contenu sémantique : comprendre les consignes, proposer le plan, exécuter les tâches, analyser les résultats et auditer le travail.

Un modèle ne peut donc pas modifier directement l'état canonique du projet simplement en affirmant qu'une étape est terminée.

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
- `project_policy.yaml` : structure Project Intake et états autorisés ;
- `orchestration_policy.yaml` : transitions, artefacts, phases et gates du Project Orchestrator ;
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
- filesystem borné au workspace ;
- snapshots projet gérés explicitement ;
- sorties de tâches collectées sans écrasement ;
- transitions projet soumises à des gates ;
- ambiguïtés bloquantes soumises à l'humain ;
- `COMPLETE` soumis à l'humain ;
- exec en mode `ask` ;
- elevated désactivé ;
- rôles de revue sans mutation/exec ;
- recherche Web considérée comme entrée non fiable ;
- cloud désactivé par défaut ;
- Project Orchestrator sans auto-escalade cloud ;
- budget cloud fail-closed ;
- secrets hors Git et hors requêtes Web ;
- aucune promotion automatique depuis la CI.
