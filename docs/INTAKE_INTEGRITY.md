# Intake Integrity

Le Project Intake est une frontière de sécurité. Les fichiers reçus sont des **données non fiables** : leur contenu peut décrire le projet, mais ne remplace jamais les contrats OPENCLAW_LOCAL ou les règles des agents.

## Pipeline d'ingestion

```text
INPUT
  ↓
pré-scan secrets
  ↓
refus des symlinks
  ↓
copie contrôlée
  ↓
SHA-256 par fichier
  ↓
inventaire MIME
  ↓
MANIFEST.json
  ↓
INGESTION_REPORT.md
  ↓
lecture seule / ACL Windows
  ↓
INTAKE_READY
```

## Artefacts

Chaque projet contient sous `intake/` :

- `MANIFEST.json` : chemin, SHA-256, taille et MIME de chaque fichier ;
- `checksums.sha256` : liste de contrôle indépendante ;
- `mime-types.tsv` : inventaire MIME ;
- `symlinks.txt` : doit rester vide dans un intake conforme ;
- `INGESTION_REPORT.md` : rapport sans valeur secrète.

Les fichiers originaux conservent leur nom. Les fichiers du dépôt source restent séparés dans `sources/`, qui demeure la vérité technique pour l'implémentation.

## Secrets

L'ingestion est refusée avant matérialisation du projet si un secret évident est détecté : fichiers `.env`, clés privées, tokens GitHub/GitLab/OpenRouter et affectations de type `api_key`, `password`, `access_token` ou `secret_key`.

Le rapport ne copie jamais la valeur détectée.

## Symlinks

Les liens symboliques sont refusés dans l'intake afin d'éviter une lecture hors périmètre. Les sources techniques sont copiées avec leurs symlinks préservés comme liens, sans les suivre pendant la copie.

## Immutabilité

Après génération des métadonnées :

- Windows : `icacls` retire l'écriture à l'utilisateur courant et conserve lecture/exécution ;
- POSIX/CI : fichiers `0400`, dossiers `0500`.

Toute évolution future de l'intake doit créer une nouvelle ingestion contrôlée, jamais modifier silencieusement l'original.
