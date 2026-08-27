# État du projet

## Version courante

**0.2.0 — Local-First Project Workflow + Project Orchestrator + V7 Superset + Document Flow + flotte performance-only**

`OPENCLAW_LOCAL` est le successeur local-first de `openclaw_openrouter` : huit rôles spécialisés, contrats, projets, preuves, séparation producteur/auditeur, pédagogie, publication gouvernée et garde-fous V7 sont préservés ou renforcés. Le parcours LLM nominal reste local ; le cloud est une escalade explicite, budgétée et contrôlée.

La CI valide l'architecture logicielle et les contrats. Elle **ne qualifie pas** les performances des modèles, le backend Intel Arc ni la qualité sémantique multimodale sur la workstation réelle.

## Parcours projet implémenté

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

Le système dispose de :

- Project Intake durci avec archive canonique, scan de secrets, refus symlinks, SHA-256, MIME et ACL/lecture seule ;
- manifeste projet strict avec classification et criticité ;
- analyse structurée, clarifications humaines, plan et Task Contracts enrichis ;
- exécution locale versionnée avec tentatives bornées ;
- remediation ciblée après échec de validation/review ;
- checksums et preuves d'intégrité par phase ;
- package final avec SHA-256 et approbation humaine obligatoire.

## Document Ingestion et Artifact Exchange

Les fichiers utilisateur peuvent être indexés et traités sans modifier les originaux :

- texte/code/configuration : représentation locale ;
- DOCX/PPTX/XLSX : extraction locale déterministe ;
- PDF : outil OpenClaw `pdf`, avec parcours borné et fallback vision lorsque nécessaire ;
- images : `view_image` ;
- index SHA-256/MIME/document_id et provenance ;
- `source_coverage[]` obligatoire pour chaque document, avec `READ`, `PARTIAL` ou `UNREADABLE` ;
- une méthode de lecture doit être compatible avec le type réel du document ;
- un document illisible ne peut pas être présenté comme compris.

Les sorties de tâches sont échangées via des bundles versionnés :

```text
context/exchange/<task-id>/
├── self/run-NNN/
└── dependencies/<producer>/run-NNN/
```

Les sorties `PASS` sont propagées aux dépendants ; les sorties `FAIL` restent dans l'historique mais ne deviennent jamais des entrées valides. Provenance, tentative et SHA-256 sont conservés, et les consommateurs ne modifient pas les bundles reçus.

## Pédagogie et accessibilité

- profils `efficient` 90/10, `balanced` 70/30 et `intensive` 60/40 ;
- modes guided/assisted/autonomous/evaluation ;
- `SKILLS_MATRIX.csv`, `LEARNING_JOURNAL.md`, `TEACH_BACK.md`, `RETENTION_PLAN.yaml` et Learning Contract ;
- verdict pédagogique distinct du verdict technique ;
- quatre profondeurs documentaires : Comprendre, Utiliser, Approfondir, Diagnostiquer ;
- exactitude technique et sécurité prioritaires sur la simplification.

## Publication gouvernée

Machine de publication distincte :

```text
LOCAL_IN_PROGRESS
→ LOCAL_VALIDATED
→ READY_TO_PUBLISH
→ REMOTE_CREATED
→ BRANCH_PUSHED
→ PR_MR_OPEN
→ CI_GREEN
→ REMOTE_CLONE_VALIDATED
→ RELEASE_CREATED (optionnel)
→ PUBLISHED_AND_VERIFIED
```

State gates et action gates protègent notamment création distante, visibilité, PR/MR, merge, release, branch protection, force-push et suppression. Les preuves distantes, clone propre et approbations humaines ne sont jamais supposés.

## Permissions et séparation des responsabilités

- Chef et Expert Recherche : lecture/orchestration, pas de production silencieuse de code ;
- Architecte : writer borné à `context/architecture/` et `diagrams/`, sans écriture générique ;
- DevOps : modification/exécution dans son workspace selon politique ;
- Sécurité : audit/read-only sur les sources auditées ;
- Release/Forges : Git/PR/MR/release sous gates ;
- Rédacteur : documentation versionnée, sans réécriture des sources de vérité ;
- Auditeur : contrôle indépendant, sans correction silencieuse.

## Flotte IA locale — performance-only

**Trois modèles locaux, et uniquement trois :**

| Alias | Runtime | Tier | Usage cible |
|---|---|---|---|
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX | orchestration, recherche, sécurité, release, raisonnement complexe |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP | architecture, rédaction, audit, contre-revue multimodale |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST | DevOps/software engineering agentique |

Il n'existe **aucun petit modèle local ou modèle legacy supporté comme fallback**. Les trois modèles ci-dessus sont `required: true` dans le catalogue et constituent exactement la flotte installable/routable par la plateforme.

### Routage par rôle

```text
Chef opérations       -> Qwen 3.8 27B
Expert recherche      -> Qwen 3.8 27B + Web
Architecte solutions  -> Gemma 4 26B
Ingénieur DevOps      -> Devstral Small 2 24B
Ingénieur sécurité    -> Qwen 3.8 27B
Release/Forges        -> Qwen 3.8 27B
Rédacteur technique   -> Gemma 4 26B
Auditeur qualité      -> Gemma 4 26B ; bascule Qwen 3.8 27B si producteur Gemma
```

Cette table définit le **support logiciel et le routage nominal**. Elle n'est pas une preuve de performance B580.

## Qualification de la flotte

La suite active reste `devops-v2`. Les **trois modèles supportés sont tous requis** pour le gate global :

```powershell
.\scripts\windows\03_pull_models.ps1
.\scripts\windows\07_run_qualification.ps1
```

L'échec de l'un des trois modèles fait échouer le gate de qualification de la flotte. Il n'existe aucun candidat local optionnel à promouvoir dans le routage.

La qualification réelle exige encore les critères de `qualification_policy.yaml`, notamment E2E OpenClaw, tool-calling, réparation après erreur, stabilité sur trois runs, parcours Project Intake/Web, multimodalité PDF/image, absence de dépendance cloud nominale et revue humaine.

## Backends Intel Arc

Candidats :

- `ollama-vulkan` — nominal pré-qualification ;
- `llama-cpp-sycl` — candidat ;
- `llama-cpp-vulkan` — candidat.

La sélection finale exige des mesures B580 réelles : TTFT, tokens/s, VRAM, RAM, stabilité, contexte et tool-calling. Aucun backend n'est déclaré vainqueur par la CI.

## Télémétrie

- stockage local append-only ;
- modèle, agent, backend, route et durée ;
- TTFT, tokens/s, tokens, VRAM/RAM seulement lorsqu'ils sont observés ;
- tool calls, retries, transitions locales et escalade cloud ;
- prompts, réponses, secrets et documents privés interdits ;
- métriques inconnues jamais fabriquées.

## Gates anti-régression

La CI et Release couvrent notamment :

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

Le gate flotte vérifie que le catalogue contient **exactement** les trois runtimes supportés, que tous les rôles n'utilisent que ces alias, qu'aucun ancien petit modèle ne réapparaît dans les surfaces actives, que les trois modèles sont obligatoires dans la qualification et que l'indépendance de l'Auditeur reste respectée.

## À exécuter sur matériel réel

Les points suivants **ne peuvent pas être validés par GitHub Actions** :

1. installation complète Windows 11 Pro sur la workstation cible ;
2. ACL d'Intake dans l'environnement final ;
3. E2E OpenClaw avec les trois modèles réellement chargés ;
4. vrai projet multi-documents PDF/images/Office/code ;
5. qualité sémantique de lecture de PDF scannés et images ;
6. benchmark Qwen 3.8 27B ;
7. benchmark Gemma 4 26B ;
8. benchmark Devstral Small 2 24B ;
9. comparaison Ollama/Vulkan vs llama.cpp/SYCL vs llama.cpp/Vulkan ;
10. mesure TTFT, tokens/s, VRAM, RAM, stabilité, tool-calling et consommation avec offload ;
11. qualification 8K/16K puis éventuelle montée 32K/64K selon preuves ;
12. test d'indépendance réelle producteur/auditeur sur des tâches représentatives ;
13. télémétrie réelle sur un projet complet ;
14. publication réelle jusqu'au clone propre/audit distant ;
15. validation du coût réel des rares escalades OpenRouter.

## Non prétendu

- équivalence systématique d'un modèle local avec un modèle frontier cloud ;
- débit garanti sur Intel Arc B580 avant benchmark ;
- résidence VRAM complète des modèles 24–27B sur 12 Go ;
- contexte maximal théorique utilisable avec un bon débit sur cette workstation ;
- compréhension parfaite des PDF/images avant E2E ;
- sélection automatique d'un backend sans preuve ;
- escalade cloud automatique par le Project Orchestrator ;
- publication distante sans preuve et approbation ;
- résultat matériel inventé par la CI.

## Critère pour V1.0.0

La version `1.0.0` reste réservée à un parcours nominal réellement qualifié sur la workstation Windows 11 + Intel Arc B580, avec au moins un projet complet exécuté de `INTAKE_READY` jusqu'au package final, preuves reproductibles, multimodalité réelle, télémétrie observée, limites documentées et validation humaine.
