# Parcours de lecture

Ce document répond à une question simple : **que dois-je lire ou exécuter maintenant, selon mon rôle et mon objectif ?**

Il ne remplace pas les documents techniques. Il sert de **carte de navigation** entre découverte, exploitation et expertise.

## Choisir son profil

| Profil | Objectif | Commencer ici | Résultat attendu |
|---|---|---|---|
| Débutant | comprendre le projet sans connaissances préalables | [Premiers pas](PREMIERS_PAS_OPENCLAW_LOCAL.md) | savoir ce qu'est OPENCLAW_LOCAL, reconnaître ses composants et exécuter les premiers contrôles sans deviner la suite |
| Opérateur | installer, vérifier, exploiter et dépanner | [Opérations](OPERATIONS.md) puis [Guide utilisateur](GUIDE_UTILISATEUR/README.md) | savoir quelle commande lancer, ce qui doit réussir, quand s'arrêter et où chercher une preuve |
| Mainteneur | modifier le dépôt sans casser les contrats | [Architecture](ARCHITECTURE.md), [Sécurité](SECURITY.md), [Gouvernance GitHub](GITHUB_GOVERNANCE.md) | comprendre les invariants, les gates CI et les responsabilités avant de changer le code ou la configuration |
| Expert / auditeur | retrouver immédiatement contrats, qualification et preuves | [Portail documentaire](README.md), [Qualification](QUALIFICATION.md), [État du projet](../STATUS.md) | identifier le contrat applicable, distinguer preuve et hypothèse, vérifier la readiness sans interprétation implicite |

## Règle commune de lecture

Chaque parcours suit le même contrat :

```text
PRÉREQUIS
   ↓
ACTION OU LECTURE
   ↓
RÉSULTAT ATTENDU
   ↓
VALIDATION / PREUVE
   ↓
GO → étape suivante
STOP → diagnostic / correction avant de continuer
```

Ne continuez pas sur une étape critique si son résultat attendu n'est pas obtenu.

## Parcours A — Débutant

### Prérequis

- savoir ouvrir PowerShell 7 ;
- savoir naviguer dans un répertoire ;
- disposer du dépôt local ou pouvoir consulter GitHub ;
- ne pas avoir besoin de connaître OpenClaw, Ollama ou llama.cpp au départ.

### Étapes

1. Lire [Premiers pas](PREMIERS_PAS_OPENCLAW_LOCAL.md).
2. Lire le niveau 1 du [portail documentaire](README.md).
3. Utiliser le [guide utilisateur](GUIDE_UTILISATEUR/README.md) pour choisir un besoin concret.
4. En cas de blocage, aller directement dans `GUIDE_UTILISATEUR/07_DIAGNOSTIC/` au lieu d'improviser.

### Résultat attendu

Vous devez pouvoir expliquer :

- ce que fait la plateforme ;
- pourquoi les LLM restent locaux ;
- la différence entre un agent direct et un projet orchestré ;
- où trouver les commandes opérateur ;
- où trouver le diagnostic si une étape échoue.

### Critère STOP

Si vous ne savez pas encore quelle commande ou quel document utiliser pour votre prochain objectif, revenez au [guide utilisateur](GUIDE_UTILISATEUR/README.md) et choisissez le chemin par besoin.

### À lire ensuite

- pour travailler : [Guide utilisateur](GUIDE_UTILISATEUR/README.md) ;
- pour installer : [Installation Windows 11](INSTALLATION_WINDOWS_11.md) ;
- pour comprendre l'architecture : [Architecture](ARCHITECTURE.md).

## Parcours B — Opérateur

### Prérequis

- Windows 11 Pro x64 ;
- PowerShell 7+ ;
- dépôt synchronisé ;
- droits et accès nécessaires à l'installation locale ;
- connaissance de l'emplacement du runtime géré.

### Séquence nominale

```powershell
git checkout main
git pull

.\menu.ps1 -Action install-full -DryRun
.\menu.ps1 -Action install-full

.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Pour la B580 hybride Vulkan :

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify

.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid

.\menu.ps1 -Action e2e -Backend b580-hybrid -DryRun
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

### Résultat attendu

L'opérateur doit obtenir des contrôles explicites sur :

- runtime et versions ;
- services locaux ;
- modèles requis ;
- huit agents ;
- routage local-only ;
- chemin Vulkan ;
- E2E et preuves associées.

### Critère STOP

**Arrêter la progression** dès qu'une commande retourne FAIL, NON CONFORME ou qu'une preuve attendue manque. Ne pas compenser un échec par un contournement non documenté.

### Diagnostic

1. Lire [Troubleshooting](TROUBLESHOOTING.md).
2. Utiliser `GUIDE_UTILISATEUR/07_DIAGNOSTIC/`.
3. Consulter les logs et preuves avant de relancer.
4. Utiliser le rollback documenté lorsque le scénario le prévoit.

### À lire ensuite

- exploitation quotidienne : [Opérations](OPERATIONS.md) ;
- B580 : [Intel Arc B580](INTEL_ARC_B580.md) ;
- backends : [Backends locaux](RUNTIME_BACKENDS.md) ;
- qualification : [Qualification](QUALIFICATION.md).

## Parcours C — Mainteneur

### Prérequis

- comprendre Git et les pull requests ;
- lire les contrats avant de modifier leur implémentation ;
- considérer les validateurs CI comme des invariants, pas comme des obstacles à contourner.

### Ordre de lecture recommandé

1. [Architecture](ARCHITECTURE.md)
2. [Sécurité](SECURITY.md)
3. [Project Orchestrator](PROJECT_ORCHESTRATOR.md)
4. [Backends locaux](RUNTIME_BACKENDS.md)
5. [Intégration OpenClaw](OPENCLAW_INTEGRATION.md)
6. [Gouvernance GitHub](GITHUB_GOVERNANCE.md)
7. [ADR](ADR/README.md)

### Résultat attendu

Avant toute modification structurante, le mainteneur doit pouvoir répondre :

- quel contrat est modifié ;
- quel comportement observable doit rester inchangé ;
- quel test ou validateur prouve la conformité ;
- quel rollback existe ;
- quelle documentation doit évoluer avec le code.

### Critère STOP

Ne pas fusionner un changement si le code, les configs, les docs et les gates racontent des architectures différentes.

### À lire ensuite

- pour une release : [Gouvernance GitHub](GITHUB_GOVERNANCE.md) ;
- pour les limites actuelles : [État du projet](../STATUS.md) ;
- pour la readiness : [Qualification](QUALIFICATION.md).

## Parcours D — Expert / auditeur

### Point d'entrée rapide

| Question | Référence |
|---|---|
| Quelle architecture est supportée ? | [Architecture](ARCHITECTURE.md) |
| Quels runtimes sont autorisés ? | [Backends locaux](RUNTIME_BACKENDS.md) |
| Quels modèles sont routés ? | [Modèles locaux](MODELES_LOCAUX.md) |
| Quelles frontières de sécurité ? | [Sécurité](SECURITY.md) |
| Comment le projet passe ses états ? | [Project Orchestrator](PROJECT_ORCHESTRATOR.md) |
| Qu'est-ce qui prouve la qualification ? | [Qualification](QUALIFICATION.md) |
| Le projet est-il V1-ready ? | `config/v1/release_readiness.yaml` et [État du projet](../STATUS.md) |
| Quelles décisions sont historiques ? | [ADR](ADR/README.md) |

### Contrat preuve / état / hypothèse

Un expert doit distinguer immédiatement :

- **contrat** : comportement exigé par config, code, policy ou gate ;
- **état observé** : résultat d'un contrôle ou d'une exécution ;
- **preuve** : artefact vérifiable associé à cet état ;
- **hypothèse** : élément non encore prouvé, qui ne doit pas devenir une readiness implicite.

### Critère STOP

Si une affirmation de readiness n'a pas de preuve réelle associée, elle reste non approuvée. La CI ne remplace pas la qualification matérielle de la workstation.

### À lire ensuite

- [Qualification](QUALIFICATION.md) ;
- [Benchmark](BENCHMARK.md) ;
- [Télémétrie](TELEMETRY.md) ;
- [État du projet](../STATUS.md).

## Contrat de navigation documentaire

Le portail documentaire est considéré conforme uniquement si :

1. les profils Débutant, Opérateur, Mainteneur et Expert / auditeur possèdent chacun un point d'entrée ;
2. chaque parcours indique des prérequis, un résultat attendu, un critère STOP et une suite ;
3. les liens relatifs essentiels du portail pointent vers des fichiers existants ;
4. le CI et le workflow de release exécutent le validateur documentaire ;
5. la distinction découverte / exploitation / maintenance / audit reste explicite.

Le gate associé est `scripts/48_validate_documentation_portal.py`.
