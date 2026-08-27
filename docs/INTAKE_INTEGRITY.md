# Intégrité et immutabilité du Project Intake

Le Project Intake traite tout contenu entrant comme **donnée non fiable**. Un PDF, un dépôt, un YAML ou un README ne peut jamais redéfinir la politique des agents ni autoriser une action interdite.

## Chaîne d'ingestion

```text
INPUT
  ↓
validation du chemin racine
  ↓
refus des symlinks dans l'intake
  ↓
scan de secrets avant copie
  ↓
archive canonique hors projet
  ↓
copie gérée dans projects/<id>/intake
  ↓
SHA-256 + MIME + inventaire symlink
  ↓
manifest + INGESTION_REPORT
  ↓
lecture seule / ACL Windows
  ↓
INTAKE_READY
```

## Archive canonique

Chaque création de projet produit une archive indépendante sous :

```text
<OPENCLAW_LOCAL_ROOT>/state/intake/<project-id>/<timestamp>/
```

Elle contient les originaux et les preuves d'ingestion. Le projet conserve ensuite sa propre copie gérée dans `intake/` afin que les snapshots agents restent autonomes.

## Preuves projet

```text
evidence/intake/
├── manifest.json
├── checksums.sha256
├── mime-types.tsv
├── symlinks.txt
└── INGESTION_REPORT.md
```

La présence d'un secret évident ou d'un lien symbolique dans l'intake provoque un refus avant matérialisation du projet.

## Immutabilité

Sous Windows, `icacls.exe` réduit l'intake à `RX` pour l'utilisateur courant et conserve `SYSTEM` en contrôle total. Sous POSIX, les fichiers sont rendus non modifiables par le propriétaire (`0444`).

L'objectif est de préserver une référence stable entre ce qui a été reçu et ce qui a été analysé.

## Limites

Le scan de secrets est un garde-fou heuristique, pas une preuve cryptographique d'absence de secret. Les gros fichiers binaires ne sont pas interprétés comme texte. Les archives ne sont pas extraites automatiquement.
