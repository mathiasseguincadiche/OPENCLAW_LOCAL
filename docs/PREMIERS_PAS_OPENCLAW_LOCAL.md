# Premiers pas avec OPENCLAW_LOCAL et OpenClaw

## À qui s'adresse ce guide ?

Ce guide est destiné à une personne qui utilise pour la première fois une IA locale avec OpenClaw et `OPENCLAW_LOCAL`.

L'objectif n'est pas seulement de donner des commandes à copier-coller. Il explique :

- ce qui tourne réellement sur la machine ;
- la différence entre OpenClaw, Ollama, les modèles, les agents et le Project Orchestrator ;
- comment vérifier que le système est prêt ;
- comment parler à un agent ;
- comment choisir le bon rôle ;
- comment lancer un vrai projet multi-agents ;
- comment répondre à une clarification humaine ;
- où retrouver les livrables, preuves, logs et versions ;
- ce qu'il ne faut pas modifier manuellement ;
- comment diagnostiquer un problème sans masquer une panne locale par le cloud.

Ce document décrit **les interfaces réellement versionnées dans ce dépôt**. Il utilise donc principalement PowerShell, `menu.ps1`, les scripts Python du projet et la CLI OpenClaw.

---

## 1. Le modèle mental à retenir

`OPENCLAW_LOCAL` n'est pas « un chatbot unique installé sur le PC ».

C'est une petite plateforme locale composée de plusieurs couches :

```text
Vous
 |
 +--> menu.ps1 / scripts projet
 |
 +--> OpenClaw
 |      |
 |      +--> 8 agents spécialisés
 |      |
 |      +--> Gateway local
 |
 +--> Ollama
        |
        +--> Qwen 3.8 27B
        +--> Gemma 4 26B
        +--> Devstral Small 2 24B
```

À cela s'ajoutent :

- le **Project Orchestrator**, qui transforme un dossier de travail en projet structuré ;
- l'**Artifact Exchange**, qui transmet les sorties versionnées entre tâches dépendantes ;
- les **preuves**, qui permettent de vérifier ce qui s'est réellement passé ;
- la **télémétrie locale**, qui mesure les exécutions sans stocker le contenu privé des prompts/réponses ;
- une politique **local-first**, qui interdit le fallback cloud silencieux.

### OpenClaw

OpenClaw est la couche d'exécution des agents. Il connaît leurs workspaces, leurs outils et leur configuration.

### Ollama

Ollama sert les modèles locaux sur la machine, via l'API loopback locale.

### Les modèles

La flotte supportée est volontairement fermée à exactement trois modèles :

| Alias | Modèle | Usage principal |
|---|---|---|
| `qwen-max` | `qwen3.8:27b` | orchestration, recherche, sécurité, release |
| `gemma-deep` | `gemma4:26b` | architecture, rédaction, audit |
| `devstral-devops` | `devstral-small-2:24b` | DevOps, code, scripts, modifications multi-fichiers |

Il n'existe pas de petit modèle local de secours dans le parcours nominal.

### Les agents

Un agent n'est pas un modèle supplémentaire. Un agent est un **rôle**, avec :

- une mission ;
- des règles ;
- des permissions d'outils ;
- un workspace ;
- un routage vers l'un des trois modèles.

### Le Project Orchestrator

Le Project Orchestrator est ce qui fait passer le système d'une simple conversation à un fonctionnement de type équipe projet :

```text
INTAKE_READY
    ↓
ANALYZED
    ↓
CLARIFICATION_REQUIRED si nécessaire
    ↓
PLANNED
    ↓
ASSIGNED
    ↓
IN_PROGRESS
    ↓
VALIDATING
    ↓
REVIEW
    ↓
PACKAGING
    ↓
COMPLETE
```

---

## 2. Ne pas confondre le dépôt Git et la plateforme installée

Il y a **deux emplacements différents**.

### Le dépôt Git

C'est le clone que vous mettez à jour avec Git et depuis lequel vous lancez les commandes :

```text
<REPO>\
├── menu.ps1
├── scripts\
├── src\
├── config\
├── agents\
└── docs\
```

Exemple :

```text
C:\Users\<vous>\OPENCLAW_LOCAL
```

### La plateforme gérée

C'est l'endroit où vivent le runtime, les modèles, les projets et l'état local.

Si `E:` existe, le défaut est :

```text
E:\AI\OpenClawLocal\
├── runtime\
├── models\ollama\
├── projects\
├── workspaces\
├── state\
└── proofs\
```

Sinon, la racine par défaut est sous :

```text
%LOCALAPPDATA%\OpenClawLocal
```

La variable `OPENCLAW_LOCAL_ROOT` permet de choisir explicitement une autre racine.

### Règle pratique

- vous **mettez à jour le code** dans `<REPO>` ;
- vous **conservez vos projets et preuves** dans `<OPENCLAW_LOCAL_ROOT>`.

Ne mélangez pas les deux.

---

## 3. Quand peut-on commencer à utiliser l'IA ?

L'installation complète doit d'abord terminer avec :

```text
ACTION_RESULT=PASS
```

Après une première installation, fermez puis rouvrez PowerShell afin de récupérer le PATH utilisateur configuré par le bootstrap.

Ensuite, depuis le dépôt :

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Avant une utilisation sérieuse, exécutez également :

```powershell
.\menu.ps1 -Action e2e
```

Le résultat attendu est notamment :

- runtime conforme ;
- Ollama accessible localement ;
- trois modèles présents ;
- huit agents configurés ;
- Gateway joignable ;
- inférence locale fonctionnelle ;
- tool-calling fonctionnel ;
- réparation après erreur d'outil fonctionnelle ;
- aucune escalade cloud sur le parcours nominal.

La qualification matérielle vient ensuite :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Un E2E réussi prouve le fonctionnement. La qualification mesure ensuite les performances réelles de la machine.

---

## 4. La routine simple au début de chaque session

Pour les premières utilisations, gardez cette routine :

```powershell
cd <REPO>
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Si ces contrôles sont conformes, vous pouvez travailler.

Après un redémarrage Windows, un changement de pilote GPU, de modèle, de backend ou de runtime, refaire les contrôles avant de conclure qu'un problème vient du modèle.

---

## 5. Le menu : à quoi sert chaque action ?

Afficher le menu interactif :

```powershell
.\menu.ps1
```

Ou lancer directement une action :

```powershell
.\menu.ps1 -Action <action>
```

| Action | Quand l'utiliser |
|---|---|
| `install-full` | première installation ou réparation complète reproductible |
| `install-core` | installer/réparer seulement le runtime verrouillé |
| `audit` | inspecter la machine sans effectuer de réparation implicite |
| `configure-local` | configurer/vérifier Ollama et l'emplacement des modèles |
| `models` | télécharger/vérifier les trois modèles locaux requis |
| `configure-openclaw` | générer et appliquer la configuration OpenClaw |
| `deploy-agents` | redéployer les huit workspaces agents |
| `verify` | vérifier l'inférence locale Ollama |
| `benchmark` | lancer le benchmark simple |
| `inventory` | collecter l'inventaire matériel/runtime |
| `e2e` | tester les huit agents, le Gateway, les outils et la réparation |
| `qualification` | lancer la qualification matérielle complète |
| `team` | afficher les contrats principaux de l'équipe IA |
| `docs` | afficher le chemin du portail documentaire |
| `logs` | afficher les derniers logs et emplacements de preuves |

### Dry-run

Quand l'action le supporte :

```powershell
.\menu.ps1 -Action install-full -DryRun
```

Le dry-run sert à prévisualiser sans mutation.

---

## 6. Premier échange avec un agent

Pour un premier test, commencez avec le Chef des opérations.

La forme OpenClaw utilisée par les tests E2E du projet est :

```powershell
openclaw agent `
  --agent chef-operations `
  --message "Explique en quelques lignes ton rôle dans OPENCLAW_LOCAL." `
  --timeout 180 `
  --json
```

La sortie est volontairement en JSON afin de rester contrôlable et exploitable par les scripts.

Pour n'afficher que la réponse finale dans PowerShell :

```powershell
$result = openclaw agent `
  --agent chef-operations `
  --message "Explique en quelques lignes ton rôle dans OPENCLAW_LOCAL." `
  --timeout 180 `
  --json | ConvertFrom-Json

$result.final
```

### La route gouvernée recommandée

Pour passer par le routeur `OPENCLAW_LOCAL` et obtenir aussi la preuve de décision de routage :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent chef-operations `
  --message "Explique comment tu organiserais un nouveau projet DevOps." `
  --execute
```

Sans `--execute`, le script affiche la décision et la commande prévue sans lancer l'agent :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent chef-operations `
  --message "Explique comment tu organiserais un nouveau projet DevOps."
```

C'est utile pour comprendre quel modèle et quelle route seraient utilisés.

---

## 7. Quel agent choisir ?

Les identifiants doivent être utilisés exactement comme ci-dessous.

| Agent | À utiliser pour | Exemple de demande |
|---|---|---|
| `chef-operations` | cadrer, découper, organiser, coordonner | « Transforme cette demande en plan de travail avec critères de fin. » |
| `expert-recherche` | faits récents, comparaison de sources, recherche Web | « Recherche la documentation officielle actuelle et synthétise les différences. » |
| `architecte-solutions` | architecture, ADR, compromis, schémas | « Propose deux architectures et explique les compromis. » |
| `ingenieur-devops` | CI/CD, IaC, conteneurs, scripts, GitOps | « Analyse cette pipeline et propose une correction testable. » |
| `ingenieur-securite` | audit, hardening, secrets, supply-chain, risques | « Audite ce changement et liste les risques bloquants. » |
| `ingenieur-release-forges` | Git, PR, release, packaging, preuves distantes | « Prépare la stratégie de release et les checks nécessaires. » |
| `redacteur-technique` | README, procédures, runbooks, documentation | « Transforme ces notes en runbook exploitable. » |
| `auditeur-qualite` | conformité, preuves, revue indépendante | « Vérifie que le livrable répond à tous les critères annoncés. » |

### Si vous ne savez pas quel agent choisir

Commencez par :

```text
chef-operations
```

Son rôle est justement de cadrer le besoin et de répartir le travail dans un vrai projet orchestré.

---

## 8. Comment formuler une bonne demande

Une IA locale reste une IA : la qualité de la demande influence fortement la qualité du résultat.

Une bonne demande contient idéalement cinq éléments :

```text
1. objectif
2. contexte
3. contraintes
4. résultat attendu
5. méthode de validation
```

Exemple :

```text
Objectif : analyser mon pipeline GitLab.
Contexte : application Angular + Spring Boot + PostgreSQL.
Contraintes : je veux une réponse orientée Ops, sans réécrire le code métier.
Résultat attendu : liste des problèmes, corrections proposées et ordre d'application.
Validation : chaque correction doit avoir une commande ou un test de vérification.
```

Vous pouvez aussi demander explicitement :

```text
Explique d'abord ce que tu vas vérifier, puis donne la procédure, le résultat attendu et la manière de revenir en arrière si nécessaire.
```

La politique pédagogique du projet est active pour tous les agents. Le profil par défaut est `balanced` et le mode par défaut `assisted` : la livraison reste prioritaire, mais les explications utiles doivent accompagner les actions.

---

## 9. Question ponctuelle ou vrai projet ?

C'est une distinction fondamentale.

### Question ponctuelle

Utilisez un agent directement lorsque vous voulez :

- une explication ;
- une analyse limitée ;
- un diagnostic rapide ;
- une recherche ciblée ;
- tester un rôle.

Exemple :

```powershell
python .\scripts\27_route_openclaw.py `
  --agent ingenieur-devops `
  --message "Explique pourquoi ce Dockerfile est lent à construire." `
  --execute
```

### Projet orchestré

Utilisez le Project Orchestrator lorsque vous avez :

- des consignes ;
- plusieurs fichiers ;
- un dépôt source ;
- plusieurs livrables ;
- plusieurs rôles ;
- des dépendances entre tâches ;
- besoin de validation et de revue ;
- besoin de conserver les preuves et versions.

Un vrai projet doit suivre le parcours projet décrit dans la suite de ce guide.

---

## 10. Créer son premier projet

Supposons que vous ayez :

```text
C:\Travail\mon-projet\
├── consignes.pdf
├── cahier-des-charges.md
└── repository\
```

Créez le Project Intake :

```powershell
python .\scripts\28_create_project.py `
  --id mon-premier-projet `
  --title "Mon premier projet OpenClaw" `
  --intake "C:\Travail\mon-projet\consignes.pdf" `
  --intake "C:\Travail\mon-projet\cahier-des-charges.md" `
  --source "C:\Travail\mon-projet\repository" `
  --deliverable README `
  --deliverable runbook
```

Le projet central est créé sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\mon-premier-projet\
```

Sa structure ressemble à :

```text
mon-premier-projet\
├── project.json
├── intake\
├── sources\
├── context\
├── work\
├── deliverables\
├── evidence\
└── diagrams\
```

### Pourquoi `intake` et `sources` sont séparés ?

`intake` contient les consignes reçues et protégées comme référence d'origine.

`sources` contient le dépôt ou les fichiers de travail de référence.

Il ne faut pas modifier `intake` pour « corriger » une consigne : si la demande change, le changement doit être traité explicitement dans le projet.

---

## 11. Voir l'état d'un projet

À tout moment :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action status
```

Le JSON indique notamment :

- l'identifiant ;
- le titre ;
- le statut ;
- la classification ;
- la criticité ;
- les livrables attendus ;
- les clarifications bloquantes ;
- les tâches actuellement prêtes.

Cette commande est l'un des meilleurs réflexes lorsqu'un projet semble « bloqué ».

---

## 12. Lancer le projet automatiquement jusqu'au prochain gate

Lancer le parcours :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action run `
  --execute
```

Le Project Orchestrator avance automatiquement tant que les gates sont satisfaits.

Il peut s'arrêter volontairement, par exemple sur :

```text
STOP=HUMAN_CLARIFICATION_REQUIRED
```

ou :

```text
STOP=TASK_CORRECTION_REQUIRED
```

ou :

```text
STOP=VALIDATION_FAILED_TASKS_REOPENED
```

ou :

```text
STOP=REVIEW_FAILED_TASKS_REOPENED
```

ou, à la fin :

```text
STOP=HUMAN_COMPLETION_APPROVAL_REQUIRED
```

Un `STOP` n'est donc pas nécessairement une panne. C'est souvent un gate volontaire.

---

## 13. Que faire si OpenClaw demande une clarification ?

Afficher l'état :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action status
```

Repérez l'identifiant de la clarification bloquante.

Répondez explicitement :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action resolve `
  --clarification-id "<id-affiché-par-status>" `
  --answer "Votre décision ou information manquante"
```

Puis reprenez :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action run `
  --execute
```

Le système est conçu pour **demander** plutôt que d'inventer une réponse lorsqu'une ambiguïté est réellement bloquante.

---

## 14. Que se passe-t-il si une validation échoue ?

Le système ne détruit pas le travail précédent.

Une validation ou revue en échec peut rouvrir les tâches concernées et leurs dépendants.

Le projet revient alors à :

```text
IN_PROGRESS
```

Les anciennes tentatives restent conservées.

Relancez :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action run `
  --execute
```

La nouvelle tentative produit une nouvelle version au lieu d'écraser silencieusement l'ancienne.

---

## 15. Validation humaine finale

Lorsque le projet a été validé, revu et packagé, le run s'arrête sur :

```text
STOP=HUMAN_COMPLETION_APPROVAL_REQUIRED
```

Vérifiez alors les livrables et preuves.

Si vous approuvez réellement le résultat :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action complete `
  --human-approved
```

Le projet passe alors à :

```text
COMPLETE
```

Aucun agent n'a le droit de s'auto-attribuer cette validation finale.

---

## 16. Où sont les livrables ?

Le dossier principal est :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\deliverables\
```

Le travail intermédiaire se trouve sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\work\
```

Les preuves projet sont sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\evidence\
```

Les schémas sont sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\diagrams\
```

Les décisions, plans, échanges et profils de projet sont principalement sous :

```text
<OPENCLAW_LOCAL_ROOT>\projects\<project-id>\context\
```

---

## 17. Comment les agents partagent-ils le travail ?

Le projet central est la source de vérité.

Chaque agent reçoit un snapshot sous :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\<agent-id>\projects\<project-id>
```

Ces workspaces sont **reconstruisibles**. Ils ne doivent pas devenir votre source de vérité.

Après une tâche, les sorties utiles sont collectées dans le projet central et publiées dans un échange versionné.

Exemple :

```text
context\exchange\task-architecture\self\run-001\
```

Un consommateur dépendant reçoit une copie versionnée :

```text
context\exchange\task-documentation\dependencies\task-architecture\run-001\
```

Si l'architecture est corrigée, une nouvelle tentative peut produire :

```text
run-002
```

`run-001` reste conservé.

### Ce que cela signifie concrètement

Vous n'avez pas besoin d'envoyer manuellement le même fichier à tous les agents.

Le système resynchronise les tâches/agents concernés selon les dépendances du plan.

Cela ne signifie pas que huit agents réécrivent tout à chaque changement : seuls les consommateurs concernés doivent être remis à jour.

---

## 18. Quels types de fichiers peut-on fournir ?

Le parcours document gère notamment :

- PDF ;
- images ;
- DOCX ;
- PPTX ;
- XLSX ;
- Markdown et texte ;
- YAML, JSON, TOML, XML ;
- scripts et code source courants ;
- fichiers IaC et configuration supportés par la politique d'ingestion.

Les formats inconnus peuvent être inventoriés sans être interprétés automatiquement.

Un document illisible ou non couvert ne doit pas être présenté comme « lu » : le gate de couverture des sources peut bloquer l'analyse.

---

## 19. Utiliser Internet sans envoyer le raisonnement dans le cloud

Pour une information récente, utilisez principalement :

```text
expert-recherche
```

Le parcours prévu est :

```text
recherche Web
    ↓
sources récentes
    ↓
lecture/fetch
    ↓
raisonnement local
```

La simple nécessité d'une information récente ne justifie pas une escalade vers un LLM cloud.

---

## 20. Et le cloud ?

Pour une première utilisation, le conseil opérationnel est simple : **ignorez le cloud** tant que le parcours local n'est pas maîtrisé et qualifié.

Le cloud est désactivé par défaut.

Il ne peut être demandé que de façon explicite avec :

- activation locale ;
- motif autorisé ;
- préconditions ;
- budget FinOps ;
- éventuellement approbation humaine ;
- clé OpenRouter locale.

Il n'existe pas de fallback cloud silencieux destiné à cacher un modèle local en panne.

---

## 21. Comprendre les performances d'une IA locale

Les trois modèles supportés sont des modèles 24–27B. Le projet ne publie pas de promesse arbitraire de vitesse pour votre machine.

Les mesures réelles sont faites par :

```powershell
.\menu.ps1 -Action inventory
.\menu.ps1 -Action benchmark
.\menu.ps1 -Action qualification
```

La qualification compare notamment :

- temps avant le premier token ;
- débit ;
- RAM/VRAM observées ;
- stabilité ;
- contextes ;
- erreurs ;
- tool-calling ;
- comportement des backends.

Ne comparez donc pas une première réponse lente à une réponse cloud sans regarder les preuves de qualification.

---

## 22. Les logs : votre première source de diagnostic

Toute action réelle lancée via `menu.ps1` produit automatiquement un transcript dans :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\logs\
```

Lister les derniers logs :

```powershell
.\menu.ps1 -Action logs
```

Afficher les 100 dernières lignes du plus récent :

```powershell
$latest = Get-ChildItem "$env:OPENCLAW_LOCAL_ROOT\proofs\logs\*.log" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

Get-Content -LiteralPath $latest.FullName -Tail 100
```

Suivre le log pendant une action :

```powershell
Get-Content -LiteralPath $latest.FullName -Tail 50 -Wait
```

Les preuves E2E sont séparées :

```text
<OPENCLAW_LOCAL_ROOT>\proofs\openclaw_e2e_*.json
```

Les benchmarks/inventaires sont sous :

```text
<REPO>\benchmarks\results\
```

### Avant d'envoyer un log à quelqu'un

Vérifiez qu'il ne contient pas :

- clé API ;
- token ;
- secret ;
- `.env` ;
- document privé ;
- information confidentielle non nécessaire au diagnostic.

---

## 23. Les fichiers qu'il ne faut pas modifier à la main

Évitez de modifier manuellement :

```text
<OPENCLAW_LOCAL_ROOT>\workspaces\...
```

comme s'il s'agissait du projet principal.

Évitez également de modifier en place :

```text
context\exchange\...
```

Les bundles d'échange sont versionnés et hashés ; les modifier manuellement casserait la provenance.

Ne modifiez pas non plus l'`intake` immuable pour changer rétroactivement la demande initiale.

Travaillez à partir du projet central et des scripts prévus.

---

## 24. Pédagogie : vous pouvez demander des explications

La pédagogie est transversale à tous les agents et modèles.

Le profil par défaut est :

```text
balanced
```

Le mode par défaut est :

```text
assisted
```

Le principe est : produire d'abord un résultat utile, tout en expliquant ce qui aide réellement à comprendre et reproduire.

Vous pouvez écrire par exemple :

```text
Explique-moi chaque étape et le résultat attendu, mais ne ralentis pas l'exécution avec un quiz.
```

ou :

```text
Donne-moi directement la correction, puis explique pourquoi elle fonctionne.
```

ou :

```text
Je veux comprendre : explique le but avant la commande, le risque, le contrôle et le rollback.
```

Le projet autorise explicitement la solution directe sur demande ; la pédagogie ne doit pas bloquer la livraison.

---

## 25. Après un redémarrage ou une interruption

Les projets et leur état sont persistants sur disque.

Vous n'avez pas à recommencer un projet depuis zéro après avoir fermé PowerShell.

Au retour :

```powershell
cd <REPO>
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw gateway status --require-rpc --json
```

Puis pour le projet :

```powershell
python .\scripts\32_orchestrate_project.py `
  --project mon-premier-projet `
  --action status
```

Et reprenez avec `--action run --execute` lorsque l'état le permet.

---

## 26. Sauvegarde minimale à comprendre dès le début

Les données importantes sont principalement :

```text
<OPENCLAW_LOCAL_ROOT>\projects\
<OPENCLAW_LOCAL_ROOT>\state\
<OPENCLAW_LOCAL_ROOT>\proofs\
```

`runtime` et `workspaces` sont beaucoup plus facilement reconstruisibles.

Pour la procédure complète de sauvegarde/restauration, utiliser [Troubleshooting](TROUBLESHOOTING.md).

---

## 27. Diagnostic rapide : symptôme → premier réflexe

| Symptôme | Premier réflexe |
|---|---|
| `openclaw` n'est pas reconnu après la première installation | fermer puis rouvrir PowerShell, puis `audit` |
| Ollama ne répond pas | `menu.ps1 -Action configure-local` puis `verify` |
| un modèle manque | `menu.ps1 -Action models` |
| le Gateway ne répond pas | `openclaw gateway status --require-rpc --json`, puis consulter le dernier log |
| un agent échoue en E2E | ouvrir le dernier transcript + la preuve `openclaw_e2e_*.json` |
| un projet ne progresse plus | `32_orchestrate_project.py --action status` |
| statut `CLARIFICATION_REQUIRED` | répondre avec `--action resolve` |
| statut revenu à `IN_PROGRESS` après validation | les tâches en échec ont été rouvertes ; relancer `run --execute` |
| réponse locale trop lente | ne pas changer de modèle au hasard ; consulter benchmark/qualification |
| envie d'activer le cloud parce que le local échoue | diagnostiquer d'abord le défaut local |

Pour un diagnostic approfondi, utiliser [Opérations](OPERATIONS.md) puis [Troubleshooting](TROUBLESHOOTING.md).

---

## 28. Trois exercices recommandés pour la première journée

### Exercice 1 — vérifier un agent

```powershell
$result = openclaw agent `
  --agent chef-operations `
  --message "Réponds en cinq lignes : quel est ton rôle et quelles tâches dois-tu déléguer ?" `
  --timeout 180 `
  --json | ConvertFrom-Json

$result.final
```

Objectif : comprendre qu'un agent est un rôle et non un nouveau modèle.

### Exercice 2 — comparer deux rôles

Demandez la même question à :

```text
architecte-solutions
ingenieur-devops
```

Par exemple :

```text
Comment déployerais-tu une application web conteneurisée de façon fiable ?
```

Observez la différence de perspective : architecture globale d'un côté, implémentation/exploitation de l'autre.

### Exercice 3 — créer un petit projet test

Créez un dossier sans secret avec :

```text
consigne.md
sources\README.md
```

Créez ensuite un projet avec un livrable simple, inspectez `status`, lancez `run --execute`, puis regardez :

```text
projects\<id>\context
projects\<id>\work
projects\<id>\deliverables
projects\<id>\evidence
```

Objectif : comprendre le cycle de vie avant d'utiliser le système sur un projet important.

---

## 29. Glossaire minimal

### Agent

Rôle OpenClaw spécialisé avec identité, règles, outils et workspace.

### Modèle

LLM local réellement chargé par Ollama. Plusieurs agents peuvent utiliser le même modèle avec des contrats différents.

### Gateway

Service OpenClaw local permettant l'exécution configurée des agents.

### Intake

Copie protégée des consignes et entrées initiales du projet.

### Source de vérité

Le projet central sous `projects\<id>`, pas les copies des workspaces agents.

### Workspace

Espace de travail géré et reconstruisible d'un agent.

### Artifact Exchange

Mécanisme versionné qui publie et propage les sorties d'une tâche vers ses dépendants.

### Gate

Condition obligatoire avant de passer à l'étape suivante.

### Evidence / preuve

Fichier ou donnée permettant de vérifier objectivement qu'une action ou validation a eu lieu.

### Local-first

Le parcours local est nominal. Le cloud n'est jamais utilisé silencieusement pour cacher une panne locale.

### E2E

Test bout en bout : agent → OpenClaw → Gateway → modèle local → outils → résultat.

### Qualification

Mesure réelle des performances et de la stabilité de la workstation et des backends.

---

## 30. Les dix règles à retenir

1. **Vérifier avant d'utiliser** : `audit`, `verify`, Gateway.
2. **Un agent est un rôle, pas un modèle supplémentaire.**
3. **Pour une question ponctuelle, appeler un agent ; pour un vrai travail, créer un projet.**
4. **Le projet central est la source de vérité.**
5. **Ne pas travailler directement dans les snapshots agents comme source principale.**
6. **Ne pas modifier les bundles `context\exchange` en place.**
7. **Un arrêt sur clarification ou approbation humaine est souvent normal.**
8. **Lire les preuves et les logs avant de changer de configuration.**
9. **Ne jamais utiliser le cloud pour masquer un défaut local.**
10. **La fin d'un projet reste une décision humaine.**

---

## 31. Checklist « première utilisation réussie »

Vous pouvez considérer que vous avez compris le parcours de base lorsque vous savez faire sans hésiter :

```text
[ ] distinguer <REPO> de <OPENCLAW_LOCAL_ROOT>
[ ] exécuter audit et verify
[ ] vérifier le Gateway
[ ] appeler chef-operations
[ ] choisir un agent spécialisé
[ ] retrouver le dernier log
[ ] créer un Project Intake
[ ] lire le status du projet
[ ] lancer run --execute
[ ] répondre à une clarification
[ ] retrouver deliverables et evidence
[ ] comprendre que workspaces est reconstruisible
[ ] approuver humainement COMPLETE
[ ] lancer E2E
[ ] lancer la qualification matérielle
```

---

## 32. Où continuer ensuite ?

Une fois ce guide maîtrisé :

- [Installation Windows 11](INSTALLATION_WINDOWS_11.md) — installation reproductible ;
- [Opérations](OPERATIONS.md) — exploitation quotidienne ;
- [Project Intake](PROJECT_INTAKE.md) — création et intégrité des projets ;
- [Project Orchestrator](PROJECT_ORCHESTRATOR.md) — machine d'états détaillée ;
- [Intégration OpenClaw](OPENCLAW_INTEGRATION.md) — agents, workspaces, modèles et Gateway ;
- [Pédagogie](PEDAGOGY.md) — fonctionnement de l'accompagnement pédagogique ;
- [Modèles locaux](MODELES_LOCAUX.md) — flotte supportée ;
- [Qualification](QUALIFICATION.md) — validation matérielle ;
- [Troubleshooting](TROUBLESHOOTING.md) — diagnostic, backup, restore et rollback ;
- [Sécurité](SECURITY.md) — frontières de confiance et règles de sécurité.

Le portail complet reste disponible dans [docs/README.md](README.md).
