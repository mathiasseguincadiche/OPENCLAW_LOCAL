# Qualification de la workstation

## But

Cette procédure transforme les modèles/backends déclarés `candidate` en décisions fondées sur des preuves. Elle cible la workstation Windows 11 de référence avec Intel Arc B580 12 Go, Ryzen 7 7700 et 48 Go de RAM, sans supposer à l'avance qu'un modèle, un contexte ou un backend est performant.

## Invariants

- aucun appel cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- aucune promotion automatique ;
- résultats bruts conservés hors Git ;
- modèles requis évalués séparément ;
- LOCAL_DEEP et spécialistes optionnels tant qu'ils ne sont pas importés/validés ;
- toute dérive OpenClaw, backend ou pilote GPU invalide la réutilisation automatique d'une ancienne preuve.

## Préparation reproductible

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full

.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le téléchargement des modèles requis a lieu avant le protocole afin d'éviter une mutation réseau inattendue pendant les mesures.

## Gate OpenClaw E2E réel

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Cette étape vérifie :

1. les huit agents via le Gateway ;
2. le provider local sur le parcours nominal ;
3. un vrai appel d'outil ;
4. une erreur d'outil contrôlée puis réparation ;
5. trois exécutions stables ;
6. aucune dépendance cloud nominale.

La preuve E2E reste sous `<OPENCLAW_LOCAL_ROOT>\proofs\`.

## Qualification automatique

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le parcours V0.2 enchaîne :

1. audit Windows/runtime ;
2. lecture des modèles `required` depuis `model_catalog.yaml` ;
3. smoke test de ces modèles ;
4. collecte d'inventaire ;
5. suite déclarée par `qualification_policy.yaml` — actuellement `devops-v2` ;
6. contextes 8K et 16K ;
7. évaluation des seuils versionnés.

Les preuves sont écrites dans `benchmarks/results/`.

## LOCAL_DEEP

Le candidat `qwen-deep` peut être ajouté explicitement :

```powershell
.\scripts\windows\07_run_qualification.ps1 -IncludeDeep
```

Cette option n'implique aucune promotion. Elle sert uniquement à mesurer si le gain qualitatif justifie l'offload, la RAM et la latence supplémentaires.

## Spécialiste DevOps

SERA reste optionnel tant que son provider réel n'a pas été importé et qualifié. Le runner doit échouer explicitement plutôt que simuler sa disponibilité.

## Comparaison des backends Intel Arc

`runtime_backends.yaml` déclare :

- `ollama-vulkan` ;
- `llama-cpp-sycl` ;
- `llama-cpp-vulkan`.

La promotion d'un backend Intel Arc exige une comparaison B580 réelle, idéalement avec le même modèle/quantification, sur :

- TTFT ;
- tokens/s ;
- VRAM ;
- RAM ;
- stabilité ;
- tool-calling.

Le backend nominal V0.2 n'est pas automatiquement le vainqueur final.

## Interprétation

`NOT_READY` signifie qu'au moins un garde-fou automatique échoue. Il faut analyser la preuve avant de modifier un seuil, un contexte ou un modèle.

`READY_FOR_MANUAL_QUALIFICATION` signifie uniquement que les garde-fous automatiques sont passés. Le modèle reste `candidate` tant que l'E2E OpenClaw, la stabilité, les scénarios projet/Web et la revue humaine ne sont pas terminés.

## Pourquoi la CI ne remplace pas la B580

GitHub Actions valide le code, les contrats, Python 3.12/3.13, PowerShell, la sécurité et le rendu de configuration. Il ne possède pas l'Intel Arc B580 de référence, son pilote, sa VRAM ni les runtimes locaux réellement chargés.

La CI peut donc déclarer la **V0.2 logicielle conforme**, mais jamais inventer une qualification matérielle.

## Promotion

La promotion d'un modèle/backend doit faire l'objet d'une Pull Request distincte qui :

1. joint une synthèse redacted des preuves ;
2. modifie explicitement le statut du modèle/backend ;
3. documente les versions exactes runtime/pilote ;
4. explique les limites observées ;
5. conserve une route locale de repli ;
6. ne réactive pas le cloud par défaut.

La version `1.0.0` ne doit être envisagée qu'après qualification réelle du parcours local nominal sur la workstation cible.
