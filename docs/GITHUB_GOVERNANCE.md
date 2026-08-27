# Gouvernance GitHub

Ce document fixe les réglages GitHub attendus pour `mathiasseguincadiche/OPENCLAW_LOCAL`. Les contrats présents dans le dépôt sont automatisés par CI ; les réglages administratifs GitHub doivent rester cohérents avec cette politique.

## Métadonnées du dépôt

Description recommandée :

> Plateforme IA multi-agents local-first pour Windows 11 : OpenClaw + Ollama, routage hybride, qualification matérielle et escalade cloud contrôlée.

Topics recommandés :

- `openclaw`
- `ollama`
- `local-ai`
- `multi-agent`
- `windows-11`
- `powershell`
- `python`
- `devops`
- `llm`
- `openrouter`

## Protection de `main`

Le dépôt est maintenu par un propriétaire unique. La protection doit donc imposer le passage par Pull Request et les contrôles automatiques sans exiger l'approbation d'un second mainteneur qui n'existe pas.

Cible recommandée pour un ruleset GitHub appliqué à `main` :

- empêcher la suppression de la branche ;
- empêcher les force-push ;
- imposer une Pull Request avant fusion ;
- ne pas imposer d'approbation humaine tant que le dépôt reste mono-mainteneur ;
- imposer la résolution des conversations avant fusion ;
- imposer une branche à jour avant fusion lorsque GitHub peut l'évaluer ;
- imposer les checks `quality`, `windows-contract`, `Dependency Review` et `CodeQL / Python` après leur première exécution réussie ;
- conserver une histoire linéaire et privilégier le squash merge ;
- ne pas autoriser de bypass permanent du propriétaire sur le parcours normal.

Les règles qui exigent un deuxième approbateur ne doivent être activées qu'après ajout d'un mainteneur distinct.

## Pull Requests

Chaque changement significatif doit suivre :

```text
branche dédiée
    -> Pull Request
    -> CI Python
    -> PowerShell 7 / PSScriptAnalyzer / Pester
    -> Dependency Review
    -> CodeQL Python
    -> squash merge vers main
```

Les résultats matériels B580 ne sont jamais simulés dans GitHub Actions. Ils restent qualifiés sur la workstation réelle puis synthétisés dans une PR séparée.

## Sécurité

- aucun secret dans Git ;
- aucun modèle `.gguf` ou `.safetensors` dans Git ;
- aucun certificat ou keystore privé (`.key`, `.pem`, `.p12`, `.pfx`, `.jks`) ;
- CodeQL analyse le code Python ; PowerShell est contrôlé par PSScriptAnalyzer et Pester ;
- le **GitHub Dependency Graph doit être activé** dans les paramètres du dépôt pour que `actions/dependency-review-action` compare précisément les dépendances ajoutées par une Pull Request ;
- lorsque le Dependency Graph est disponible, Dependency Review bloque les nouvelles dépendances présentant une vulnérabilité de sévérité `moderate` ou supérieure ;
- tant que le Dependency Graph n'est pas activé, le workflow reste fail-closed sur les dépendances Python installées grâce à un fallback `pip-audit`, et signale explicitement que le contrôle différentiel GitHub n'est pas disponible ;
- Dependabot suit `pip` et GitHub Actions.

## Releases

La source de vérité de version est `VERSION`, qui doit correspondre à `project.version` dans `pyproject.toml` et à une section du `CHANGELOG.md`.

Une release est déclenchée par un tag strictement égal à :

```text
v<VERSION>
```

Exemple :

```text
VERSION = 0.1.0
Tag     = v0.1.0
```

Le workflow `Release` revalide le dépôt, le SemVer, les tests Python, PSScriptAnalyzer et Pester avant de publier une GitHub Release contenant le wheel, le sdist et leurs sommes SHA-256.

## Version 1.0.0

`1.0.0` reste interdite tant que le parcours local nominal n'a pas été qualifié sur la workstation cible avec les preuves prévues dans `docs/QUALIFICATION.md`.
