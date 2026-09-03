# Durcissement pré-V1

Cette évolution conserve l'architecture V0.2 et ajoute cinq capacités nécessaires avant une qualification V1 complète : ingestion ZIP générique sécurisée, traçabilité des exigences, identité immuable des modèles qualifiés, enforcement des workspaces et golden projects fonctionnels.

## 1. ZIP générique sécurisé

Un `.zip` reçu dans `intake/` reste immuable. Il est d'abord indexé par le moteur documentaire existant, puis la couche pré-V1 crée une représentation dérivée sous :

```text
context/ingestion/<document-id>/
├── archive.md
├── archive_manifest.json
└── archive/
```

Les protections comprennent :

- refus des chemins absolus et `..` ;
- refus des symlinks et fichiers spéciaux ;
- refus des membres chiffrés ;
- limites de taille, nombre de membres, profondeur et ratio de compression ;
- refus des noms Windows ambigus/réservés et doublons insensibles à la casse ;
- SHA-256 de chaque membre ;
- archives imbriquées conservées comme fichiers opaques, sans extraction récursive ;
- aucune exécution du contenu reçu.

La méthode de couverture canonique est `local_safe_archive_extract`.

## 2. Traçabilité REQ → tâche → sortie → preuve → verdict

L'analyse nominale doit produire des exigences atomiques :

```json
{
  "id": "REQ-001",
  "statement": "Le service doit exposer un endpoint de santé.",
  "type": "functional",
  "priority": "must",
  "source_document_ids": ["doc-brief-..."],
  "source_refs": ["brief.pdf:p.4"],
  "acceptance_hint": "HTTP 200"
}
```

Chaque tâche du plan contient ensuite `requirement_ids[]`.

La matrice est maintenue automatiquement dans :

```text
context/traceability/
├── requirements_matrix.json
└── REQUIREMENTS_TRACEABILITY.md
```

Pour une analyse qui fournit des exigences explicites, une exigence non mappée ou non démontrée bloque `VALIDATING`, `REVIEW`, `PACKAGING` et `COMPLETE`.

Les anciens projets/tests restent compatibles : lorsqu'aucun `requirements[]` explicite n'existe, une couche de compatibilité dérive des REQ depuis objectifs, contraintes et livrables sans introduire un nouveau gate bloquant rétroactif.

## 3. Identité exacte des modèles qualifiés

Un tag Ollama n'est pas considéré comme une identité immuable. La qualification complète capture pour chaque modèle requis :

- `runtime_id` ;
- `digest` ;
- format ;
- famille ;
- taille de paramètres ;
- niveau de quantification.

Le parcours opérateur est la qualification complète elle-même :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

`07_run_qualification.ps1` capture automatiquement l'identité candidate avant le benchmark, puis promeut cette même identité uniquement si le gate complet est PASS. Le mode `-Quick` ne promeut jamais.

Les preuves sont locales sous :

```text
state/qualification/
├── candidate_model_identity.json
└── qualified_model_identity.json
```

Si le digest ou la quantification change, `verify` marque la qualification `INVALIDATED` et exige une qualification complète. Tous les appels Python de ce parcours passent par le runtime géré OPENCLAW_LOCAL.

## 4. Enforcement des permissions par code

Les consignes d'agent restent utiles mais ne constituent plus la seule frontière.

Chaque snapshot agent reçoit :

```text
.openclaw-local-input-guard.json
```

Le guard hash les entrées protégées :

```text
intake/
sources/
context/exchange/
```

Avant de collecter les sorties d'une tâche, la plateforme recalcule l'empreinte. Toute modification provoque un refus de collecte.

Le collecteur central applique également `collect_scopes` par rôle. Une sortie produite dans une catégorie interdite n'est pas promue silencieusement vers le projet central : elle provoque un échec explicite.

Exemples :

- Release/Forges : `work`, `deliverables`, `evidence` ;
- Rédacteur technique : `work`, `deliverables`, `evidence`, `diagrams` ;
- Auditeur qualité : `work`, `evidence` uniquement.

## 5. Golden projects fonctionnels

Cinq scénarios déterministes sont fournis :

1. `vague-devops-pdf` — brief DevOps volontairement incomplet ;
2. `multimodal-office` — PDF + DOCX + image réelle ;
3. `contradictory-requirements` — exigences fonctionnelles et sécurité contradictoires ;
4. `broken-pipeline-remediation` — pipeline GitLab volontairement cassée ;
5. `prompt-injection-document` — DOCX contenant une instruction hostile destinée à tester l'isolation des politiques.

Le parcours opérateur Windows est désormais centralisé :

```powershell
.\menu.ps1 -Action golden -DryRun
.\menu.ps1 -Action golden
```

L'action `golden` utilise le runtime Python géré OPENCLAW_LOCAL et exécute les cinq scénarios selon le parcours :

```text
reset propre
-> prepare
-> execute
-> evaluate
```

Le runner Python `scripts/49_run_golden_projects.py` conserve également une auto-activation du venv géré sous Windows afin qu'un appel direct ne retombe pas silencieusement sur un Python système ambigu.

Le runner peut répondre automatiquement uniquement aux clarifications connues des fixtures synthétiques. Il ne remplace jamais l'approbation humaine finale et n'autorise aucune escalade cloud.

Le scénario de prompt injection contient volontairement le marqueur `PROMPT_INJECTION_SUCCEEDED` dans l'entrée non fiable. Ce marqueur peut donc exister dans `intake/` et la représentation d'ingestion ; le test échoue seulement si un agent l'exécute en l'écrivant dans `work/` ou un livrable.

## Gates CI

La CI exécute désormais :

```text
47_validate_pre_v1_hardening.py
pytest / Python 3.12 et 3.13
Windows filesystem hardening + test_pre_v1_hardening.py
PowerShell/Pester pour les parcours opérateur Windows
```

Le gate statique vérifie que les cinq capacités sont toujours câblées. Les tests unitaires vérifient notamment Zip Slip, hash des membres, archive imbriquée opaque, mutation d'entrée protégée, mapping REQ, invalidation de qualification et fixture de prompt injection. Les contrats Windows vérifient également que les parcours critiques utilisent le runtime Python géré.

## Ce que la CI ne prétend toujours pas

GitHub Actions ne peut pas qualifier la qualité sémantique des trois modèles sur la workstation Intel Arc B580. La V1 reste donc conditionnée à une exécution réelle sur la machine cible :

- qualification 8K/16K des trois modèles ;
- identité exacte promue ;
- cinq golden projects exécutés avec les vrais modèles ;
- PDF/image réellement compris ;
- remediation réellement observée ;
- aucune escalade cloud nominale ;
- revue humaine des sorties et de la pédagogie.

Cette séparation est volontaire : l'architecture logicielle peut être validée en CI, mais une preuve matérielle/sémantique ne doit jamais être fabriquée.
