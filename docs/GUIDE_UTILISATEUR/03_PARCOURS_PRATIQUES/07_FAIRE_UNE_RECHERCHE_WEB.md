# Faire une recherche Web

## Quand utiliser cette procédure ?

Utilisez ce parcours lorsqu'une réponse dépend d'informations externes susceptibles d'avoir changé : version logicielle, release, compatibilité, vulnérabilité, règle, documentation courante, état d'un service, produit ou donnée récente.

## Agent

`expert-recherche`.

## Ce qu'il faut préparer

- la question exacte ;
- la date ou période utile ;
- ce qui doit être considéré comme « actuel » ;
- les sources officielles déjà connues, si vous en avez ;
- les éléments à comparer ;
- le niveau de confiance attendu ;
- si le sujet est technique, ce qui peut être vérifié directement sur la machine ou le runtime.

## Parcours

```text
question
  ↓
identifier les faits volatils
  ↓
rechercher la source d'autorité
  ↓
enregistrer published_at / updated_at / retrieved_at
  ↓
démontrer que le fait est encore actuel
  ↓
corroborer avec une autre source si nécessaire
  ↓
vérifier le runtime si le fait est testable
  ↓
traiter les contradictions
  ↓
attribuer un niveau de confiance
  ↓
synthèse locale
```

## Règle importante : récent ≠ actuel

Une page publiée ce mois-ci n'est pas automatiquement exacte. Une documentation officielle plus ancienne peut, elle, rester la documentation canonique actuellement applicable.

La vérification porte donc sur deux questions différentes :

1. **Quand la source a-t-elle été publiée ou mise à jour ?**
2. **Qu'est-ce qui prouve aujourd'hui que le fait est encore valable ?**

Pour un fait actuel, OPENCLAW_LOCAL doit disposer d'une source autoritative de currentness récupérée récemment : release officielle, documentation courante, registre, advisory, API officielle ou état runtime vivant.

## Sources à privilégier

Ordre de confiance :

1. source de vérité canonique ;
2. source primaire/officielle ;
3. source secondaire fiable ;
4. source communautaire.

Les forums, blogs et discussions peuvent fournir des pistes de diagnostic, mais ne doivent pas remplacer une source officielle disponible pour établir une version, une compatibilité ou une règle actuelle.

## Corroboration

Pour une affirmation importante, le système vise plusieurs sources réellement indépendantes. Deux pages qui recopient le même communiqué ne constituent pas deux confirmations indépendantes.

Une source de vérité canonique peut parfois suffire seule. Exemple : le registre officiel qui définit directement la dernière version publiée.

## Vérification technique

Si la question porte sur ce qu'un logiciel installé **accepte réellement**, demandez une preuve runtime en plus des sources Web :

- CLI ;
- schéma ;
- API ;
- dry-run ;
- test ;
- registre ;
- état runtime.

Exemple :

```text
Documentation : « cette configuration devrait être supportée »
                         +
Runtime : dry-run PASS sur la version réellement installée
                         ↓
              conclusion fortement vérifiée
```

Une documentation Web ne doit pas servir à contredire silencieusement une preuve runtime réelle.

## Dans un projet orchestré

Si une tâche dépend de faits Web actuels, son `required_evidence` doit contenir :

```text
web_evidence
```

Si elle contient aussi une affirmation techniquement vérifiable :

```text
runtime_evidence
```

La tâche produit alors :

```text
evidence/<task-id>/web_evidence.json
```

Le projet refuse de marquer la tâche `PASS` si cette preuve est absente ou invalide.

## Ce que doit contenir la preuve

Pour chaque affirmation importante :

- texte de l'affirmation ;
- caractère `stable`, `volatile` ou `current` ;
- criticité ;
- statut `VERIFIED`, `CONFLICT` ou `UNVERIFIED` ;
- niveau de confiance ;
- sources utilisées ;
- base de currentness ;
- preuve runtime si nécessaire.

Pour chaque source :

- URL ;
- titre ;
- éditeur ;
- niveau d'autorité ;
- date de publication si exposée ;
- date de mise à jour si exposée ;
- date réelle de récupération ;
- capacité ou non à démontrer l'état actuel.

## Si les sources se contredisent

Ne demandez pas à l'IA de « choisir la plus probable » sans preuve.

Le résultat doit rester :

```text
CONFLICT
```

jusqu'à résolution par une meilleure source, une preuve runtime ou une décision explicitement justifiée. Une contradiction ouverte empêche la validation.

## Vérifier manuellement

Pour un fichier de preuve :

```powershell
python .\scripts\46_validate_web_evidence.py `
  --file .\evidence\<task-id>\web_evidence.json `
  --task-id <task-id>
```

Pour tout un projet :

```powershell
python .\scripts\46_validate_web_evidence.py --project <racine-projet>
```

Résultat attendu :

```text
WEB_EVIDENCE=PASS
```

## Ce qui doit provoquer un STOP

- source autoritative manquante pour un fait actuel ;
- vérification trop ancienne ;
- deux « sources » provenant en réalité du même éditeur lorsqu'une indépendance est requise ;
- contradiction ouverte ;
- information non vérifiée ;
- niveau de confiance insuffisant ;
- affirmation technique testable sans preuve runtime ;
- preuve runtime en échec.

Une recherche Web ne signifie pas escalade du modèle vers le cloud. Le raisonnement reste local dans le parcours nominal.
