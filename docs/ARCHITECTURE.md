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
consignes + sources + livrables
            |
            v
       Project Intake
            |
            v
   Chef des opérations
            |
    +-------+--------+----------------+
    |                |                |
    v                v                v
 Recherche       Architecture       DevOps
    |                |                |
    +------ LOCAL / LOCAL+WEB --------+
                     |
              LOCAL_DEEP si utile
                     |
                insuffisant ?
                |          |
               non        oui
                |          |
                v          v
           livrables   cloud sous
                        politique
                |
                v
         audit indépendant
                |
                v
        validation humaine
```

## Sources de vérité

- `config/v1/platform.yaml` : mode de déploiement et contrats liés ;
- `model_catalog.yaml` : modèles et identifiants runtime ;
- `model_routing.yaml` : routes par agent ;
- `project_policy.yaml` : structure Project Intake ;
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

Le cloud n'apparaît pas dans les fallbacks persistants OpenClaw.

## Découplage modèle / backend

Un alias modèle et un backend d'inférence sont deux axes indépendants. Le projet doit pouvoir comparer Ollama/Vulkan et llama.cpp sans réécrire les huit rôles ni les politiques de projet.

## Contrôles de sécurité structurants

- endpoints locaux en loopback ;
- filesystem borné au workspace ;
- snapshots projet gérés explicitement ;
- exec en mode `ask` ;
- elevated désactivé ;
- rôles de revue sans mutation/exec ;
- recherche Web considérée comme entrée non fiable ;
- cloud désactivé par défaut ;
- budget cloud fail-closed ;
- secrets hors Git et hors requêtes Web ;
- aucune promotion automatique depuis la CI.
