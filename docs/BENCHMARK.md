# Benchmark local

## Objectif

Mesurer avant de choisir. La qualification V0.2 distingue :

1. **fonctionnelle** : requêtes réussies et réponses conformes à des contrôles versionnés ;
2. **performance** : TTFT, débit de génération et latence murale ;
3. **contexte** : 8K puis 16K, 32K restant optionnel ;
4. **projet/DevOps** : tâches plus proches des usages réels ;
5. **agentique** : discipline outil et réparation, complétées par un vrai E2E OpenClaw ;
6. **backend** : comparaison Ollama/Vulkan et candidats llama.cpp sur Intel Arc.

Le benchmark ne cherche pas à prouver qu'un modèle local est systématiquement équivalent à un modèle frontier cloud.

## Suite active : devops-v2

La suite n'est plus codée en dur dans le runner. `scripts/benchmark_local.py` lit `config/v1/qualification_policy.yaml`, puis charge la suite déclarée par `suite`.

Pour la V0.2 :

```text
qualification_policy.yaml
    suite: devops-v2
          ↓
benchmarks/suites/devops_v2.yaml
```

La suite couvre notamment :

- analyse de Project Intake ;
- génération GitLab CI YAML ;
- diagnostic Kubernetes sans cause inventée ;
- modification Terraform multi-fichiers ;
- idempotence Ansible ;
- revue sécurité de pipeline ;
- runbook avec rollback ;
- source D2 de diagramme ;
- discipline face à une donnée récente sans source ;
- intention d'outil JSON ;
- réparation après retour d'outil ;
- discipline sur contexte synthétique long.

## Contrôles exécutables

Le runner comprend les contrôles déclarés dans la suite :

- `nonempty` ;
- `contains_all` ;
- `contains_any` ;
- `not_contains_any` ;
- `json_keys` ;
- `yaml_keys`.

`scripts/22_validate_configs.py` refuse une suite utilisant un type de contrôle que le runner ne sait pas exécuter.

## Exécution

Qualification complète :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

8K uniquement :

```powershell
.\scripts\windows\07_run_qualification.ps1 -Quick
```

Inclure le candidat LOCAL_DEEP Ollama :

```powershell
.\scripts\windows\07_run_qualification.ps1 -IncludeDeep
```

Inclure un spécialiste uniquement après préparation explicite de son provider :

```powershell
.\scripts\windows\07_run_qualification.ps1 -IncludeSpecialist
```

## Source de vérité des modèles

Les scripts PowerShell ne maintiennent plus leur propre liste de modèles. Ils utilisent `scripts/20_list_models.py`, qui lit `model_catalog.yaml`.

Cela évite qu'une qualification teste un modèle différent de celui décrit par la documentation ou le routage.

## Mesures

Le runner Ollama enregistre notamment :

- `ttft_ms` ;
- `wall_ms` ;
- `eval_count` / `eval_duration_ns` ;
- `tokens_per_second` ;
- contexte demandé ;
- résultat de chaque contrôle ;
- sortie brute dans les preuves locales hors Git.

La comparaison de backends doit compléter ces mesures avec VRAM, RAM, stabilité et tool-calling lorsque le protocole B580 est exécuté.

## Gate automatique

Les seuils versionnés sont dans `config/v1/qualification_policy.yaml` :

- aucune erreur API tolérée ;
- taux minimal de contrôles conformes ;
- débit médian minimal ;
- plafond p95 du TTFT ;
- seuils par contexte requis.

Un succès donne au mieux `READY_FOR_MANUAL_QUALIFICATION`. Aucun script ne modifie automatiquement le statut des modèles.

## Gate manuel avant promotion

Une promotion exige encore :

1. tool-calling réel via OpenClaw ;
2. correction après retour d'outil réel ;
3. Project Intake E2E ;
4. recherche Web locale E2E ;
5. trois exécutions stables ;
6. revue humaine ;
7. absence de dépendance cloud sur le parcours nominal ;
8. pour Intel Arc, comparaison des backends prévue par le contrat.

## Preuves

Les résultats bruts vont dans `benchmarks/results/` et restent exclus de Git. Une synthèse publiée doit indiquer : modèle, tag/quantification, backend, versions, contexte, pilote GPU, protocole, date et limites observées.
