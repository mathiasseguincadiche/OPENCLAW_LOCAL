# Diagrammes locaux

## Principe

Pour les schémas techniques DevOps, la V0.2 privilégie **diagram-as-code** plutôt qu'une génération d'image opaque.

Le contrat est `config/v1/diagram_policy.yaml`.

Formats privilégiés :

- D2 (`.d2`) ;
- PlantUML (`.puml` / `.plantuml`) ;
- Graphviz (`.dot`).

Sorties supportées :

- SVG ;
- PNG.

## Pourquoi diagram-as-code

Les schémas deviennent :

- versionnables dans Git ;
- reproductibles ;
- relisibles en code review ;
- modifiables sans régénération stochastique ;
- utilisables hors cloud ;
- adaptés aux architectures, flux, pipelines et dépendances.

## Renderer local

```powershell
python .\scripts\29_render_diagram.py `
  .\architecture.d2 `
  .\architecture.svg `
  --dry-run

python .\scripts\29_render_diagram.py `
  .\architecture.d2 `
  .\architecture.svg
```

Le script recherche le renderer local correspondant dans le `PATH`.

Aucun service de rendu distant n'est utilisé par défaut.

## Usage avec les projets

Les sources et rendus d'un projet doivent être placés dans :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\diagrams
```

L'Architecte solutions possède la responsabilité fonctionnelle des schémas, mais la revue qualité reste indépendante.

## Sécurité

Le rendu appelle des exécutables locaux. Il doit donc rester soumis aux mêmes principes que les autres commandes :

- binaires explicitement installés et contrôlés ;
- pas de téléchargement/exécution implicite depuis une source fournie par un LLM ;
- pas de renderer distant par défaut ;
- validation humaine lorsque le rendu implique une commande non approuvée.

## Génération d'images IA

La génération d'images par modèle n'est pas requise pour la V0.2. Elle pourra être ajoutée comme capacité distincte si un besoin réel le justifie, sans remplacer le parcours diagram-as-code pour les schémas techniques.
