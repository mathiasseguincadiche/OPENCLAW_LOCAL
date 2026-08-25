# Modèles locaux

## Règle de promotion

Un modèle n'est pas promu parce qu'il est populaire. Il doit réussir les tâches représentatives du projet avec une latence et une consommation mémoire acceptables.

## Candidats v0.1

| Modèle | Usage | Statut |
|---|---|---|
| Qwen 3.5 9B | généraliste, orchestration, DevOps courant | candidat principal |
| Gemma 4 12B | rédaction, architecture, seconde opinion | candidat principal |
| SERA 14B | code/DevOps | optionnel, import et qualification requis |

Les identifiants exacts du moteur local restent dans `config/v1/model_catalog.yaml` et doivent être validés contre le catalogue réellement installé.

## Ce que 12 Go de VRAM impliquent

Le dépôt privilégie les modèles compacts quantifiés et des contextes mesurés. Les gros modèles avec offload RAM peuvent être utiles en mode `LOCAL_DEEP`, mais ne doivent pas être supposés interactifs sans benchmark.

## Tool-calling

La qualité du texte ne suffit pas. Pour être route agentique de production, un modèle doit réussir :

- appel d'outil structuré ;
- non-fabrication d'un résultat d'outil ;
- gestion d'erreur ;
- respect du rôle ;
- arrêt correct ;
- résistance raisonnable aux instructions adverses.
