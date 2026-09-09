# Parcours de lecture unique

OPENCLAW_LOCAL suit une règle simple : **une seule documentation, un seul parcours, compréhensible par tout le monde**.

Le lecteur ne choisit pas une zone selon son niveau. Il suit le même ordre, depuis les bases jusqu'aux contrats, aux preuves et au diagnostic. La profondeur technique augmente progressivement sans changer de parcours.

## Règle de progression

Chaque étape suit le même contrat :

```text
COMPRENDRE
   ↓
PRÉREQUIS
   ↓
FAIRE / LIRE
   ↓
RÉSULTAT ATTENDU
   ↓
VALIDER / TROUVER LA PREUVE
   ↓
GO → continuer
STOP → diagnostiquer puis reprendre
   ↓
APPROFONDIR
```

Personne n'est supposé connaître OpenClaw, Ollama, llama.cpp, Vulkan, les agents ou les contrats du dépôt avant de commencer.

## Étape 1 — Comprendre ce qu'est le projet

### Lire

1. [Premiers pas avec OPENCLAW_LOCAL](PREMIERS_PAS_OPENCLAW_LOCAL.md)
2. [Portail documentaire](README.md)
3. [Guide utilisateur](GUIDE_UTILISATEUR/README.md)

### Résultat attendu

À ce stade, le lecteur doit pouvoir expliquer avec ses mots :

- ce que fait OPENCLAW_LOCAL ;
- pourquoi le raisonnement LLM reste local ;
- ce qu'est un agent ;
- la différence entre une tâche directe et un projet orchestré ;
- où trouver les commandes ;
- où aller lorsqu'une étape échoue.

### STOP

Si ces notions restent floues, ne pas sauter vers les fichiers de configuration ou les contrats internes. Reprendre les Premiers pas puis le Guide utilisateur.

### Ensuite

Continuer vers l'installation et les contrôles de base.

## Étape 2 — Installer et vérifier la plateforme

### Prérequis

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- Git ;
- dépôt local synchronisé ;
- accès nécessaire au bootstrap initial.

### Lire avant d'exécuter

- [Installation Windows 11](INSTALLATION_WINDOWS_11.md)
- [Opérations](OPERATIONS.md)

### Exécuter

```powershell
git checkout main
git pull

.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full

.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

### Résultat attendu

Les contrôles doivent confirmer le runtime attendu, les services locaux, les modèles requis, les agents et l'absence de route LLM cloud.

### STOP

Arrêter si une commande retourne `FAIL`, `NON CONFORME`, si une preuve obligatoire manque ou si l'état observé ne correspond pas au résultat attendu.

### Ensuite

Passer à [Troubleshooting](TROUBLESHOOTING.md) en cas d'échec ; sinon continuer vers l'utilisation quotidienne.

## Étape 3 — Utiliser OPENCLAW_LOCAL pour un vrai travail

### Lire

1. [Méthode générale de travail](GUIDE_UTILISATEUR/01_METHODE_DE_TRAVAIL/00_METHODE_GENERALE.md)
2. [Choisir un agent](GUIDE_UTILISATEUR/02_AGENTS/README.md)
3. [Parcours pratiques](GUIDE_UTILISATEUR/03_PARCOURS_PRATIQUES/)

### Comprendre le cycle

```text
DÉFINIR le résultat
→ PRÉPARER les entrées
→ CHOISIR agent direct ou projet orchestré
→ ANALYSER
→ CLARIFIER si nécessaire
→ PLANIFIER + ASSIGNER
→ EXÉCUTER
→ VALIDER
→ REVIEW
→ PACKAGE
→ APPROBATION humaine
```

### Résultat attendu

Le lecteur doit savoir lancer une tâche concrète, suivre son avancement, retrouver le résultat produit et identifier la preuve qui permet de le valider.

### STOP

Ne jamais contourner silencieusement un état bloquant. Utiliser [Diagnostic](GUIDE_UTILISATEUR/07_DIAGNOSTIC/) puis reprendre à l'étape documentée.

### Ensuite

Continuer vers le fonctionnement interne du projet.

## Étape 4 — Comprendre comment le système fonctionne

Lire dans cet ordre :

1. [Architecture](ARCHITECTURE.md)
2. [Project Intake](PROJECT_INTAKE.md)
3. [Intégrité Intake](INTAKE_INTEGRITY.md)
4. [Project Orchestrator](PROJECT_ORCHESTRATOR.md)
5. [Intégration OpenClaw](OPENCLAW_INTEGRATION.md)
6. [Modèles locaux](MODELES_LOCAUX.md)
7. [Backends locaux](RUNTIME_BACKENDS.md)
8. [Routage hybride](ROUTAGE_HYBRIDE.md)
9. [Intel Arc B580](INTEL_ARC_B580.md)
10. [Sécurité](SECURITY.md)

### Résultat attendu

Le lecteur doit progressivement comprendre :

- comment une entrée devient un projet ;
- comment les huit rôles interviennent ;
- comment les modèles sont routés ;
- pourquoi Vulkan est le seul chemin GPU LLM actif sur la B580 ;
- où sont les frontières de sécurité ;
- comment les artefacts et preuves circulent.

### Ensuite

Continuer vers les contrats, la qualité et les preuves.

## Étape 5 — Comprendre les contrats et la qualité

Lire :

1. [Accessibilité](ACCESSIBILITY.md)
2. [Pédagogie](PEDAGOGY.md)
3. [Gouvernance GitHub](GITHUB_GOVERNANCE.md)
4. [ADR](ADR/README.md)
5. [État du projet](../STATUS.md)

Puis consulter les validateurs sous `scripts/` et les tests sous `tests/` lorsqu'un document renvoie vers un contrat précis.

### Résultat attendu

Le lecteur doit pouvoir distinguer :

- **contrat** : ce que le système exige ;
- **état observé** : ce qu'une exécution a réellement produit ;
- **preuve** : l'artefact vérifiable associé ;
- **hypothèse** : ce qui n'est pas encore démontré.

Il doit également comprendre qu'une CI verte ne remplace pas une qualification matérielle réelle.

### Ensuite

Continuer vers la qualification et la readiness.

## Étape 6 — Comprendre la qualification et la readiness

Lire dans cet ordre :

1. [Qualification](QUALIFICATION.md)
2. [Benchmark](BENCHMARK.md)
3. [Télémétrie](TELEMETRY.md)
4. [État du projet](../STATUS.md)
5. `config/v1/release_readiness.yaml`

### Résultat attendu

Le lecteur doit pouvoir répondre :

- quelles preuves sont attendues ;
- quelles preuves existent réellement ;
- quelles limites restent ouvertes ;
- pourquoi une release peut rester fail-closed ;
- ce qui exige encore une validation humaine.

### STOP

Aucune affirmation de readiness ne doit être déduite d'une documentation complète ou d'une CI verte seule.

## Étape 7 — Diagnostiquer, maintenir et faire évoluer

À ce stade, le lecteur possède déjà le contexte nécessaire. Il peut approfondir selon le problème rencontré sans changer de documentation ni entrer dans une zone réservée.

Références principales :

- [Troubleshooting](TROUBLESHOOTING.md)
- [Opérations](OPERATIONS.md)
- [Gouvernance GitHub](GITHUB_GOVERNANCE.md)
- [Sécurité](SECURITY.md)
- [Architecture](ARCHITECTURE.md)
- [ADR](ADR/README.md)

### Règle de modification

Avant une modification structurante, pouvoir répondre :

1. quel contrat est affecté ;
2. quel comportement observable doit rester cohérent ;
3. quel test ou validateur le prouve ;
4. quel rollback existe ;
5. quelle documentation doit évoluer avec le code.

## Contrat de navigation documentaire

Le portail est conforme uniquement si :

1. il existe **un seul parcours principal** ;
2. ce parcours commence sans connaissance implicite et augmente progressivement en profondeur ;
3. aucun contenu n'est réservé à un niveau de compétence ;
4. les étapes indiquent prérequis, résultat attendu, STOP/GO et suite quand cela est pertinent ;
5. les liens essentiels pointent vers des fichiers existants ;
6. le CI et le workflow de release exécutent le validateur documentaire ;
7. la documentation permet à une personne qui part de zéro d'aller progressivement jusqu'aux contrats, preuves, opérations et mécanismes DevOps du projet.

Le gate associé est `scripts/48_validate_documentation_portal.py`.
