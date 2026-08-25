# Qualification de la workstation

## But

Cette procédure transforme les modèles déclarés `candidate` en décisions fondées sur des preuves. Elle cible la workstation Windows 11 de référence avec Intel Arc B580 12 Go, Ryzen 7 7700 et 48 Go de RAM, sans supposer à l'avance qu'un modèle ou un contexte est performant.

## Invariants

- aucun appel cloud pendant la qualification matérielle ;
- aucun téléchargement implicite pendant le benchmark ;
- aucune promotion automatique ;
- résultats bruts conservés hors Git ;
- Qwen et Gemma doivent être évalués séparément ;
- SERA reste optionnel tant qu'il n'est pas importé et validé.

## Préparation

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action configure-local
.\menu.ps1 -Action models
.\menu.ps1 -Action verify
```

Le téléchargement des modèles est volontairement séparé de la qualification pour éviter une mutation réseau inattendue au milieu d'un protocole de mesure.

## Qualification automatique

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

`READY_FOR_MANUAL_QUALIFICATION` signifie uniquement que les garde-fous automatiques sont passés. Le modèle reste `candidate` tant que les contrôles OpenClaw réels et la revue humaine ne sont pas terminés.

## Qualification OpenClaw

Avant promotion, exécuter sur le runtime OpenClaw réellement installé au moins :

- une tâche qui impose l'utilisation d'un outil autorisé ;
- une tâche où l'outil retourne une erreur contrôlée et où l'agent doit corriger son plan ;
- trois répétitions pour vérifier la stabilité ;
- une revue des traces confirmant que le provider utilisé est local.

Le dépôt ne fournit pas de faux test d'outil basé uniquement sur du JSON : une intention d'outil textuelle n'est pas une preuve de tool-calling.

## Promotion

La promotion doit être une Pull Request distincte qui :

1. joint une synthèse des preuves sans secret ;
2. modifie explicitement le statut du modèle et, si nécessaire, les contextes recommandés ;
3. explique les limites observées ;
4. conserve une route locale de repli ;
5. ne réactive pas le cloud par défaut.

La version `1.0.0` ne doit être envisagée qu'après qualification réelle du parcours local nominal.
