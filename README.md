# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

Le principe est simple : **le local absorbe le volume de travail ; le cloud devient une escalade explicite** pour les cas qui exigent recherche fraîche, contexte très large, arbitrage de haut niveau ou contrôle indépendant renforcé.

## Architecture

```text
Utilisateur
   |
   v
OpenClaw ------------------------------+
   |                                    |
   |                                    +--> Cloud optionnel
   |                                         OpenRouter
   |                                         - recherche fraîche
   v                                         - arbitrage complexe
Ollama natif Windows                         - dernier recours
   |
   +--> Qwen 3.5 9B        généraliste
   +--> Gemma 4            rédaction / seconde opinion
   +--> SERA 14B (*)       candidat spécialiste code/DevOps
   |
   v
8 agents spécialisés
   |
   +--> contrats / routage / escalade / preuves
        gérés par `clawlocal`
```

> `(*)` SERA 14B est déclaré comme candidat local optionnel : il doit être importé et validé sur la machine cible avant d'être activé comme route de production.

## Principes de conception

- **Windows natif** pour OpenClaw, le Gateway et les moteurs IA locaux ; WSL2 reste un backend DevOps externe et facultatif.
- **Local-first** : aucune dépendance cloud n'est requise pour le parcours nominal.
- **Cloud-on-demand** : les routes cloud sont désactivées tant qu'elles ne sont pas explicitement activées et configurées.
- **Séparation des responsabilités** : les huit agents gardent des rôles distincts ; un producteur ne s'auto-audite pas.
- **Fail closed** : une escalade non autorisée, un modèle absent ou une configuration invalide doit échouer explicitement.
- **Preuves avant promesses** : le dépôt distingue ce qui est implémenté, testé, candidat ou simplement documenté.
- **Configuration versionnée** : rôles, modèles, politiques d'escalade, qualification, sécurité et profils matériels sont des contrats Git.
- **État local hors Git** : modèles téléchargés, secrets, journaux, benchmarks et caches restent sur la workstation.

## Démarrage rapide

Prérequis : Windows 11 Pro x64, PowerShell 7, Python 3.12+ et OpenClaw. Ollama est le backend local de référence.

```powershell
# 1. Audit sans mutation
.\menu.ps1 -Action audit

# 2. Préparer le backend local
.\menu.ps1 -Action configure-local -DryRun
.\menu.ps1 -Action configure-local

# 3. Télécharger les modèles déclarés par défaut
.\menu.ps1 -Action models

# 4. Vérifier l'inférence locale
.\menu.ps1 -Action verify

# 5. Mesure simple
.\menu.ps1 -Action benchmark

# 6. Qualification matérielle complète, sans cloud
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le raccourci `START_MENU.cmd` ouvre le même centre de contrôle en mode interactif.

## Qualification avant promotion

Les modèles restent `candidate` tant qu'ils n'ont pas été mesurés sur la workstation réelle. La phase 2 fournit maintenant un protocole reproductible : inventaire, suite DevOps versionnée, TTFT, débit, contextes 8K/16K et gate automatique. Un gate réussi produit uniquement `READY_FOR_MANUAL_QUALIFICATION` : le tool-calling OpenClaw réel, la stabilité et la revue humaine restent obligatoires.

Voir [Qualification](docs/QUALIFICATION.md) et [Benchmark](docs/BENCHMARK.md).

## Huit rôles

| Rôle | Mission principale | Route locale de référence | Escalade cloud |
|---|---|---|---|
| Chef des opérations | cadrage, orchestration, risques | Qwen 3.5 9B | arbitrage exceptionnel |
| Expert recherche | recherche, sources, synthèse | Qwen 3.5 9B | recherche web fraîche |
| Architecte solutions | architecture, ADR, compromis | Gemma 4 | décision complexe |
| Ingénieur DevOps | CI/CD, IaC, conteneurs, scripts | Qwen 3.5 9B / SERA candidat | blocage technique persistant |
| Ingénieur sécurité | hardening, supply chain, secrets | Qwen 3.5 9B | revue critique |
| Ingénieur release/forges | Git, PR, releases, preuves distantes | Qwen 3.5 9B | exceptionnel |
| Rédacteur technique | README, runbooks, vulgarisation | Gemma 4 | document stratégique |
| Auditeur qualité | conformité, preuves, contrôle final | famille différente du producteur | contrôle indépendant si nécessaire |

La source de vérité se trouve dans `config/v1/role_matrix.yaml`, `config/v1/model_routing.yaml`, `config/v1/escalation_policy.yaml` et `config/v1/qualification_policy.yaml`.

## État du projet

La version actuelle est un **socle de production contrôlé avec outillage de qualification**, pas une prétention de performance universelle. Aucun résultat matériel n'est déclaré tant que la suite n'a pas été exécutée sur la workstation. Voir [STATUS.md](STATUS.md).

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows 11](docs/INSTALLATION_WINDOWS_11.md)
- [Modèles locaux](docs/MODELES_LOCAUX.md)
- [Routage hybride](docs/ROUTAGE_HYBRIDE.md)
- [Qualification](docs/QUALIFICATION.md)
- [Opérations](docs/OPERATIONS.md)
- [Sécurité](docs/SECURITY.md)
- [Benchmark](docs/BENCHMARK.md)
- [Gouvernance GitHub](docs/GITHUB_GOVERNANCE.md)

## Qualité et sécurité

La CI vérifie Python **et** PowerShell 7. Le code Python passe les validateurs, Ruff, Pytest et CodeQL ; les scripts Windows passent le parseur PowerShell, PSScriptAnalyzer et Pester. Les changements de dépendances sont contrôlés par Dependency Review.

```powershell
python scripts/21_validate_repository.py
python scripts/22_validate_configs.py
python scripts/24_validate_release.py
ruff check src tests scripts
pytest -q

Invoke-ScriptAnalyzer -Path .\scripts\windows -Recurse `
  -Settings .\.github\powershell\PSScriptAnalyzerSettings.psd1
Invoke-Pester -Path .\tests\powershell -CI
```

## Releases

Le versionnage suit SemVer. `VERSION`, `pyproject.toml` et `CHANGELOG.md` doivent rester cohérents. Un tag `v<VERSION>` déclenche le workflow `Release`, qui revalide le dépôt avant de publier les artefacts Python et leurs sommes SHA-256.

La version `1.0.0` reste réservée à un parcours local réellement qualifié sur la workstation cible.

## Licence

MIT — voir [LICENSE](LICENSE).
