# Travailler avec différents langages et formats

OPENCLAW_LOCAL peut traiter de nombreux fichiers, mais la méthode de contrôle dépend du langage.

| Type | Exemples | Contrôles typiques |
|---|---|---|
| shell Windows | PowerShell `.ps1` | parsing PowerShell, PSScriptAnalyzer, Pester |
| shell Linux | Bash `.sh` | `bash -n`, ShellCheck si prévu, test d'exécution |
| configuration | YAML/JSON/TOML/INI | parseur + schéma/contrat + test consommateur |
| IaC | Terraform/HCL | `fmt`, `validate`, plan contrôlé |
| conteneurs | Dockerfile/Compose | build/config validation + test runtime |
| Kubernetes/Helm | YAML/templates | render/lint + validation cluster ciblée |
| Python | `.py` | Ruff, mypy selon projet, pytest |
| documentation | Markdown/RST | liens/structure + vérification des commandes et faits |
| données | CSV/TSV/XLSX | structure, types, cohérence et contrôle métier |

## Méthode universelle

1. identifier le langage et le consommateur réel ;
2. lire les conventions du dépôt ;
3. choisir l'agent adapté ;
4. faire une modification minimale ;
5. lancer le contrôle syntaxique ;
6. lancer le contrôle sémantique/runtime ;
7. lancer les régressions ;
8. documenter la preuve.

## Important

Ne demandez pas à l'IA de « convertir » ou « corriger » un fichier sans préciser ce qui doit rester invariant. Pour un langage inconnu du projet, demander d'abord une analyse et les outils de validation disponibles.