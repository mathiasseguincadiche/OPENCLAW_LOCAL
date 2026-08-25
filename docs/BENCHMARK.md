# Benchmark local

## Objectif

Mesurer avant de choisir. La qualification distingue quatre dimensions :

1. **fonctionnelle** : requêtes Ollama réussies et réponses conformes à des contrôles simples ;
2. **performance** : temps au premier token, débit de génération et latence murale ;
3. **contexte** : comportement mesuré à 8K puis 16K, 32K restant optionnel ;
4. **agentique** : validation OpenClaw réelle après le gate automatique.

Le benchmark ne cherche pas à prouver qu'un modèle local est équivalent à un modèle frontier cloud.

## Suite de référence

La source de vérité est `benchmarks/suites/devops_v1.yaml`. Elle couvre :

- synthèse local-first ;
- génération GitLab CI YAML ;
- diagnostic Kubernetes ;
- rédaction de runbook avec rollback ;
- revue sécurité ;
- intention d'outil structurée en JSON ;
- correction après retour d'outil ;
- discipline sur contexte synthétique plus long.

Les deux scénarios JSON évaluent uniquement la **discipline de sortie structurée**. Ils ne remplacent pas un vrai test de tool-calling OpenClaw.

## Exécution

Parcours complet :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Parcours rapide 8K uniquement :

```powershell
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Inclure SERA seulement lorsqu'il a déjà été importé localement :

```powershell
.\scripts\windows\07_run_qualification.ps1 -IncludeSpecialist
```

## Mesures

`scripts/benchmark_local.py` utilise l'API native Ollama `POST /api/generate` en streaming et enregistre notamment :

- `ttft_ms` : temps observé jusqu'au premier fragment de réponse ;
- `wall_ms` : durée murale complète ;
- `eval_count` / `eval_duration_ns` ;
- `tokens_per_second` calculé depuis les compteurs Ollama ;
- contexte demandé ;
- résultat des contrôles automatisés ;
- sortie brute, uniquement dans les preuves locales ignorées par Git.

## Gate automatique

Les seuils versionnés sont dans `config/v1/qualification_policy.yaml`. Ils servent de **garde-fou d'utilisabilité**, pas de classement marketing :

- aucune erreur API tolérée ;
- taux minimal de contrôles conformes ;
- débit médian minimal ;
- plafond p95 du TTFT ;
- contrôle spécifique par contexte requis.

Si le gate passe, le verdict est `READY_FOR_MANUAL_QUALIFICATION`. Cela ne modifie jamais automatiquement `model_catalog.yaml`.

## Gate manuel avant promotion

Une promotion en route locale de production exige encore :

1. tool-calling réel via OpenClaw ;
2. correction après retour d'outil réel ;
3. trois exécutions stables ;
4. revue humaine des sorties représentatives ;
5. confirmation que le parcours nominal n'a utilisé aucun cloud.

## Preuves

Les résultats bruts vont dans `benchmarks/results/` et sont exclus de Git. Une conclusion publiée doit indiquer : modèle, quantification ou tag, moteur, versions, contexte, pilote GPU, protocole et date.

Aucune sortie brute contenant une donnée sensible ne doit être publiée sans rédaction préalable.
