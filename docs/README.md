# Portail documentaire

| Besoin | Document |
|---|---|
| comprendre la filiation avec `openclaw_openrouter` | [Filiation V7 / Parity Plus](V7_PARITY_PLUS.md) |
| comprendre le système | [Architecture](ARCHITECTURE.md) |
| installer/reproduire le runtime Windows | [Installation Windows 11](INSTALLATION_WINDOWS_11.md) |
| fournir consignes, sources et livrables à OpenClaw | [Project Intake](PROJECT_INTAKE.md) |
| vérifier l'intégrité/immutabilité des entrées | [Intégrité Intake](INTAKE_INTEGRITY.md) |
| transformer un projet flou en projet planifié, vérifié et packagé | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| produire tout en comprenant le projet | [Pédagogie](PEDAGOGY.md) |
| lire la documentation à plusieurs profondeurs | [Accessibilité](ACCESSIBILITY.md) |
| publier un projet GitHub/GitLab avec gates | [Publication projet](PROJECT_PUBLICATION.md) |
| mesurer les agents/backends en usage réel | [Télémétrie](TELEMETRY.md) |
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
3. créer un Project Intake durci + archive canonique
4. ANALYZE : transformer les sources en compréhension structurée
5. CLARIFY : faire trancher les ambiguïtés bloquantes par l'humain
6. PLAN + ASSIGN : créer les tâches et les confier aux rôles OpenClaw
7. EXECUTE : travailler principalement avec les modèles locaux
8. apprendre aux jalons utiles selon efficient/balanced/intensive
9. utiliser le Web pour les faits récents
10. passer en LOCAL_DEEP si une tâche le justifie et si le modèle est qualifié
11. VALIDATE + REVIEW : auditer indépendamment les résultats
12. PACKAGE : produire le ZIP et les hashes
13. COMPLETE : validation humaine finale
14. PUBLICATION : GitHub/GitLab sous machine d'états et preuves distantes
15. TELEMETRY : exploiter les métriques réelles pour optimiser modèles/backends
```

OpenRouter reste hors du parcours automatique : une escalade cloud éventuelle doit continuer à respecter la politique d'escalade et FinOps.

La documentation distingue systématiquement **contrat**, **état observé**, **hypothèse** et **preuve**. Les résultats matériels et E2E réels restent des preuves locales hors Git tant qu'ils n'ont pas été redacted et revus pour publication.
