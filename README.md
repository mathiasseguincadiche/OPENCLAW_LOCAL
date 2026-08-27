# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64.

Le local absorbe le parcours nominal. Le cloud n'est jamais un fallback silencieux : il n'est accessible qu'après une décision d'escalade explicite, un motif autorisé et une activation volontaire.

## Architecture

```text
Utilisateur
   |
   v
OpenClaw / Gateway loopback
   |
   +--> 8 agents réellement matérialisés
   |      +-- workspaces séparés
   |      +-- politiques outils par rôle
   |      +-- fallbacks persistants uniquement locaux
   |
   +--> Ollama natif Windows
   |      +-- Qwen 3.5 9B
   |      +-- Gemma 4
   |      +-- SERA 14B (*) candidat optionnel
   |
   +--> clawlocal
          +-- renderer OpenClaw
          +-- routage local/cloud explicite
          +-- benchmark / qualification / preuves
          |
          +--> OpenRouter uniquement sur escalade autorisée
```

> `(*)` SERA 14B n'est pas activé automatiquement : son import/backend et sa qualification sont séparés.

## Principes de conception

- **Windows natif** pour OpenClaw, Gateway, Ollama et les modèles ; WSL2 reste externe/facultatif.
- **Installation reproductible** : versions runtime centralisées dans `config/v1/runtime_versions.json`.
- **Intégrité vérifiée** : Node.js par SHA-256 et package OpenClaw par SHA-512/SRI.
- **Local-first** : aucune dépendance cloud n'est requise pour le parcours nominal.
- **Cloud-on-demand** : activation + motif + rôle autorisé + secret local pour une exécution réelle.
- **Huit rôles distincts** : séparation producteur/relecteur et permissions d'outils par agent.
- **Fail closed** : modèle, runtime, config ou escalade non conforme échoue explicitement.
- **Workspaces confinés** : filesystem limité au workspace ; exec soumis à approbation ; elevated désactivé.
- **Preuves avant promesses** : aucun résultat B580 ni tool-calling n'est déclaré avant exécution réelle.
- **État local hors Git** : modèles, secrets, sessions, logs, benchmarks et preuves restent sur la workstation.

## Démarrage rapide

Prérequis utilisateur : **Windows 11 Pro x64, PowerShell 7 et WinGet**. Python, Node.js, OpenClaw et Ollama peuvent être provisionnés par le dépôt.

```powershell
# 1. Prévisualiser l'installation complète
.\menu.ps1 -Action install-full -DryRun

# 2. Installer runtime + Ollama + modèles + OpenClaw + 8 agents + Gateway
.\menu.ps1 -Action install-full

# 3. Vérifier le parcours local
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify

# 4. Vérifier réellement OpenClaw/tool-calling/réparation/stabilité
.\menu.ps1 -Action e2e

# 5. Qualifier les modèles sur la machine cible
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Pour ne préparer que les runtimes :

```powershell
.\menu.ps1 -Action install-core -DryRun
.\menu.ps1 -Action install-core
```

Le raccourci `START_MENU.cmd` ouvre le centre de contrôle interactif.

## Flotte OpenClaw

Les contrats Git sont rendus en configuration OpenClaw par `src/clawlocal/openclaw_config.py`. Chaque agent dispose d'un workspace géré sous `<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>`.

| Rôle | Mission principale | Route locale de référence | Escalade cloud |
|---|---|---|---|
| Chef des opérations | cadrage, orchestration, risques | Qwen 3.5 9B | arbitrage exceptionnel |
| Expert recherche | recherche, sources, synthèse | Qwen 3.5 9B | recherche web fraîche |
| Architecte solutions | architecture, ADR, compromis | Gemma 4 | décision complexe |
| Ingénieur DevOps | CI/CD, IaC, conteneurs, scripts | Qwen 3.5 9B / SERA candidat | blocage persistant |
| Ingénieur sécurité | hardening, supply chain, secrets | Qwen 3.5 9B | revue critique |
| Ingénieur release/forges | Git, PR, releases, preuves distantes | Qwen 3.5 9B | exceptionnel |
| Rédacteur technique | README, runbooks, vulgarisation | Gemma 4 | document stratégique |
| Auditeur qualité | conformité, preuves, contrôle final | famille locale distincte si possible | contrôle indépendant |

Les rôles et permissions viennent de `role_matrix.yaml`, `model_routing.yaml`, `tool_policy.yaml` et `escalation_policy.yaml`.

## Routage exécutable

Plan local sans exécution :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message 'Analyse ce problème Kubernetes.'
```

Le même parcours avec `--execute` appelle explicitement `openclaw agent --agent ... --model ollama/...`.

Une route cloud exige `--cloud --reason <motif>`, `OPENCLAW_LOCAL_CLOUD_ENABLED=true` et, lors de l'exécution, `OPENROUTER_API_KEY`. Le secret n'est jamais généré ni écrit dans le dépôt.

## Qualification avant promotion

Les modèles restent `candidate` jusqu'à preuve sur la workstation réelle.

Deux gates complémentaires existent :

1. **E2E OpenClaw réel** : huit agents, provider Ollama, vrai appel d'outil, correction après erreur, trois runs stables ;
2. **qualification matérielle** : inventaire, suite DevOps, TTFT, débit, contextes 8K/16K et seuils versionnés.

Un succès automatique signifie au mieux `READY_FOR_MANUAL_QUALIFICATION`. Aucune CI et aucun script ne promeuvent un modèle automatiquement.

Voir [Qualification](docs/QUALIFICATION.md), [Intégration OpenClaw](docs/OPENCLAW_INTEGRATION.md) et [Benchmark](docs/BENCHMARK.md).

## État du projet

Le dépôt contient maintenant le socle, le durcissement GitHub, l'installateur reproductible, la flotte OpenClaw et les gates d'exécution. **Les résultats matériels réels restent volontairement en attente de la workstation cible.** Voir [STATUS.md](STATUS.md).

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows 11](docs/INSTALLATION_WINDOWS_11.md)
- [Intégration OpenClaw](docs/OPENCLAW_INTEGRATION.md)
- [Modèles locaux](docs/MODELES_LOCAUX.md)
- [Routage hybride](docs/ROUTAGE_HYBRIDE.md)
- [Qualification](docs/QUALIFICATION.md)
- [Opérations](docs/OPERATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Sécurité](docs/SECURITY.md)
- [Benchmark](docs/BENCHMARK.md)
- [Gouvernance GitHub](docs/GITHUB_GOVERNANCE.md)

## Qualité et sécurité

La CI couvre :

```text
Python 3.12 + 3.13
Ruff
mypy
Pytest + coverage >= 75 %
validateurs dépôt/config/version
PowerShell 7
PSScriptAnalyzer
Pester
CodeQL
Dependency Review / pip-audit fallback
```

Commandes locales principales :

```powershell
python scripts/21_validate_repository.py
python scripts/22_validate_configs.py
python scripts/24_validate_release.py
ruff check src tests scripts
mypy src
pytest -q --cov=clawlocal --cov-report=term-missing --cov-fail-under=75

Invoke-ScriptAnalyzer -Path .\scripts\windows -Recurse `
  -Settings .\.github\powershell\PSScriptAnalyzerSettings.psd1
Invoke-Pester -Path .\tests\powershell -CI
```

## Releases

Le versionnage suit SemVer. `VERSION`, `pyproject.toml` et `CHANGELOG.md` doivent rester cohérents.

Un tag `v<VERSION>` déclenche une release qui :

- revalide Python et PowerShell ;
- construit wheel + sdist ;
- génère un **SBOM CycloneDX 1.6** ;
- calcule les sommes SHA-256 ;
- produit des **attestations GitHub de provenance et de SBOM** ;
- publie les artefacts seulement si tous les gates passent.

La version `1.0.0` reste réservée à un parcours local réellement qualifié sur la workstation cible.

## Licence

MIT — voir [LICENSE](LICENSE).
