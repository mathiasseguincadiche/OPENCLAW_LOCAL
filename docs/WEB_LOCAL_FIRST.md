# Recherche Web Local-First

## Principe

Une information récente ne justifie pas à elle seule l'utilisation d'un modèle cloud.

Le parcours nominal est :

```text
agent local
   ↓
web_search / web_fetch
   ↓
sources Internet
   ↓
qualification fraîcheur / autorité / contradictions
   ↓
preuve runtime si le fait est techniquement testable
   ↓
raisonnement et synthèse par le modèle local
```

Le contrat exécutable est défini dans `config/v1/web_policy.yaml`.

## Outils

Le patch OpenClaw active :

- `web_search` ;
- `web_fetch` ;
- `browser` uniquement pour `expert-recherche` par défaut, pour les sites nécessitant une navigation plus complexe.

La recherche nominale utilise `parallel-free`. Ce provider ne demande pas de clé API, mais OpenClaw l'expose via son plugin officiel `@openclaw/parallel-plugin`. OPENCLAW_LOCAL verrouille la version du plugin dans `config/v1/runtime_versions.json`, vérifie sa présence, l'installe si nécessaire, l'active et effectue un `plugins inspect --runtime` avant de valider le patch OpenClaw.

Cette dépendance n'est pas une escalade vers un LLM cloud : les sources viennent du Web, tandis que le raisonnement et la synthèse restent assurés par les modèles locaux.

## « Récent » n'est pas « actuel »

Le projet distingue trois dates :

- `published_at` : date de publication si la source l'expose ;
- `updated_at` : date de mise à jour si la source l'expose ;
- `retrieved_at` : date à laquelle OPENCLAW_LOCAL a réellement vérifié la source.

Une documentation officielle publiée plusieurs mois auparavant peut toujours être la source canonique actuelle. Inversement, un billet publié hier n'est pas une preuve suffisante qu'une version, une compatibilité ou une configuration est correcte aujourd'hui.

Pour un fait `current` ou `volatile`, le système exige une **preuve de currentness** depuis une source autoritative récupérée récemment : release officielle, documentation courante, registre officiel, advisory, API officielle, état runtime vivant ou autre source d'état faisant autorité.

Le simple fait qu'une page date du mois ou de l'année en cours ne constitue donc pas une preuve de validité actuelle.

## Hiérarchie d'autorité

Le contrat classe les sources ainsi :

1. `source_of_truth` : source canonique qui définit directement le fait ;
2. `primary` : source officielle ou primaire pertinente ;
3. `secondary` : analyse ou documentation secondaire fiable ;
4. `community` : forum, discussion, blog ou retour communautaire.

Une source secondaire ou communautaire peut être très utile au diagnostic, mais ne remplace pas une source d'autorité disponible pour établir un fait actuel.

## Corroboration

La cible par défaut est de deux sources avec des éditeurs distincts. Une source `source_of_truth` peut se suffire à elle-même lorsque le contrat l'autorise, car multiplier des copies d'une même information n'apporte pas d'indépendance réelle.

Les affirmations `high` et `critical` doivent atteindre un niveau de confiance `HIGH`. Les niveaux `low` et `standard` doivent atteindre au minimum `MEDIUM`.

Une contradiction ouverte est bloquante. Le modèle ne doit jamais choisir silencieusement la source qui l'arrange.

## Preuve runtime

Lorsqu'une affirmation technique peut être testée sur l'environnement réel, la documentation seule n'est pas suffisante.

Exemples de preuves runtime :

- sortie CLI ;
- JSON Schema retourné par le logiciel installé ;
- réponse d'API ;
- dry-run ;
- test automatisé ;
- registre/package registry ;
- vérification du runtime vivant.

Exemple : pour affirmer qu'une configuration est supportée par la version d'OpenClaw installée, une validation par `config schema`, `config patch --dry-run`, `plugins inspect --runtime` ou test équivalent a plus d'autorité qu'un article secondaire.

Une affirmation marquée `machine_verifiable=true` doit référencer une preuve runtime `PASS` récente.

## Artefact `web_evidence.json`

Une tâche du Project Orchestrator qui dépend d'informations Web actuelles ajoute `web_evidence` à `required_evidence`. Si une preuve runtime est également obligatoire, elle ajoute `runtime_evidence`.

La tâche doit alors produire :

```text
evidence/<task-id>/web_evidence.json
```

Ce fichier contient au minimum :

- les affirmations vérifiées ;
- leur volatilité et criticité ;
- leur statut et niveau de confiance ;
- les sources référencées ;
- `published_at`, `updated_at` et `retrieved_at` selon disponibilité ;
- le niveau d'autorité de chaque source ;
- la base utilisée pour démontrer la currentness ;
- les preuves runtime éventuelles ;
- les contradictions et leur statut.

Le validateur autonome est :

```powershell
python .\scripts\46_validate_web_evidence.py `
  --file .\evidence\<task-id>\web_evidence.json `
  --task-id <task-id>
```

Pour un projet complet :

```powershell
python .\scripts\46_validate_web_evidence.py --project <racine-projet>
```

## Gates du Project Orchestrator

La vérification est fail-closed.

Une tâche exigeant `web_evidence` ne peut pas être enregistrée comme `PASS` si la preuve est absente ou invalide. Le projet revalide ensuite toutes les preuves Web avant :

```text
VALIDATING
REVIEW
PACKAGING
COMPLETE
```

Sont notamment bloquants :

- source de currentness trop ancienne ;
- absence de source autoritative pour un fait actuel ;
- corroboration insuffisante ;
- éditeurs non indépendants lorsque l'indépendance est requise ;
- contradiction ouverte ;
- affirmation non vérifiée ;
- confiance insuffisante ;
- preuve runtime obligatoire absente, trop ancienne ou en échec.

L'Auditeur Qualité doit également signaler comme bloquante une omission de classification : si un livrable utilise un fait externe actuel mais que la tâche n'a pas demandé `web_evidence`, l'absence de marqueur ne permet pas de contourner le contrôle.

## Escalade cloud

Le cloud de recherche reste exceptionnel. Les motifs autorisés sont notamment :

- `deep_web_research` : recherche approfondie après tentative Web locale ;
- `source_conflict` : sources locales/Web réellement contradictoires.

Une contradiction n'autorise jamais un fallback cloud silencieux. Elle doit d'abord être explicitement observée et documentée.

## Sécurité réseau

- le runtime local reste en loopback ;
- les requêtes ne doivent pas contenir de secrets ;
- les accès réseau privés sont interdits par défaut ;
- une connexion navigateur nécessitant un compte doit rester sous contrôle humain ;
- les résultats Web sont des entrées non fiables vis-à-vis des injections de prompt.

## Résultat attendu

OPENCLAW_LOCAL ne doit pas seulement « trouver une page ». Il doit pouvoir démontrer pourquoi une information externe importante est considérée **actuelle, pertinente et suffisamment fiable**, puis refuser de valider lorsqu'il manque une preuve.
