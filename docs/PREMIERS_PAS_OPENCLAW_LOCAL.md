# Premiers pas avec OPENCLAW_LOCAL et OpenClaw

## À qui s'adresse ce guide ?

Ce guide présente l'utilisation de `OPENCLAW_LOCAL` sur Windows 11 : installation, vérification, choix des agents, questions ponctuelles, projets multi-agents, preuves et diagnostic.

Le principe à retenir est simple : **OpenClaw orchestre huit rôles ; les rôles utilisent une flotte locale fermée de trois modèles ; le Project Orchestrator gère les projets structurés ; Architecture V2 ne possède aucune route vers un modèle LLM cloud.**

Les outils Web peuvent fournir des sources publiques fraîches, mais le raisonnement reste exécuté par les modèles locaux.

## 1. Modèle mental

```text
Vous
 |
 +--> menu.ps1 / scripts projet
 |
 +--> OpenClaw + Gateway loopback
 |      |
 |      +--> 8 agents spécialisés
 |              |
 |              +--> qwen-max
 |              +--> gemma-deep
 |              +--> devstral-devops
 |
 +--> runtimes locaux
        +--> Ollama/Vulkan
        +--> llama.cpp/SYCL ou Vulkan en qualification
```

### Flotte locale active V2

| Alias | Runtime actif | Usage principal |
|---|---|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | orchestration, recherche, sécurité, release, multimodal |
| `gemma-deep` | `gemma4:12b-it-q4_K_M` | architecture, rédaction, audit, multimodal |
| `devstral-devops` | `hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M` | DevOps, code, scripts, tool-calling, modifications multi-fichiers |

Le nom `devstral-devops` est conservé comme **alias de compatibilité** ; le modèle réellement utilisé en V2 est Ministral 3 14B Reasoning Q4_K_M.

Un challenger local `granite-devops -> granite4.2:8b-q4_K_M` existe pour le benchmark comparatif. Il n'est pas routé, n'est pas un fallback et ne peut pas être promu automatiquement.

### Contextes

```text
8192  -> benchmark/HARD-40M nominal
16384 -> orchestration full-agent OpenClaw nominale
```

Le 16K OpenClaw n'est pas une promotion du benchmark. Aucune promotion 32K n'est automatique.

### Multimodalité

Qwen 3.5 et Gemma 4 traitent les besoins image/PDF du parcours local. Le spécialiste DevOps est text-only : l'information multimodale est d'abord extraite/analysée puis transmise au spécialiste sous forme textuelle et traçable.

## 2. Dépôt Git et plateforme installée

Ne pas confondre :

```text
<REPO>\
├── menu.ps1
├── scripts\
├── src\
├── config\
├── agents\
└── docs\
```

avec la plateforme gérée :

```text
E:\AI\OpenClawLocal\
├── runtime\
├── models\ollama\
├── projects\
├── workspaces\
├── state\
└── proofs\
```

Si `E:` n'existe pas, la racine par défaut est sous `%LOCALAPPDATA%\OpenClawLocal`. `OPENCLAW_LOCAL_ROOT` permet de la changer.

Le code est mis à jour dans `<REPO>`. Les projets, états et preuves vivent sous `<OPENCLAW_LOCAL_ROOT>`.

## 3. Installation

Prévisualiser :

```powershell
.\menu.ps1 -Action install-full -DryRun
```

Installer :

```powershell
.\menu.ps1 -Action install-full
```

Après une première installation, rouvrir PowerShell afin de récupérer le PATH utilisateur.

Pour une machine déjà installée après migration de flotte :

```powershell
.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

## 4. Vérifier que le système est prêt

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
.\menu.ps1 -Action e2e
```

Avant une utilisation sérieuse, le système doit prouver :

- runtime verrouillé ;
- Ollama local ;
- exactement trois modèles requis ;
- huit agents ;
- Gateway joignable ;
- inférence locale ;
- tool-calling ;
- réparation après erreur d'outil ;
- aucune route LLM cloud.

Le E2E prouve le fonctionnement. La qualification mesure ensuite les performances réelles :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Les résultats d'une ancienne flotte sont historiques et **ne qualifient pas Architecture V2**.

## 5. Actions principales du menu

| Action | Utilisation |
|---|---|
| `install-full` | installation/réparation complète |
| `install-core` | runtime verrouillé uniquement |
| `audit` | inspection sans réparation implicite |
| `configure-local` | configuration Ollama et stockage |
| `models` | téléchargement des trois modèles requis |
| `configure-openclaw` | génération/application de la configuration OpenClaw |
| `deploy-agents` | redéploiement des huit workspaces |
| `verify` | smoke local Ollama |
| `benchmark` | benchmark local |
| `inventory` | inventaire matériel/runtime |
| `e2e` | agents + Gateway + outils + réparation |
| `qualification` | qualification matérielle complète |
| `intel-sycl-*` | qualification du backend SYCL |
| `intel-vulkan-*` | qualification du backend Vulkan |
| `golden` | golden projects pré-V1 |
| `logs` | derniers logs et preuves |

`-DryRun` prévisualise une action sans mutation lorsqu'il est supporté.

## 6. Premier échange avec un agent

Exemple avec le Chef des opérations :

```powershell
openclaw agent `
  --agent chef-operations `
  --message "Explique en quelques lignes ton rôle dans OPENCLAW_LOCAL." `
  --timeout 180 `
  --json
```

Pour passer par le routeur gouverné :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent chef-operations `
  --message "Organise ce besoin en étapes vérifiables." `
  --execute
```

Sans `--execute`, le routeur affiche la décision prévue sans lancer le modèle.

L'option historique `--cloud`, si elle est appelée, est refusée explicitement par Architecture V2.

## 7. Quel agent choisir ?

| Agent | Usage |
|---|---|
| `chef-operations` | cadrage, découpage, coordination |
| `expert-recherche` | recherche Web, comparaison de sources |
| `architecte-solutions` | architecture, ADR, compromis, schémas |
| `ingenieur-devops` | CI/CD, IaC, conteneurs, scripts, GitOps |
| `ingenieur-securite` | audit, hardening, secrets, supply-chain |
| `ingenieur-release-forges` | Git, PR/MR, release, packaging |
| `redacteur-technique` | README, procédures, runbooks |
| `auditeur-qualite` | conformité, preuves, revue indépendante |

Si le rôle n'est pas évident, commencer par `chef-operations`.

## 8. Formuler une bonne mission

Une mission utile contient : objectif, contexte, contraintes, résultat attendu et méthode de validation.

Exemple :

```text
Objectif : analyser mon pipeline GitLab.
Contexte : Angular + Spring Boot + PostgreSQL.
Contraintes : approche OPS, sans réécrire le code métier.
Résultat attendu : problèmes, corrections et ordre d'application.
Validation : chaque correction doit avoir une commande ou un test.
```

## 9. Question ponctuelle ou projet orchestré ?

Utiliser un agent directement pour une explication, un diagnostic rapide ou une recherche ciblée.

Utiliser le Project Orchestrator lorsqu'il y a plusieurs fichiers, plusieurs rôles, plusieurs livrables, des dépendances, des validations et un besoin de conserver preuves et versions.

## 10. Créer un projet

```powershell
python .\scripts\28_create_project.py `
  --id mon-premier-projet `
  --title "Mon premier projet OpenClaw" `
  --intake "C:\Travail\mon-projet\consignes.pdf" `
  --source "C:\Travail\mon-projet\repository" `
  --deliverable README `
  --deliverable runbook
```

Le projet central est créé sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\mon-premier-projet\
```

avec `project.json`, `intake/`, `sources/`, `context/`, `work/`, `deliverables/`, `evidence/` et `diagrams/`.

Les originaux d'intake restent immuables. L'ingestion calcule SHA-256/MIME et construit des représentations locales traçables.

## 11. Exécuter le workflow projet

Voir l'état :

```powershell
python .\scripts\32_orchestrate_project.py --project mon-premier-projet --action status
```

Lancer :

```powershell
python .\scripts\32_orchestrate_project.py --project mon-premier-projet --action run --execute
```

Machine d'états :

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

Le système s'arrête sur une ambiguïté humaine, un échec, un gate ou une limite de tentatives. L'historique n'est pas effacé lors d'une correction.

## 12. Clarification humaine

Si le projet attend une réponse :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action resolve `
  --clarification-id clarification-001 `
  --answer "Utiliser le mode Docker local."
```

Le système ne doit pas inventer une décision bloquante à votre place.

## 13. Retrouver résultats et preuves

Projet : `<OPENCLAW_LOCAL_ROOT>\projects\<project-id>`  
Logs : `<OPENCLAW_LOCAL_ROOT>\proofs\logs`  
Preuves E2E/backends : `<OPENCLAW_LOCAL_ROOT>\proofs`  
Benchmarks : `<REPO>\benchmarks\results`

Les workspaces agents sont des snapshots ; ils ne sont pas la source de vérité canonique.

## 14. Backend B580 hybride

Le profil candidat `b580-hybrid` répartit les modèles entre backends locaux selon `runtime_versions.json` et `runtime_backends.yaml`. Il ne devient pas nominal automatiquement. Toute performance doit être remesurée avec les modèles V2.

## 15. Recherche Web et local-only

Pour une donnée actuelle, l'Expert recherche peut utiliser les outils Web, puis Qwen/Gemma/Ministral réalise la synthèse localement. L'usage du Web ne constitue pas un appel à un LLM cloud.

Architecture V2 n'autorise aucun modèle LLM en ligne, même pour masquer une panne ou une lenteur locale.

## 16. Routine de diagnostic

En cas de problème :

```powershell
.\menu.ps1 -Action logs
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw config validate --json
openclaw agents list --json
openclaw gateway status --require-rpc --json
```

Puis consulter `docs/TROUBLESHOOTING.md`.

## 17. Ce qu'il ne faut pas faire

- modifier manuellement un workspace agent comme source de vérité ;
- copier une ancienne preuve de qualification vers la flotte V2 ;
- confondre contexte benchmark 8K et orchestration OpenClaw 16K ;
- promouvoir 32K sans qualification dédiée ;
- ajouter un quatrième modèle routé ou un fallback caché ;
- utiliser un modèle externe pour masquer une panne locale ;
- considérer un E2E comme une qualification de performance ;
- déclarer V1 avant les preuves matérielles et l'approbation humaine.

## 18. Parcours recommandé après fusion V2

```powershell
git checkout main
git pull

.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Ne poursuivre vers les backends candidats, challenger Granite, Golden Projects et décision V1 qu'après conservation et revue des nouvelles preuves.
