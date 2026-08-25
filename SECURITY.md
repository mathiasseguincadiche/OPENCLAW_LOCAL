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
- les modèles/quantifications sont qualifiés avant promotion.

Voir également [docs/SECURITY.md](docs/SECURITY.md).
