# Benchmark

## Objectif

Mesurer avant de choisir : temps au premier token, débit approximatif, mémoire, stabilité, contexte et qualité agentique.

## Scénarios minimaux

1. synthèse courte ;
2. YAML CI/CD ;
3. diagnostic Docker/Kubernetes ;
4. rédaction de runbook ;
5. revue sécurité ;
6. appel d'outil ;
7. correction après retour d'outil ;
8. contexte long représentatif.

## Règle

Les résultats bruts vont dans `benchmarks/results/` et ne sont pas commités par défaut. Une conclusion publiée doit indiquer modèle, quantification, moteur, version, contexte, pilote GPU et protocole.
