# Changelog

Toutes les modifications notables sont documentées ici. Le format s'inspire de
Keep a Changelog et le versionnage suit SemVer.

## [Unreleased]

### Added

- Project Orchestrator fail-closed avec machine d'états explicite ;
- analyse structurée, clarifications humaines, plan et assignation de tâches ;
- exécution locale des tâches OpenClaw avec dépendances et tentatives bornées ;
- collecte namespacée des sorties par tâche/agent/tentative ;
- validation et review indépendantes avec boucle de remediation exécutable ;
- réouverture ciblée des tâches et dépendants transitifs après `FAIL` ;
- historique `remediation_history.json` sans remise à zéro des tentatives ;
- packaging final ZIP avec SHA-256 et approbation humaine obligatoire ;
- **Intake Integrity** : pré-scan secrets, refus des symlinks, SHA-256, inventaire MIME, manifeste et rapport ;
- verrouillage read-only de l'intake avec ACL Windows ou permissions POSIX ;
- politique pédagogique `efficient` / `balanced` / `intensive` ;
- `SKILLS_MATRIX.csv`, `LEARNING_JOURNAL.md`, `TEACH_BACK.md` et `RETENTION_PLAN.yaml` ;
- `PROJECT_GUIDANCE.md` injecté dans le contexte projet ;
- accessibilité documentaire progressive Comprendre / Utiliser / Approfondir / Diagnostiquer ;
- machine d'états de publication projet GitHub/GitLab avec CI, clean clone, audit et approbations ;
- télémétrie opérationnelle locale privacy-first et hors Git ;
- agrégation des routes, agents, modèles, backends, tokens, durée, RAM/VRAM, retries et cloud ;
- scripts `33_project_learning.py`, `34_project_publication.py`, `35_telemetry.py` ;
- validateur `36_validate_v7_parity.py` exécuté par la CI et les releases ;
- documentation Intake Integrity, Learning/Accessibility, Publication et Telemetry.

### Changed

- `project_policy.yaml` couvre désormais orchestration, intégrité intake, pédagogie, accessibilité, publication et télémétrie ;
- les documents entrants sont explicitement traités comme données non fiables ;
- `project.json` enrichi avec classification, criticité, profil pédagogique et intégrité intake ;
- les snapshots de revue peuvent inclure les sorties centrales ;
- un `FAIL` de validation/review remet réellement les tâches concernées en état exécutable ;
- l'Architecte solutions peut produire ADR et schémas mais ne peut pas exécuter de commandes ;
- l'Ingénieur sécurité redevient read-only sur les sources ;
- le routage peut émettre des événements de télémétrie locale sans bloquer l'exécution ;
- la CI vérifie explicitement la non-régression des capacités importantes héritées de `openclaw_openrouter`.

### Security

- secret potentiel dans l'intake = refus avant matérialisation du projet ;
- symlink dans l'intake = refus ;
- intake rendu immuable après génération des métadonnées ;
- prompts, réponses, documents source et secrets interdits dans la télémétrie ;
- métriques matérielles fabriquées interdites ;
- publication distante et états sensibles sous approbation humaine.

## [0.2.0] - 2026-08-27

### Added

- Project Intake avec manifeste, arborescence gérée et snapshots par agent ;
- garde-fou contre les secrets évidents dans l'intake ;
- recherche Web local-first avec raisonnement local ;
- politique d'escalade cloud à préconditions exécutables ;
- budget FinOps quotidien, mensuel et par projet ;
- Qwen 3.5 27B comme candidat LOCAL_DEEP ;
- matrice de backends Ollama/Vulkan, llama.cpp/SYCL et llama.cpp/Vulkan ;
- support de qualification multimodale text/image ;
- diagram-as-code local D2, PlantUML et Graphviz ;
- suite de qualification `devops-v2` ;
- documentation Project Intake, Web, runtime backends, FinOps et diagrammes.

### Changed

- Gemma est désormais épinglé explicitement sur `gemma4:12b` ;
- la fraîcheur Web seule ne déclenche plus Perplexity/Sonar ;
- les modèles téléchargés et smoke-testés sont lus depuis `model_catalog.yaml` ;
- le runner charge la suite déclarée dans `qualification_policy.yaml` ;
- les validateurs couvrent les nouveaux contrats V0.2 ;
- la version plateforme/package passe à `0.2.0`.

### Security

- aucun fallback cloud silencieux ;
- dépassement de budget refusé par défaut ;
- approbation humaine appliquée aux motifs qui l'exigent ;
- snapshots de projet non gérés protégés contre l'écrasement.

## [0.1.0] - 2026-08-25

### Added

- socle `OPENCLAW_LOCAL` local-first sous Windows 11 ;
- gouvernance GitHub, CI, documentation et politique de sécurité ;
- huit rôles multi-agents ;
- catalogue Qwen/Gemma et candidat SERA ;
- routage local avec escalade cloud explicite ;
- profil matériel Intel Arc B580 12 Go ;
- scripts d'audit, configuration, vérification et benchmark ;
- validateurs Python et tests unitaires.
