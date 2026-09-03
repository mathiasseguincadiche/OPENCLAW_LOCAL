# OPENCLAW_LOCAL

[![CI](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/ci.yml)
[![CodeQL](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml/badge.svg)](https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PowerShell 7](https://img.shields.io/badge/PowerShell-7%2B-blue.svg)](https://learn.microsoft.com/powershell/)
[![Python 3.12-3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

Plateforme IA **local-first, multi-agents et multi-modèles** pour Windows 11 Pro x64, conçue pour la workstation cible **AMD Ryzen 7 7700 + Intel Arc B580 12 Go**.

`OPENCLAW_LOCAL` combine OpenClaw, huit rôles spécialisés, Project Intake, orchestration fail-closed, preuves, télémétrie locale et publication gouvernée. OpenRouter n'est jamais un fallback silencieux : toute escalade cloud reste explicite, budgétée et traçable.

## Flotte locale B580 right-sized

La flotte supportée contient exactement trois modèles Q4_K_M :

| Alias logique | Runtime | Taille registre indicative | Usage nominal |
|---|---|---:|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | ~6,6 Go | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | ~8,1 Go | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | ~9,0 Go | DevOps, code, dépôts, édition multi-fichiers |

`devstral-devops` est conservé comme alias logique de compatibilité ; le runtime réel est désormais Qwen2.5 Coder 14B. Ce spécialiste est text-only. Les tâches DevOps nécessitant une image ou un PDF reçoivent un handoff traçable depuis Qwen 3.5 ou Gemma 3.

Le **contexte nominal est 8192 tokens**. Le contexte 16384 reste un stress de qualification et n'est pas promu automatiquement.

Cette flotte remplace l'ancienne stratégie 24–27B après mesures réelles montrant un offload CPU/GPU important sur la B580 12 Go. Le changement vise un meilleur ajustement matériel ; il ne constitue pas une preuve de débit ou de résidence VRAM complète avant nouvelle qualification.

## Huit rôles

```text
chef-operations             -> Qwen 3.5 9B
expert-recherche            -> Qwen 3.5 9B + Web
architecte-solutions        -> Gemma 3 12B
ingenieur-devops            -> Qwen 2.5 Coder 14B
ingenieur-securite          -> Qwen 3.5 9B
ingenieur-release-forges    -> Qwen 3.5 9B
redacteur-technique         -> Gemma 3 12B
auditeur-qualite            -> Gemma 3 12B
                               -> Qwen 3.5 9B si producteur Gemma
```

Les rôles restent distincts et soumis à leurs scopes d'outils. Le Workspace Guard, les règles de producer/reviewer et les gates V1 ne sont pas affaiblis par le changement de modèles.

## Architecture générale

```text
Consignes / PDF / images / Office / code / ZIP
                     |
                     v
          Project Intake durci
  SHA-256 / MIME / liens / secrets / ACL
                     |
                     v
         Document Ingestion locale
                     |
                     v
          Project Orchestrator
 ANALYZE -> CLARIFY -> PLAN -> ASSIGN
 -> EXECUTE -> VALIDATE -> REVIEW -> PACKAGE
                     |
                     v
        Artifact Exchange versionné
                     |
                     v
          OpenClaw / Gateway local
                     |
             8 agents spécialisés
                     |
      +--------------+--------------+
      |              |              |
   Qwen 3.5       Gemma 3       Qwen Coder
      |              |              |
      +--------------+--------------+
                     |
               preuves locales
```

## Prérequis

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- WinGet ;
- Git ;
- connexion Internet pour le bootstrap et le téléchargement initial ;
- espace disque suffisant pour les trois modèles, runtimes et preuves.

Python, Node.js, OpenClaw et Ollama sont contrôlés par le runtime lock du dépôt.

## Installation

```powershell
git clone https://github.com/mathiasseguincadiche/OPENCLAW_LOCAL.git
cd OPENCLAW_LOCAL

.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Par défaut, la plateforme gérée est placée sous `E:\AI\OpenClawLocal` si `E:` existe, sinon sous `%LOCALAPPDATA%\OpenClawLocal`. `OPENCLAW_LOCAL_ROOT` peut surcharger cet emplacement.

Sur une installation existante après changement de flotte :

```powershell
git pull
.\menu.ps1 -Action configure-local
.\scripts\windows\03_pull_models.ps1
```

Les anciens modèles éventuellement présents dans le cache Ollama ne sont plus routés par le catalogue actif. Leur suppression n'est pas requise avant validation de la nouvelle flotte.

## Vérification opérateur

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
```

Ces commandes doivent vérifier notamment :

- runtime verrouillé ;
- Ollama sur loopback ;
- exactement trois modèles requis ;
- huit agents OpenClaw ;
- inférence locale ;
- tool-calling et réparation après erreur ;
- aucun cloud nominal.

## Qualification matérielle

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le HARD-40M conserve **30 cas**, un plafond global de 40 minutes et les seuils existants. Le redimensionnement de la flotte ne baisse aucun seuil.

Le mode diagnostic reste :

```powershell
.\menu.ps1 -Action qualification -Quick
```

Les trois modèles sont obligatoires. Un échec de l'un d'eux fait échouer la flotte.

Voir [Qualification](docs/QUALIFICATION.md) et [Benchmark](docs/BENCHMARK.md).

## Backends locaux

Le modèle et le backend sont indépendants :

- `ollama-vulkan` — chemin nominal pré-qualification ;
- `llama-cpp-sycl` — candidat Intel SYCL/Level Zero ;
- `llama-cpp-vulkan` — candidat Vulkan ;
- `b580-hybrid` — profil candidat Qwen/Ollama + Gemma/Qwen Coder llama.cpp/Vulkan.

Aucun backend n'est déclaré vainqueur avant mesures réelles B580.

Parcours Intel :

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
.\menu.ps1 -Action intel-sycl-compare -Quick
```

Voir [Backends](docs/RUNTIME_BACKENDS.md).

## Golden Projects pré-V1

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

Les cinq scénarios couvrent :

1. brief DevOps PDF vague ;
2. PDF + DOCX + image ;
3. exigences contradictoires ;
4. pipeline cassé + remediation ;
5. document avec prompt injection.

Ils ne remplacent pas le projet représentatif final ni la revue humaine.

## Principes de sécurité et de qualité

- **local-first** ;
- **fail-closed** ;
- **Intake immuable** ;
- **ZIP/Office bornés et sûrs** ;
- **Workspace Guard** appliqué par le code ;
- **REQ -> tâche -> sortie -> preuve -> verdict** ;
- **aucun fallback cloud silencieux** ;
- **séparation producteur/auditeur** ;
- **télémétrie locale privacy-safe** ;
- **publication gouvernée** ;
- **approbation humaine finale** ;
- **aucune performance matérielle inventée par CI**.

## Machine d'états projet

```text
INTAKE_READY
  -> ANALYZED
  -> CLARIFICATION_REQUIRED si nécessaire
  -> PLANNED
  -> ASSIGNED
  -> IN_PROGRESS
  -> VALIDATING
  -> REVIEW
  -> PACKAGING
  -> COMPLETE
```

La transition finale exige une approbation humaine.

## Documentation

- [État du projet](STATUS.md)
- [Modèles locaux](docs/MODELES_LOCAUX.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows 11](docs/INSTALLATION_WINDOWS_11.md)
- [Intégration OpenClaw](docs/OPENCLAW_INTEGRATION.md)
- [Routage hybride](docs/ROUTAGE_HYBRIDE.md)
- [Backends](docs/RUNTIME_BACKENDS.md)
- [Qualification](docs/QUALIFICATION.md)
- [Benchmark](docs/BENCHMARK.md)
- [Opérations](docs/OPERATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## V1.0.0

La version `1.0.0` reste bloquée tant que la workstation réelle n'a pas fourni toutes les preuves requises : HARD-40M, OpenClaw E2E, comparaison backend, Golden Projects, multimodalité, télémétrie, projet représentatif, limites documentées et approbation humaine UTC.

Le manifeste `config/v1/release_readiness.yaml` reste fail-closed. Aucun changement de flotte ne contourne cette exigence.
