# Lire en premier

## But

Comprendre le minimum nécessaire avant de confier un travail à OPENCLAW_LOCAL.

## Les 5 idées à retenir

1. **Un agent est un rôle**, pas un modèle supplémentaire.
2. **Le projet central** sous `<OPENCLAW_LOCAL_ROOT>\projects\<id>` est la source de vérité.
3. Une question courte peut être traitée directement ; un travail complexe doit passer par le **Project Orchestrator**.
4. Un `STOP` peut être un **gate normal** : clarification, correction ou approbation humaine.
5. Le cloud ne doit jamais masquer une panne locale.

## Routine avant de travailler

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Si le travail est important, vérifier aussi l'état du projet avant toute exécution.

## Ensuite

Lire `01_COMPRENDRE_OPENCLAW_LOCAL.md`, puis la méthode générale dans `../01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md`.