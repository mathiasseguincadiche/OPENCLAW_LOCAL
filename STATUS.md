# État du projet

## Version courante

**0.2.0 — Local-First Project Workflow + Project Orchestrator + V7 Superset + Document Flow + flotte B580 right-sized**

`OPENCLAW_LOCAL` est une plateforme multi-agent locale avec huit rôles spécialisés, projets, preuves, séparation producteur/auditeur, pédagogie, publication gouvernée et garde-fous fail-closed. Le parcours LLM nominal reste local ; le cloud est une escalade explicite, budgétée et contrôlée.

La CI valide l'architecture logicielle et les contrats. Elle **ne qualifie pas** les performances des modèles, le backend Intel Arc ni la qualité sémantique multimodale sur la workstation réelle.

## Statut de la flotte B580

Le projet est passé de l'ancienne flotte 24–27B à une **flotte candidate officielle à benchmarker**, dimensionnée autour de trois modèles Q4_K_M :

| Alias routé | Runtime | Usage cible |
|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | orchestration, recherche, sécurité, release, raisonnement, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | DevOps/software engineering agentique, texte/code |

L'alias `devstral-devops` reste volontairement conservé pour compatibilité ; son runtime est Qwen2.5 Coder 14B.

**Invariant : exactement trois modèles sont installables/routables par le contrat opérationnel.** Aucun petit modèle ni runtime legacy n'est un fallback supporté.

## Challenger obligatoire : Ministral 3 14B

Gemma 3 12B reste l'incumbent `gemma-deep`, mais sa sélection définitive est désormais conditionnée à une comparaison obligatoire contre :

```text
ministral-tool-calling -> ministral-3:14b-instruct-2512-q4_K_M
```

Ministral est un **challenger de benchmark uniquement** :

- `routing_active: false` ;
- il n'est affecté à aucun des huit rôles ;
- il ne compte pas dans les trois modèles opérationnels ;
- il n'est pas un fallback ;
- il n'entre pas dans le HARD-40M des trois modèles routés ;
- il ne peut pas être auto-promu ;
- toute éventuelle substitution de Gemma exige preuves réelles et décision humaine explicite.

Le motif principal du challenge est le **tool-calling natif** et la capacité de **réparation après retour d'outil en erreur**, tout en conservant l'évaluation de qualité deep, latence, débit et adéquation VRAM.

## Routage nominal

```text
Chef opérations       -> Qwen 3.5 9B
Expert recherche      -> Qwen 3.5 9B + Web
Architecte solutions  -> Gemma 3 12B
Ingénieur DevOps      -> Qwen 2.5 Coder 14B
Ingénieur sécurité    -> Qwen 3.5 9B
Release/Forges        -> Qwen 3.5 9B
Rédacteur technique   -> Gemma 3 12B
Auditeur qualité      -> Gemma 3 12B
                         -> Qwen 3.5 9B si producteur Gemma
```

Ministral n'apparaît pas dans cette table tant qu'une PR future n'a pas explicitement modifié le routage après qualification.

## Politique de contexte

- **8192 tokens** : contexte nominal B580 ;
- **16384 tokens** : stress HARD-40M des trois modèles routés ;
- comparaison Gemma/Ministral : **8192 tokens** ;
- aucune montée de contexte n'est considérée acquise sans mesures réelles.

## HARD-40M

Le HARD-40M reste inchangé dans son principe :

```text
30 cas total
24 cas 8K
 6 cas 16K
2400 s maximum qualification complète
210 s maximum par cas
max_error_rate = 0.0
```

Les trois modèles routés sont tous obligatoires. L'échec de l'un d'eux fait échouer la qualification. Le challenger Ministral ne peut pas servir de contournement.

## Benchmark challenger Gemma / Ministral

Le challenger doit être installé explicitement :

```powershell
ollama pull ministral-3:14b-instruct-2512-q4_K_M
```

Puis :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Le protocole `native_tool_calling_v1` réalise par défaut **3 répétitions à 8K** et vérifie :

1. appel natif `read_file(path="config/prod.yaml")` ;
2. retour contrôlé `file_not_found` ;
3. réparation attendue via `list_files(directory="config")` ;
4. taux de réussite tool-intent/réparation ;
5. erreurs de protocole ;
6. wall time et tokens/s ;
7. taille/résidence VRAM via `/api/ps` lorsque disponible.

Preuve :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Le résultat ne peut produire qu'une preuve destinée à la **sélection humaine** :

```text
PROMOTION_ALLOWED=false
MANUAL_DECISION_REQUIRED=true
```

## Project Orchestrator et Document Flow

Machine d'états principale :

```text
INTAKE_READY
  -> ANALYZED
  -> CLARIFICATION_REQUIRED si nécessaire
  -> PLANNED
  -> ASSIGNED
  -> IN_PROGRESS
  -> VALIDATING
  -> REVIEW
  -> PACKAGING
  -> COMPLETE
```

Le système conserve notamment : Intake immuable, scan de secrets, SHA-256/MIME, ingestion PDF/image/Office, `source_coverage[]`, Artifact Exchange versionné, remediation bornée, séparation producteur/auditeur, package final et approbation humaine.

## Permissions

- Chef/Recherche : orchestration/lecture ;
- Architecte : écriture bornée architecture/diagrammes ;
- DevOps : modification/exécution selon politique ;
- Sécurité : audit read-only ;
- Release/Forges : Git/PR/MR/release sous gates ;
- Rédacteur : documentation versionnée ;
- Auditeur : contrôle indépendant sans correction silencieuse.

## Backends Intel Arc

Candidats :

- `ollama-vulkan` — nominal pré-qualification ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat ;
- `b580-hybrid` — profil candidat.

La sélection exige des mesures B580 réelles : TTFT, tokens/s, VRAM/RAM, stabilité, contexte, tool-calling et comportement multimodal pertinent. Aucun backend n'est déclaré vainqueur par la CI.

## Gates anti-régression

CI/Release couvrent notamment :

```text
21_validate_repository.py
22_validate_configs.py
35_validate_v7_parity.py
39_validate_v7_superset.py
44_validate_document_flow.py
45_validate_model_fleet.py
24_validate_release.py
Ruff
mypy
pytest + coverage
Python 3.12 / 3.13
PowerShell 7
PSScriptAnalyzer
Pester
CodeQL
Dependency Review
```

Le gate flotte exige maintenant à la fois :

- exactement trois modèles routés Q4_K_M ;
- aucun runtime legacy actif ;
- Ministral déclaré séparément comme challenger obligatoire de Gemma ;
- comparaison native tool-calling + réparation ;
- challenger hors routage ;
- promotion automatique interdite et décision humaine obligatoire.

## À exécuter sur matériel réel

GitHub Actions ne peut pas valider :

1. installation réelle Windows 11 + B580 ;
2. E2E OpenClaw avec les trois modèles routés ;
3. HARD-40M complet Qwen 3.5 / Gemma 3 / Qwen 2.5 Coder ;
4. comparaison Gemma 3 12B vs Ministral 3 14B ;
5. vraie multimodalité PDF/image ;
6. Golden Projects ;
7. projet représentatif multi-documents ;
8. comparaison Ollama/Vulkan vs llama.cpp/SYCL/Vulkan ;
9. TTFT, tokens/s, VRAM/RAM, stabilité et résidence GPU ;
10. indépendance producteur/auditeur ;
11. télémétrie réelle ;
12. package final et revue humaine.

## Non prétendu

- aucun des quatre modèles mesurables n'est encore qualifié matériellement ;
- Ministral n'est pas déclaré meilleur que Gemma avant benchmark ;
- aucun débit B580 n'est garanti ;
- aucune résidence VRAM complète n'est supposée ;
- aucun backend n'est auto-sélectionné ;
- aucun fallback cloud silencieux n'est autorisé ;
- aucun résultat matériel n'est inventé par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours nominal réellement qualifié sur Windows 11 + Intel Arc B580, avec HARD-40M, E2E, preuve de sélection Gemma/Ministral, backends, Golden Projects, multimodalité réelle, télémétrie, projet représentatif, limites documentées et validation humaine explicite.
