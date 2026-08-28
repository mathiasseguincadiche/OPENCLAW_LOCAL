# Comprendre OPENCLAW_LOCAL

## Ce qui tourne réellement

```text
Utilisateur
  ↓
menu / scripts / Project Orchestrator
  ↓
OpenClaw et ses 8 rôles
  ↓
Gateway local
  ↓
Ollama
  ↓
3 modèles locaux supportés
```

OpenClaw organise les agents, leurs workspaces, outils et modèles. Ollama sert les modèles. L'orchestrateur ajoute la méthode projet : intake, analyse, plan, tâches, validations, versions, preuves et package final.

## Dépôt et plateforme installée

- `<REPO>` : code Git, scripts, configuration et documentation.
- `<OPENCLAW_LOCAL_ROOT>` : runtime, modèles, projets, workspaces, état et preuves.

Ne travaillez jamais dans un workspace agent comme s'il s'agissait de votre projet principal.

## Local-first

Le fonctionnement nominal reste local. Recherche Web et cloud sont deux concepts distincts : une information récente peut être récupérée sur le Web puis raisonnée localement.