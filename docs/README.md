# Portail documentaire

| Besoin | Document |
|---|---|
| comprendre le système | [Architecture](ARCHITECTURE.md) |
| installer/reproduire le runtime Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| fournir consignes, sources et livrables à OpenClaw | [Project Intake](PROJECT_INTAKE.md) |
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

## Parcours V0.2 recommandé

```text
1. installer / auditer Windows
2. qualifier le runtime local
3. créer un Project Intake
4. synchroniser le contexte vers les 8 agents
5. travailler localement
6. utiliser le Web pour les faits récents
7. passer en LOCAL_DEEP si nécessaire
8. n'escalader vers OpenRouter que sous politique + budget
9. produire preuves, documentation et diagrammes
10. auditer avant validation humaine
```

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**. Les résultats matériels et E2E réels restent des preuves locales hors Git tant qu'ils n'ont pas été redacted et revus pour publication.
