# Modèle de preuve Web

Utilisez ce modèle lorsqu'une tâche du Project Orchestrator contient `web_evidence` dans `required_evidence`.

Le fichier réel doit être créé sous :

```text
evidence/<task-id>/web_evidence.json
```

## Exemple

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-08-28T18:00:00+00:00",
  "task_id": "verifier-compatibilite",
  "sources": [
    {
      "source_id": "official",
      "url": "https://example.org/releases/latest",
      "title": "Latest release",
      "publisher": "Example Project",
      "authority": "source_of_truth",
      "published_at": null,
      "updated_at": null,
      "retrieved_at": "2026-08-28T17:55:00+00:00",
      "date_status": "not_exposed",
      "supports_currentness": true
    },
    {
      "source_id": "independent",
      "url": "https://example.net/analysis",
      "title": "Compatibility analysis",
      "publisher": "Independent Publisher",
      "authority": "secondary",
      "published_at": "2026-08-28T12:00:00+00:00",
      "updated_at": null,
      "retrieved_at": "2026-08-28T17:56:00+00:00",
      "date_status": "known",
      "supports_currentness": false
    }
  ],
  "runtime_evidence": [
    {
      "evidence_id": "runtime-dry-run",
      "kind": "dry_run",
      "observed_at": "2026-08-28T17:58:00+00:00",
      "result": "PASS",
      "command": "outil config patch --dry-run",
      "exit_code": 0,
      "artifact": "evidence/verifier-compatibilite/dry-run.log"
    }
  ],
  "claims": [
    {
      "claim_id": "claim-compatibility",
      "text": "La configuration est acceptée par la version actuellement installée.",
      "volatility": "current",
      "criticality": "high",
      "status": "VERIFIED",
      "confidence": "HIGH",
      "source_ids": ["official", "independent"],
      "runtime_evidence_ids": ["runtime-dry-run"],
      "machine_verifiable": true,
      "currentness_basis": "live_runtime"
    }
  ],
  "conflicts": []
}
```

## Valeurs importantes

### `authority`

- `source_of_truth` : source canonique qui définit directement le fait ;
- `primary` : source officielle ou primaire ;
- `secondary` : analyse secondaire fiable ;
- `community` : forum, blog, discussion ou retour communautaire.

### `volatility`

- `stable` : fait peu susceptible de changer ;
- `volatile` : fait susceptible de changer ;
- `current` : affirmation explicitement présentée comme actuelle.

### `status`

- `VERIFIED` : preuve suffisante ;
- `CONFLICT` : sources contradictoires ;
- `UNVERIFIED` : preuve insuffisante.

Une tâche requise ne peut pas passer avec `CONFLICT` ou `UNVERIFIED`.

### `confidence`

- `HIGH` ;
- `MEDIUM` ;
- `LOW` ;
- `UNVERIFIED`.

Les affirmations `high` et `critical` exigent `HIGH` dans le contrat courant.

### `currentness_basis`

Valeurs prévues :

```text
official_latest_release
official_current_docs
official_registry
official_advisory
official_api
live_runtime
other_authoritative_current_state
```

## Contradiction

Ne supprimez pas une contradiction pour faire passer le validateur. Documentez-la :

```json
{
  "conflict_id": "conflict-001",
  "claim_ids": ["claim-compatibility"],
  "description": "La documentation et le runtime donnent des résultats incompatibles.",
  "status": "OPEN"
}
```

Tant que `status` vaut `OPEN`, la validation doit échouer.

## Validation

```powershell
python .\scripts\46_validate_web_evidence.py `
  --file .\evidence\verifier-compatibilite\web_evidence.json `
  --task-id verifier-compatibilite `
  --require-runtime
```

Résultat attendu :

```text
WEB_EVIDENCE=PASS
```
