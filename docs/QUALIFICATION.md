# Qualification de la workstation

## But

Cette procédure transforme les modèles déclarés `candidate` en décisions fondées sur des preuves. Elle cible la workstation Windows 11 de référence avec Intel Arc B580 12 Go, Ryzen 7 7700 et 48 Go de RAM, sans supposer à l'avance qu'un modèle, un contexte ou une version runtime est performant.

## Invariants

- aucun appel cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- aucune promotion automatique ;
- résultats bruts conservés hors Git ;
- Qwen et Gemma évalués séparément ;
- SERA optionnel tant qu'il n'est pas importé et validé ;
- toute dérive OpenClaw/Ollama/pilote GPU invalide la réutilisation automatique d'une ancienne preuve.

## Préparation reproductible

Pour une machine neuve ou après évolution majeure :

```powershell
.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full
```

Puis :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Le téléchargement des modèles reste effectué avant le protocole de benchmark afin d'éviter une mutation réseau inattendue au milieu des mesures.

## Gate OpenClaw E2E réel

Avant de considérer la qualification matérielle comme promotable :

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Cette étape vérifie réellement :

1. les huit agents via le Gateway ;
2. `provider=ollama` sur le parcours nominal ;
3. un vrai appel d'outil ;
4. une erreur d'outil contrôlée puis une réparation ;
5. trois exécutions stables ;
6. aucune dépendance cloud nominale.

La preuve E2E est stockée sous `<OPENCLAW_LOCAL_ROOT>\proofs\` et n'est pas commitée.

## Qualification automatique des modèles

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Le parcours enchaîne :

1. audit Windows/Ollama ;
2. smoke test des deux modèles requis ;
3. collecte d'inventaire ;
4. suite `devops-v1` en 8K et 16K ;
5. évaluation des seuils versionnés.

Les preuves sont écrites dans `benchmarks/results/`.

## Interprétation

`NOT_READY` signifie qu'au moins un garde-fou automatique échoue. Il faut analyser la preuve avant de modifier un seuil, un contexte ou un modèle.

`READY_FOR_MANUAL_QUALIFICATION` signifie uniquement que les garde-fous automatiques sont passés. Le modèle reste `candidate` tant que le gate OpenClaw réel, la stabilité et la revue humaine ne sont pas terminés.

## Pourquoi la CI ne remplace pas la B580

GitHub Actions valide le code, les contrats, Python 3.12/3.13, PowerShell, la sécurité et le renderer. Il ne possède pas l'Intel Arc B580 de référence, les pilotes de la workstation ni l'état Ollama local. Les métriques matérielles et le tool-calling avec le modèle réellement chargé doivent donc provenir de la machine cible.

## Promotion

La promotion doit être une Pull Request distincte qui :

1. joint une synthèse redacted des preuves E2E + benchmark + inventaire ;
2. modifie explicitement le statut du modèle et, si nécessaire, les contextes recommandés ;
3. documente les versions exactes du runtime et du pilote ;
4. explique les limites observées ;
5. conserve une route locale de repli ;
6. ne réactive pas le cloud par défaut.

La version `1.0.0` ne doit être envisagée qu'après qualification réelle du parcours local nominal sur la workstation cible.
