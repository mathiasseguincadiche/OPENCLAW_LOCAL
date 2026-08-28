# Artefacts — référence rapide

| Fichier/dossier | Rôle |
|---|---|
| `context/project_analysis.json` | compréhension du besoin |
| `context/clarifications.json` | questions/décisions humaines |
| `context/project_plan.json` | plan des tâches |
| `context/task_assignments.json` | propriétaires |
| `evidence/task_results.json` | résultats de tâches |
| `evidence/<task-id>/web_evidence.json` | fraîcheur, autorité, corroboration, confiance et preuve runtime des faits Web requis |
| `evidence/validation_report.json` | validation |
| `evidence/review_report.json` | revue |
| `deliverables/package_manifest.json` | contenu du package |
| `evidence/final_report.json` | synthèse finale |
| `context/exchange/.../run-NNN` | échanges versionnés |

Les noms sont des contrats du projet ; ne modifiez pas les bundles d'échange en place. Une tâche dont `required_evidence` contient `web_evidence` ne peut pas être considérée comme terminée sans un `web_evidence.json` valide.
