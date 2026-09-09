# Politique de sécurité

## Signaler une vulnérabilité

Ne publiez pas de secret, jeton, clé API, chemin privé ou donnée personnelle dans une issue publique. Utilisez les mécanismes privés de signalement GitHub lorsqu'ils sont disponibles.

## Modèle de menace

Le projet traite comme sensibles :

- configuration runtime réelle ;
- prompts, journaux et preuves contenant des données de projet ;
- endpoints locaux exposés au-delà du loopback ;
- modèles ou templates capables d'exécuter des outils ;
- requêtes et résultats Web susceptibles de contenir des données non fiables ou sensibles.

Architecture V2 ne supporte **aucun fournisseur d'inférence LLM cloud**. Aucune clé OpenRouter ou autre clé de fournisseur LLM n'est requise par le parcours nominal et aucun fallback LLM en ligne n'est autorisé. Les outils Web restent des sources d'information distantes distinctes du runtime LLM local.

## Garde-fous

- Ollama reste sur `127.0.0.1` par défaut ;
- aucune clé réelle dans Git ;
- aucun modèle LLM cloud ni fallback LLM en ligne ;
- les résultats Web sont traités comme des entrées non fiables et les requêtes ne doivent jamais exposer de secrets ;
- les petits modèles locaux ne sont pas considérés comme une barrière de sécurité ;
- les opérations sensibles gardent une approbation humaine ;
- les modèles/quantifications sont qualifiés avant promotion ;
- CodeQL analyse le code Python sur `main`, les Pull Requests et de façon planifiée ;
- Dependency Review contrôle les nouvelles dépendances introduites par une Pull Request ;
- PSScriptAnalyzer et Pester contrôlent les scripts PowerShell 7 ;
- les certificats/keystores privés (`.key`, `.pem`, `.p12`, `.pfx`, `.jks`) sont interdits dans Git ;
- les releases sont publiées uniquement après validation SemVer, tests Python et contrôles PowerShell.

Voir également [docs/SECURITY.md](docs/SECURITY.md) et [docs/GITHUB_GOVERNANCE.md](docs/GITHUB_GOVERNANCE.md).
