# Changelog

Toutes les modifications notables sont documentées ici. Le format s'inspire de
Keep a Changelog et le versionnage suit SemVer.

## [Unreleased]

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
