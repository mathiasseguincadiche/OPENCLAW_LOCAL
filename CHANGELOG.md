# Changelog

Toutes les modifications notables sont documentées ici. Le format s'inspire de
Keep a Changelog et le versionnage suit SemVer.

## [Unreleased]

### Added

- Project Orchestrator fail-closed avec machine d'états explicite ;
- analyse structurée, clarifications humaines, plan et assignation de tâches ;
- exécution locale des tâches OpenClaw avec dépendances et tentatives bornées ;
- collecte namespacée des sorties par tâche/agent/tentative ;
- validation et review indépendantes avec retour en correction ;
- boucle de remediation exécutable avec réouverture ciblée des tâches et dépendants transitifs ;
- historique `remediation_history.json` sans remise à zéro des tentatives ;
- arrêt fail-closed lorsque la limite de tentatives impose une intervention humaine ;
- packaging final ZIP avec SHA-256 et approbation humaine obligatoire ;
- Intake renforcé avec archive canonique hors projet, SHA-256, MIME, politique symlink, rapport d'ingestion et lecture seule/ACL Windows ;
- politique pédagogique `efficient` / `balanced` / `intensive` et modes guided/assisted/autonomous/evaluation ;
- artefacts `SKILLS_MATRIX.csv`, `LEARNING_JOURNAL.md`, `TEACH_BACK.md` et `RETENTION_PLAN.yaml` ;
- documentation progressive Comprendre / Utiliser / Approfondir / Diagnostiquer ;
- machine d'états de publication des projets GitHub/GitLab avec preuves locales/distantes et gates humains ;
- télémétrie opérationnelle locale append-only sans prompts, réponses, secrets ni documents privés ;
- writer d'architecture borné à `context/architecture/` et `diagrams/` ;
- validateur `35_validate_v7_parity.py` et documentation de filiation V7.

### Changed

- `project_policy.yaml` couvre désormais tout le cycle jusqu'à `COMPLETE` et référence Intake/Pédagogie/Accessibilité/Publication/Télémétrie ;
- les snapshots de revue peuvent inclure les sorties centrales ;
- le portail projet documente le parcours flou -> livrable -> publication contrôlée ;
- un `FAIL` de validation/review remet réellement les tâches concernées en état exécutable ;
- l'Ingénieur sécurité redevient explicitement read-only pour les modifications de sources ;
- l'Architecte produit ADR et schémas via un writer spécialisé plutôt que via des droits génériques ;
- la CI et le workflow Release exécutent le validateur de parité V7.

### Security

- les documents entrants sont explicitement non fiables et ne peuvent pas redéfinir la politique des agents ;
- les symlinks sont refusés dans l'Intake et ne sont jamais suivis ;
- les secrets potentiels bloquent l'ingestion avant matérialisation du projet ;
- l'Intake et son archive canonique deviennent immuables après création ;
- la télémétrie refuse les contenus privés et les métriques négatives/fabriquées ;
- les publications distantes restent soumises à approbation humaine et preuves observées.

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
