# Document Ingestion + Artifact Exchange

## Objectif

Cette couche permet à un projet `OPENCLAW_LOCAL` de recevoir des consignes et références hétérogènes (PDF, images, documents Office, texte et fichiers inconnus) sans modifier les originaux, puis de faire circuler de façon versionnée les productions des agents entre tâches dépendantes.

Le principe reste local-first : l'ingestion documentaire ne nécessite aucun service cloud et les workspaces agents restent des snapshots jetables du projet central.

## Sources de vérité

- `intake/` : originaux immuables déclarés par l'utilisateur ;
- `sources/` : dépôt ou autres sources techniques réelles ;
- `context/ingestion/` : représentation dérivée locale et registre documentaire ;
- `context/exchange/` : bundles versionnés de sorties entre tâches ;
- `deliverables/`, `work/`, `evidence/`, `diagrams/` : sorties centrales collectées.

Une extraction ou un résumé ne remplace jamais l'original. En cas de divergence, `intake/` et `sources/` restent prioritaires.

## Document Ingestion

La création via `scripts/28_create_project.py` construit immédiatement `context/ingestion/index.json`. Pour un projet plus ancien, `ensure_current_project_schema()` crée automatiquement l'index au prochain passage de l'orchestrateur.

La CLI dédiée est :

```powershell
python .\scripts\42_project_ingest.py --project mon-projet --validate-only
```

Une reconstruction explicite est possible avec `--force`; elle ne modifie jamais `intake/`.

### PDF

Les PDF restent sous `intake/`. L'index indique à l'agent d'utiliser l'outil OpenClaw `pdf`. Le modèle documentaire reste local : Qwen en primaire et Gemma en fallback. OpenClaw extrait le texte et, pour les pages pauvres en texte ou scannées, peut rendre les pages en images vers un modèle vision. Les documents longs sont parcourus par tranches conformes à `pdfMaxPages`.

### Images

PNG, JPEG, WebP, BMP, GIF et TIFF sont indexés avec l'outil `view_image`. Les agents ne doivent pas inventer les détails illisibles.

### DOCX, PPTX et XLSX

Ces formats sont extraits localement avec la bibliothèque standard Python en lisant les parties XML du conteneur ZIP :

- DOCX : document principal, en-têtes, pieds de page, notes et commentaires utiles ;
- PPTX : texte des slides dans l'ordre ;
- XLSX : cellules, formules et valeurs observables dans les worksheets.

La représentation est écrite sous `context/ingestion/<document-id>/extracted.md` avec SHA-256 de l'original.

### Texte et formats inconnus

Les formats textuels usuels sont normalisés dans `extracted.md`. Les formats inconnus sont au minimum inventoriés et doivent être déclarés `UNREADABLE` si aucun outil compatible ne peut les lire.

## Source coverage obligatoire

L'analyse du Chef des opérations doit désormais produire `source_coverage[]` avec exactement une entrée par document indexé :

```json
{
  "document_id": "doc-consignes-1234567890",
  "status": "READ",
  "method": "pdf",
  "notes": "Pages 1-18 analysées"
}
```

Statuts : `READ`, `PARTIAL`, `UNREADABLE`.

Méthodes : `local_text_extract`, `local_zip_xml_extract`, `pdf`, `view_image`, `raw_file`.

Un document `UNREADABLE` doit également apparaître dans `missing_information[]`. Un index absent, incomplet ou périmé bloque l'analyse.

## Artifact Exchange

Chaque tâche produit dans son workspace sous :

```text
work/<task-id>/
deliverables/<task-id>/
evidence/<task-id>/
diagrams/<task-id>/
```

Après collecte centrale, l'orchestrateur crée toujours un historique propre à la tâche :

```text
context/exchange/<task-id>/self/run-001/
context/exchange/<task-id>/self/run-002/
```

Une tentative `FAIL` reste donc disponible pour correction sans être écrasée.

Lorsqu'une tâche est `PASS`, ses sorties sont aussi propagées aux tâches dépendantes, y compris transitivement selon la politique :

```text
context/exchange/<consumer>/dependencies/<producer>/run-001/
```

Chaque bundle possède `manifest.json` avec provenance, statut du producteur, tentative, liste des fichiers, SHA-256 individuels et digest agrégé.

Les consommateurs doivent considérer ces bundles en lecture seule et produire une nouvelle version dans leurs propres répertoires de tâche.

## Resynchronisation des agents

Après chaque tentative collectée, les agents affectés par l'échange sont resynchronisés depuis le projet central. Un agent dépendant reçoit donc automatiquement les sorties validées de ses prédécesseurs avant d'exécuter sa tâche.

Cette architecture évite les workspaces partagés :

```text
Projet central
    ↓
collecte versionnée
    ↓
context/exchange
    ↓
resync ciblé
    ↓
workspace du consommateur
```

## Fail-closed

Les transitions vers `VALIDATING`, `REVIEW`, `PACKAGING` ou `COMPLETE` sont refusées si l'Artifact Exchange attendu est absent ou si un hash ne correspond plus.

Audit manuel :

```powershell
python .\scripts\43_project_exchange.py --project mon-projet
python .\scripts\43_project_exchange.py --project mon-projet --task task-002
```

## Sécurité et confidentialité

- `tools.fs.workspaceOnly=true` reste obligatoire ;
- les huit rôles disposent de `pdf` et `view_image`, mais gardent leurs restrictions d'écriture propres ;
- l'Ingénieur sécurité et l'Auditeur restent non-mutants ;
- les originaux Intake restent immuables ;
- aucun contenu documentaire n'est enregistré dans la télémétrie ;
- l'ingestion ne déclenche jamais une escalade cloud automatique.

## Anti-régression

`scripts/44_validate_document_flow.py` vérifie la politique d'ingestion, les outils PDF/image, la couverture documentaire, le câblage OpenClaw, la propagation versionnée, les hashes et le fail-closed de l'orchestrateur. Le gate est exécuté par CI et Release.
