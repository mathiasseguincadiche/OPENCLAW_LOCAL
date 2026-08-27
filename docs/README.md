# Portail documentaire

| Besoin | Document |
|---|---|
| comprendre le système | [Architecture](ARCHITECTURE.md) |
| installer/reproduire le runtime Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| fournir consignes, sources et livrables à OpenClaw | [Project Intake](PROJECT_INTAKE.md) |
| transformer un projet flou en projet planifié, vérifié et packagé | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| comprendre la flotte OpenClaw et le routage runtime | [Intégration OpenClaw](OPENCLAW_INTEGRATION.md) |
| utiliser Internet sans basculer automatiquement dans le cloud | [Recherche Web Local-First](WEB_LOCAL_FIRST.md) |
| comprendre Ollama/Vulkan et les candidats llama.cpp | [Backends locaux](RUNTIME_BACKENDS.md) |
| choisir/qualifier les modèles | [Modèles locaux](MODELES_LOCAUX.md) |
| comprendre l'escalade | [Routage hybride](ROUTAGE_HYBRIDE.md) |
| contrôler les dépenses OpenRouter | [FinOps](FINOPS.md) |
| produire des schémas techniques locaux | [Diagrammes](DIAGRAMMES.md) |
| mesurer la machine et les modèles | [Benchmark](BENCHMARK.md) |
| exécuter la qualification réelle | [Qualification](QUALIFICATION.md) |
| exploiter au quotidien | [Opérations](OPERATIONS.md) |
| sécurité | [Sécurité](SECURITY.md) |
| dépanner, sauvegarder, rollback, désinstaller | [Troubleshooting](TROUBLESHOOTING.md) |
| gouvernance, protection de main et releases | [Gouvernance GitHub](GITHUB_GOVERNANCE.md) |
| décisions structurantes | [ADR](ADR/README.md) |

## Parcours projet recommandé

```text
1. installer / auditer Windows
2. qualifier le runtime local
3. créer un Project Intake
4. ANALYZE : transformer les sources en compréhension structurée
5. CLARIFY : faire trancher les ambiguïtés bloquantes par l'humain
6. PLAN + ASSIGN : créer les tâches et les confier aux rôles OpenClaw
7. EXECUTE : travailler principalement avec les modèles locaux
8. utiliser le Web pour les faits récents
9. passer en LOCAL_DEEP si une tâche le justifie et si le modèle est qualifié
10. VALIDATE + REVIEW : auditer indépendamment les résultats
11. PACKAGE : produire le ZIP et les hashes
12. COMPLETE : validation humaine finale
```

OpenRouter reste hors du parcours automatique : une escalade cloud éventuelle doit continuer à respecter la politique d'escalade et FinOps.

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**. Les résultats matériels et E2E réels restent des preuves locales hors Git tant qu'ils n'ont pas été redacted et revus pour publication.
