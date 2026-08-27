# Changelog

Toutes les modifications notables sont documentées ici. Le format s'inspire de Keep a Changelog et le versionnage suit SemVer.

## [Unreleased]

### Added

- protocole de qualification matérielle sans cloud ;
- inventaire Windows de preuves ;
- suite DevOps `devops-v1` ;
- benchmark Ollama streaming avec TTFT et débit ;
- gate automatique configurable et promotion manuelle uniquement ;
- orchestrateur PowerShell de qualification ;
- analyse CodeQL, Dependency Review, PSScriptAnalyzer et Pester ;
- validation SemVer et workflow GitHub Release ;
- bootstrap Windows reproductible avec lock Python/Node/OpenClaw/Ollama ;
- validation SHA-256 du runtime Node.js et SHA-512/SRI du package OpenClaw ;
- installation complète runtime + modèles + OpenClaw + Gateway ;
- renderer déterministe de la flotte OpenClaw ;
- matérialisation des huit workspaces agents ;
- politique d'outils par rôle, filesystem workspace-only, exec avec approbation et elevated désactivé ;
- pont de routage `clawlocal` vers les références modèles OpenClaw ;
- commande de routage local/cloud explicite sans fallback silencieux ;
- gate E2E OpenClaw réel : huit agents, tool-calling, réparation après erreur et stabilité sur trois runs ;
- couverture Python avec seuil, mypy et matrice Python 3.12/3.13 ;
- SBOM CycloneDX de release ;
- attestations GitHub de provenance et SBOM ;
- documentation d'intégration OpenClaw et troubleshooting approfondi ;
- documentation de gouvernance GitHub et politique de protection de `main` ;
- badges CI, CodeQL, version, licence, PowerShell et Python dans le README.

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
