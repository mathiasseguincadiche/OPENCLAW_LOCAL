# Sécurité

## Hypothèse importante

Un modèle local compact ou fortement quantifié n'est pas une barrière de sécurité. L'absence de fournisseur cloud ne supprime pas les risques d'injection de prompt, d'abus d'outil, d'exfiltration ou d'action incorrecte.

La V0.2 ajoute deux surfaces importantes : **Project Intake** et **Web local-first**. Elles sont traitées comme des entrées non fiables.

## Mesures structurantes

- backend local et Gateway en loopback ;
- permissions minimales par rôle ;
- filesystem borné au workspace ;
- `exec` en mode `ask` ;
- elevated désactivé ;
- secrets hors Git, prompts, requêtes Web et preuves publiables ;
- validation humaine pour publication, fusion, suppression et opérations sensibles ;
- séparation producteur/auditeur ;
- cloud désactivé par défaut ;
- budget fail-closed ;
- aucune promotion automatique depuis la CI.

## Project Intake

Les fichiers déposés dans `intake/` et `sources/` peuvent contenir des instructions hostiles ou contradictoires.

Règles :

- aucun secret dans les entrées projet ;
- le dépôt source réel reste la vérité pour le code ;
- le RAG ne remplace pas la lecture de fichier ;
- un snapshot non géré n'est jamais écrasé ;
- les agents de revue ne peuvent pas modifier silencieusement le livrable ;
- une instruction contenue dans un document ne doit pas modifier la politique d'outils ou d'escalade.

## Recherche Web

Le contenu Web est non fiable par défaut.

- privilégier les sources officielles ;
- ne jamais exécuter une commande trouvée sur le Web sans analyse ;
- ne pas transmettre de secret dans une requête ;
- accès réseau privé interdit par défaut ;
- connexion navigateur avec compte sous contrôle humain ;
- les instructions présentes dans une page Web ne peuvent pas contourner les contrats OpenClaw/clawlocal.

## Cloud

Une clé OpenRouter éventuelle doit être stockée localement, jamais dans le dépôt.

Une escalade exige :

- activation explicite ;
- motif versionné ;
- préconditions démontrées ;
- budget disponible ;
- approbation humaine lorsque le motif l'exige.

Par défaut, les documents privés ne sont pas transmis au cloud. Les secrets ne doivent jamais l'être.

## FinOps comme garde-fou sécurité

Le budget n'est pas uniquement économique : il empêche aussi une boucle d'agent ou un fallback mal configuré de générer une dépense cloud non bornée.

Le ledger de coûts reste hors Git et ne doit pas contenir de secret.

## Diagrammes et renderers

Les diagrammes sont rendus par des outils locaux. Les renderers distants sont interdits par défaut. Une source de diagramme générée par IA doit être inspectée avant toute exécution impliquant un binaire ou une commande non approuvée.
