# Politique de sécurité

## Signaler une vulnérabilité

Ne publiez pas de secret, jeton, clé API, chemin privé ou donnée personnelle dans une issue publique. Utilisez les mécanismes privés de signalement GitHub lorsqu'ils sont disponibles.

## Modèle de menace

Le projet traite comme sensibles :

- clés OpenRouter ou autre fournisseur cloud ;
- configuration runtime réelle ;
- prompts, journaux et preuves contenant des données de projet ;
- endpoints locaux exposés au-delà du loopback ;
- modèles ou templates capables d'exécuter des outils.

## Garde-fous

- Ollama reste sur `127.0.0.1` par défaut ;
- aucune clé réelle dans Git ;
- cloud désactivé par défaut ;
- escalade cloud explicite et auditable ;
- les petits modèles locaux ne sont pas considérés comme une barrière de sécurité ;
- les opérations sensibles gardent une approbation humaine ;
- les modèles/quantifications sont qualifiés avant promotion ;
- CodeQL analyse le code Python sur `main`, les Pull Requests et de façon planifiée ;
- Dependency Review contrôle les nouvelles dépendances introduites par une Pull Request ;
- PSScriptAnalyzer et Pester contrôlent les scripts PowerShell 7 ;
- les certificats/keystores privés (`.key`, `.pem`, `.p12`, `.pfx`, `.jks`) sont interdits dans Git ;
- les releases sont publiées uniquement après validation SemVer, tests Python et contrôles PowerShell.

Voir également [docs/SECURITY.md](docs/SECURITY.md) et [docs/GITHUB_GOVERNANCE.md](docs/GITHUB_GOVERNANCE.md).
