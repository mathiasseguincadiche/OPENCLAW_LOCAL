# Contribution

## Principes

1. créer une branche dédiée depuis `main` ;
2. ne jamais committer de secret, modèle, cache, journal ou résultat de benchmark brut ;
3. garder les scripts idempotents et `-DryRun`/`-WhatIf` quand une mutation est possible ;
4. documenter préconditions, mutations, preuves, risques et rollback réel ;
5. conserver `README.md` comme porte d'entrée et le détail dans `docs/` ;
6. ajouter ou adapter un test pour toute correction reproductible ;
7. ne jamais transformer une hypothèse de performance locale en fait sans benchmark ;
8. mettre à jour `CHANGELOG.md` et `VERSION` uniquement lors d'une release ;
9. soumettre une PR avec risques et validation.

## Contrôles locaux

```powershell
python scripts/21_validate_repository.py
python scripts/22_validate_configs.py
ruff check src tests scripts
pytest -q
```

## Modification du routage

Toute PR touchant `model_routing.yaml` ou `escalation_policy.yaml` doit expliquer :

- pourquoi la route locale actuelle est insuffisante ;
- quel coût ou risque introduit la nouvelle route ;
- comment revenir en arrière ;
- quel benchmark ou test justifie la promotion.

Les changements directs sur `main`, le force-push et la réécriture d'historique sont déconseillés sans nécessité documentée.
