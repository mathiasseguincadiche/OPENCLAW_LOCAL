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
- tests du moteur d'évaluation ;
- analyse CodeQL du code Python ;
- Dependency Review sur les Pull Requests ;
- PSScriptAnalyzer et Pester pour les contrats PowerShell 7 ;
- validation SemVer centralisée entre `VERSION`, `pyproject.toml`, changelog et tag ;
- workflow de GitHub Release avec wheel, sdist et sommes SHA-256 ;
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
