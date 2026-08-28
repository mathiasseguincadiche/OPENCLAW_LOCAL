# Recherche Web Local-First

## Principe

Une information récente ne justifie pas à elle seule l'utilisation d'un modèle cloud.

Le parcours nominal de la V0.2 est :

```text
agent local
   ↓
web_search / web_fetch
   ↓
sources Internet récentes
   ↓
raisonnement et synthèse par le modèle local
```

Le contrat est défini dans `config/v1/web_policy.yaml`.

## Outils

Le patch OpenClaw active :

- `web_search` ;
- `web_fetch` ;
- `browser` uniquement pour `expert-recherche` par défaut, pour les sites nécessitant une navigation plus complexe.

La recherche nominale utilise `parallel-free`. Ce provider ne demande pas de clé API, mais OpenClaw l'expose via son plugin officiel `@openclaw/parallel-plugin`. OPENCLAW_LOCAL verrouille la version du plugin dans `config/v1/runtime_versions.json`, vérifie sa présence, l'installe si nécessaire, l'active et effectue un `plugins inspect --runtime` avant de valider le patch OpenClaw.

Cette dépendance n'est pas une escalade vers un LLM cloud : les sources viennent du Web, tandis que le raisonnement et la synthèse restent assurés par les modèles locaux. Le provider de recherche reste une dépendance interchangeable du contrat Web, pas une dépendance du routage LLM.

## Fraîcheur des informations

Pour une donnée susceptible d'avoir changé — version logicielle, documentation courante, compatibilité, vulnérabilité, release, règle ou état externe — l'agent doit rechercher une source récente avant de conclure.

La politique privilégie :

1. sources primaires ou officielles ;
2. au moins deux sources lorsque cela améliore la confiance ;
3. séparation entre fait observé et interprétation du modèle.

Le modèle local ne doit jamais inventer une version « actuelle » faute d'accès Web.

## Escalade cloud

Le cloud de recherche reste exceptionnel. Les motifs V0.2 autorisés sont notamment :

- `deep_web_research` : recherche approfondie après tentative Web locale ;
- `source_conflict` : sources locales/Web réellement contradictoires.

Exemple de plan d'escalade :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent expert-recherche `
  --message 'Analyse les sources contradictoires.' `
  --cloud `
  --reason source_conflict `
  --source-conflict-observed `
  --project-id p5-devops
```

Pour `deep_web_research`, `--local-web-attempted` est obligatoire.

## Ce qui est interdit

La politique refuse notamment :

- `web_freshness_only` ;
- la commodité ;
- le fait qu'un modèle local soit simplement plus lent ;
- le fallback cloud silencieux ;
- une escalade sans budget validé ;
- l'envoi de secrets ou de documents privés par défaut.

## Sécurité réseau

- le runtime local reste en loopback ;
- les requêtes ne doivent pas contenir de secrets ;
- les accès réseau privés sont interdits par défaut ;
- une connexion navigateur nécessitant un compte doit rester sous contrôle humain ;
- les résultats Web sont considérés comme des entrées non fiables vis-à-vis des injections de prompt.

## Résultat attendu

Le système doit pouvoir répondre à une question récente avec des sources actuelles **sans payer un LLM cloud**, puis réserver OpenRouter à une véritable escalation de capacité ou de qualité.
