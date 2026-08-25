# OPENCLAW_LOCAL

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
   +--> Gemma 4 12B        rédaction / seconde opinion
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
- **Configuration versionnée** : rôles, modèles, politiques d'escalade, sécurité et profils matériels sont des contrats Git.
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

# 5. Mesurer la machine
.\menu.ps1 -Action benchmark
```

Le raccourci `START_MENU.cmd` ouvre le même centre de contrôle en mode interactif.

## Huit rôles

| Rôle | Mission principale | Route locale de référence | Escalade cloud |
|---|---|---|---|
| Chef des opérations | cadrage, orchestration, risques | Qwen 3.5 9B | arbitrage exceptionnel |
| Expert recherche | recherche, sources, synthèse | Qwen 3.5 9B | recherche web fraîche |
| Architecte solutions | architecture, ADR, compromis | Gemma 4 12B | décision complexe |
| Ingénieur DevOps | CI/CD, IaC, conteneurs, scripts | Qwen 3.5 9B / SERA candidat | blocage technique persistant |
| Ingénieur sécurité | hardening, supply chain, secrets | Qwen 3.5 9B | revue critique |
| Ingénieur release/forges | Git, PR, releases, preuves distantes | Qwen 3.5 9B | exceptionnel |
| Rédacteur technique | README, runbooks, vulgarisation | Gemma 4 12B | document stratégique |
| Auditeur qualité | conformité, preuves, contrôle final | famille différente du producteur | contrôle indépendant si nécessaire |

La source de vérité se trouve dans `config/v1/role_matrix.yaml`, `config/v1/model_routing.yaml` et `config/v1/escalation_policy.yaml`.

## État du projet

Cette première version est un **socle de production contrôlé**, pas une prétention de performance universelle. Les modèles doivent être benchmarkés sur la workstation avant promotion. Voir [STATUS.md](STATUS.md) et [docs/BENCHMARK.md](docs/BENCHMARK.md).

## Documentation

- [Portail documentaire](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows 11](docs/INSTALLATION_WINDOWS_11.md)
- [Modèles locaux](docs/MODELES_LOCAUX.md)
- [Routage hybride](docs/ROUTAGE_HYBRIDE.md)
- [Opérations](docs/OPERATIONS.md)
- [Sécurité](docs/SECURITY.md)
- [Benchmark](docs/BENCHMARK.md)

## Qualité

```powershell
python scripts/21_validate_repository.py
python scripts/22_validate_configs.py
ruff check src tests scripts
pytest -q
```

## Licence

MIT — voir [LICENSE](LICENSE).
