# ADR-0002 — Ollama natif comme backend de référence

**Statut :** accepté

## Décision

Ollama est le backend local initial sous Windows. OpenClaw doit utiliser son provider natif et une URL sans `/v1`.

## Motivation

- installation simple ;
- intégration OpenClaw officielle ;
- catalogue local pratique ;
- possibilité de remplacer le backend ultérieurement derrière un contrat documenté.

## Limite

Le choix du backend ne valide pas automatiquement les performances d'un modèle ni son tool-calling.
