# État du projet

## Version courante

**0.2.0 — Architecture V2 local-only + Project Orchestrator + V7 Superset + Document Flow + flotte B580**

`OPENCLAW_LOCAL` est une plateforme multi-agent locale avec huit rôles spécialisés, projets, preuves, séparation producteur/auditeur, pédagogie, publication gouvernée et garde-fous fail-closed. **Aucun modèle LLM cloud n'est supporté en Architecture V2.** Les outils Web peuvent fournir des informations fraîches, mais l'analyse et le raisonnement restent exécutés par les modèles locaux.

La CI valide l'architecture logicielle et les contrats. Elle **ne qualifie pas** les performances des modèles, le backend Intel Arc ni la qualité sémantique multimodale sur la workstation réelle.

## Flotte V2 candidate B580

La flotte opérationnelle candidate contient exactement trois modèles Q4_K_M :

| Alias routé | Runtime local | Usage cible |
|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | orchestration, recherche, sécurité, release, raisonnement, multimodal |
| `gemma-deep` | `gemma4:12b-it-q4_K_M` | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M` | DevOps/software engineering agentique, outils, texte/code |

L'alias `devstral-devops` est conservé pour compatibilité des routes et états. Son runtime V2 est **Ministral 3 14B Reasoning Q4_K_M**, local via Ollama.

**Invariant : exactement trois modèles sont routables par le contrat opérationnel.** Aucun petit modèle, runtime legacy ou modèle en ligne n'est un fallback supporté.

## Challenger local : Granite 4.2 8B

Le catalogue déclare séparément :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

Granite est un **challenger de benchmark local** du spécialiste DevOps :

- `routing_active: false` ;
- aucun des huit rôles ne l'utilise nominalement ;
- il ne compte pas dans les trois modèles opérationnels ;
- il n'est pas un fallback ;
- il ne remplace pas un échec HARD-40M ;
- `automatic_promotion: false` ;
- toute substitution exige une décision humaine explicite appuyée sur les preuves B580.

Le challenge couvre notamment coding, tool-calling natif, réparation après erreur d'outil et adéquation B580.

## Routage nominal

```text
Chef opérations       -> Qwen 3.5 9B
Expert recherche      -> Qwen 3.5 9B + outils Web
Architecte solutions  -> Gemma 4 12B
Ingénieur DevOps      -> Ministral 3 14B Reasoning
Ingénieur sécurité    -> Qwen 3.5 9B
Release/Forges        -> Qwen 3.5 9B
Rédacteur technique   -> Gemma 4 12B
Auditeur qualité      -> Gemma 4 12B
                         -> Qwen 3.5 9B si séparation de famille requise
```

Granite n'apparaît pas dans ce routage tant qu'une décision humaine future n'a pas explicitement modifié le contrat après qualification.

## Politique de contexte

Architecture V2 sépare explicitement le benchmark de l'orchestration :

- **8192 tokens** : contexte nominal benchmark/HARD-40M ;
- **16384 tokens** : contexte nominal d'orchestration OpenClaw ;
- le 16384 OpenClaw n'est pas une promotion du benchmark ;
- **aucune promotion automatique à 32K** ;
- toute extension future exige une qualification dédiée.

## HARD-40M

Le HARD-40M reste inchangé :

```text
30 cas total
24 cas 8K
 6 cas 16K
2400 s maximum qualification complète
210 s maximum par cas
max_error_rate = 0.0
```

Les trois modèles routés sont obligatoires. L'échec de l'un d'eux fait échouer la qualification. Granite constitue une preuve comparative séparée et ne peut servir de contournement.

## Benchmark challenger Ministral / Granite

Le challenger est installé explicitement lorsque le test est demandé :

```powershell
ollama pull granite4.2:8b-q4_K_M
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Le protocole `native_tool_calling_v1` réalise par défaut 3 répétitions à 8K et vérifie appel d'outil natif, gestion d'un retour contrôlé en erreur, réparation attendue, erreurs de protocole, wall time, tokens/s et résidence VRAM lorsque disponible.

Preuve :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Le résultat reste destiné à la **sélection humaine** :

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

Candidats locaux :

- `ollama-vulkan` — nominal pré-qualification ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat ;
- `b580-hybrid` — profil candidat.

La sélection exige des mesures B580 réelles : TTFT, tokens/s, VRAM/RAM, stabilité, contexte, tool-calling et multimodalité pertinente. Aucun backend n'est déclaré vainqueur par la CI.

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
pytest + coverage >= 75 %
Python 3.12 / 3.13
PowerShell 7
PSScriptAnalyzer
Pester
CodeQL
Dependency Review
```

Le gate flotte V2 exige :

- exactement trois modèles routés Q4_K_M ;
- Qwen 3.5 9B + Gemma 4 12B + Ministral 3 14B Reasoning ;
- aucun runtime legacy actif ;
- `local_only: true` ;
- `cloud_models_supported: false` ;
- toute demande cloud refusée ;
- Granite 4.2 déclaré séparément comme challenger local ;
- promotion automatique interdite et décision humaine obligatoire.

## À exécuter sur matériel réel

GitHub Actions ne peut pas valider :

1. installation réelle Windows 11 + B580 ;
2. E2E OpenClaw avec les trois modèles routés ;
3. HARD-40M complet Qwen 3.5 / Gemma 4 / Ministral 3 Reasoning ;
4. comparaison Ministral 3 Reasoning vs Granite 4.2 ;
5. vraie multimodalité PDF/image ;
6. Golden Projects ;
7. projet représentatif multi-documents ;
8. comparaison Ollama/Vulkan vs llama.cpp/SYCL/Vulkan ;
9. TTFT, tokens/s, VRAM/RAM, stabilité et résidence GPU ;
10. indépendance producteur/auditeur ;
11. télémétrie réelle ;
12. package final et revue humaine.

## Non prétendu

- aucun modèle n'est encore qualifié matériellement par cette PR ;
- Granite n'est pas déclaré meilleur que Ministral avant benchmark ;
- aucun débit B580 n'est garanti ;
- aucune résidence VRAM complète n'est supposée ;
- aucun backend n'est auto-sélectionné ;
- aucun LLM cloud n'est supporté ;
- aucun résultat matériel n'est inventé par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours réellement qualifié sur Windows 11 + Intel Arc B580, avec HARD-40M, E2E, preuve de sélection du spécialiste, backends, Golden Projects, multimodalité réelle, télémétrie, projet représentatif, limites documentées et validation humaine explicite.
