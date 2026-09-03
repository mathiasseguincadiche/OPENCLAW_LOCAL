# Télémétrie locale

## Objectif

La télémétrie de `OPENCLAW_LOCAL` sert à observer le comportement réel de la plateforme sans transformer les prompts, réponses ou documents privés en données de monitoring.

## Flotte suivie

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

`devstral-devops` est l'alias de compatibilité du spécialiste Qwen 2.5 Coder 14B.

Toute métrique portant sur l'ancienne flotte 24–27B reste historique. Elle ne doit pas être agrégée comme si elle mesurait la flotte actuelle.

## Données autorisées

Selon disponibilité réelle du runtime :

- timestamp ;
- projet et phase ;
- agent ;
- alias et runtime modèle ;
- backend/provider ;
- contexte demandé ;
- durée murale ;
- TTFT ;
- tokens d'entrée/sortie ;
- tokens/s ;
- VRAM/RAM observées ;
- durée de chargement ;
- tool calls ;
- retries ;
- transitions projet ;
- statut PASS/FAIL ;
- éventuelle escalade cloud avec motif et coût, sans contenu privé.

Une donnée non disponible reste `null`/absente. Elle n'est jamais estimée puis présentée comme observée.

## Données interdites

La télémétrie ne doit pas stocker :

- prompts complets ;
- réponses complètes ;
- documents utilisateur ;
- secrets ;
- clés API ;
- tokens Gateway ;
- contenu du canal thinking ;
- fichiers privés du projet.

Le volume de thinking peut être compté lorsqu'il est exposé, mais son contenu brut n'est pas conservé.

## Contexte et migration

Le contexte nominal de la nouvelle flotte est 8192 tokens. Les mesures 16K appartiennent au protocole de qualification/stress et doivent être identifiées comme telles.

Après changement de modèle, digest, quantification, backend, pilote ou runtime, les séries doivent rester distinguables. Une ancienne performance ne peut pas être réattribuée au nouveau fingerprint.

## Stockage

Les preuves/télémétries opérationnelles restent locales, sous la racine gérée et hors Git selon les politiques du projet.

L'objectif est de pouvoir relier une mesure à :

```text
commit
+ agent
+ alias
+ runtime_id
+ digest/quantification si disponible
+ backend
+ pilote
+ contexte
+ scénario
```

## Utilisation pour la qualification

Les données de télémétrie peuvent soutenir la décision V1 uniquement lorsqu'elles correspondent à la flotte, au commit et au matériel réellement qualifiés. Elles complètent les preuves HARD-40M, E2E, backend, multimodalité, golden projects et projet représentatif ; elles ne les remplacent pas.
