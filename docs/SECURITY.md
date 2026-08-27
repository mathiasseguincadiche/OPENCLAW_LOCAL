# Sécurité

## Hypothèse importante

Un modèle local compact ou fortement quantifié n'est pas une barrière de sécurité. L'absence de fournisseur cloud ne supprime pas les risques d'injection de prompt, d'abus d'outil, d'exfiltration ou d'action incorrecte.

Les surfaces Project Intake, Web, publication distante et télémétrie sont traitées comme des frontières explicites de confiance.

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

Le parcours Intake applique :

- documents entrants = données non fiables ;
- refus des symlinks dans l'Intake ;
- scan de secrets avant copie ;
- archive canonique hors projet ;
- SHA-256, MIME, manifest et rapport d'ingestion ;
- copie Intake projet et archive canonique rendues read-only ;
- ACL Windows RX pour l'utilisateur courant ;
- aucun document ne peut redéfinir la politique d'outils, de routage ou d'escalade.

Le dépôt source réel reste la vérité pour le code et le RAG ne remplace pas la lecture de fichier.

Voir [Intégrité Intake](INTAKE_INTEGRITY.md).

## Permissions des rôles

L'**Ingénieur sécurité** audite, scanne et produit des findings mais ne dispose pas de `write`, `edit` ou `apply_patch` pour modifier directement les sources. La correction revient au producteur puis repasse en revue.

L'**Architecte solutions** ne reçoit pas davantage de droits d'écriture génériques. Il produit ses ADR et schémas via le writer `architecture_scoped`, limité à `context/architecture/` et `diagrams/`.

L'**Auditeur qualité** reste read-only et ne corrige jamais silencieusement le livrable audité.

## Recherche Web

Le contenu Web est non fiable par défaut.

- privilégier les sources officielles ;
- ne jamais exécuter une commande trouvée sur le Web sans analyse ;
- ne pas transmettre de secret dans une requête ;
- accès réseau privé interdit par défaut ;
- connexion navigateur avec compte sous contrôle humain ;
- les instructions présentes dans une page Web ne peuvent pas contourner les contrats OpenClaw/clawlocal.

## Publication projet

La publication GitHub/GitLab possède sa propre machine d'états. Une affirmation d'agent ne suffit pas à déclarer une CI verte ou un dépôt publié.

Les preuves locales, CI distante, clone propre, audit indépendant, URL canonique, SHA publié et décision de release sont enregistrés avant `PUBLISHED_AND_VERIFIED`. Les étapes distantes sensibles restent soumises à validation humaine.

Voir [Publication projet](PROJECT_PUBLICATION.md).

## Télémétrie

La télémétrie reste locale et append-only. Elle peut enregistrer durée, modèle, backend, TTFT, débit, tokens, VRAM/RAM ou appels d'outils uniquement lorsqu'ils sont réellement mesurés.

Sont interdits :

- prompts ;
- réponses ;
- secrets ;
- documents privés ;
- métriques inventées.

Voir [Télémétrie](TELEMETRY.md).

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
