# État du projet

## Implémenté dans v0.1.0

- structure de dépôt, gouvernance et CI ;
- huit rôles et séparation producteur/auditeur ;
- catalogue local-first et politique d'escalade ;
- profil matériel Intel Arc B580 12 Go ;
- audit Windows, configuration Ollama et smoke tests ;
- benchmark reproductible et qualification versionnée ;
- validateurs de dépôt/configuration ;
- documentation d'installation, d'architecture, d'exploitation et de sécurité.

## Phase 2 — outillage de qualification

- inventaire Windows matériel/runtime sans secret ;
- suite de benchmark DevOps versionnée ;
- mesures via API native Ollama en streaming ;
- contextes requis 8K et 16K, 32K optionnel ;
- gate automatique fonctionnel/performance/contexte ;
- preuves locales JSON hors Git ;
- politique de promotion manuelle uniquement ;
- orchestrateur PowerShell de qualification complète ;
- tests unitaires du moteur d'évaluation.

## Phase 2.5 — durcissement GitHub

- PowerShell 7, PSScriptAnalyzer et Pester ;
- CodeQL et Dependency Review avec fallback `pip-audit` ;
- SemVer et workflow Release ;
- wheel, sdist et SHA-256 ;
- gouvernance versionnée ;
- badges et métadonnées documentées.

Les réglages administratifs GitHub hors Git restent vérifiés séparément via l'issue dédiée : ruleset/protection de `main`, Dependency Graph et métadonnées/topics.

## Phase 3 — runtime et intégration OpenClaw implémentés dans le dépôt

- lock runtime Windows versionné (`runtime_versions.json`) ;
- bootstrap Windows reproductible avec contrôles d'intégrité Node/OpenClaw ;
- installation complète orchestrée ;
- huit workspaces agents gérés et protégés contre l'écrasement accidentel ;
- renderer de configuration OpenClaw à partir des contrats Git ;
- Gateway local/loopback ;
- API Ollama native avec contexte conservateur 16K avant qualification ;
- outils bornés au workspace, exec soumis à approbation et elevated désactivé ;
- fallbacks OpenClaw persistants exclusivement locaux ;
- pont `clawlocal` -> références modèles/commandes OpenClaw ;
- escalade OpenRouter explicite uniquement ;
- gate E2E réel pour 8 agents, tool-calling, réparation après erreur et 3 runs ;
- coverage Python, mypy et matrice Python 3.12/3.13 ;
- SBOM CycloneDX et attestations de build pour les releases ;
- runbook de troubleshooting approfondi.

## À exécuter sur matériel réel

- installation complète sur la workstation cible ;
- E2E OpenClaw réel avec Qwen/Gemma/Ollama ;
- qualification 8K/16K sur Intel Arc B580 ;
- décision PROMOTE / KEEP_CANDIDATE / REJECT pour Qwen et Gemma ;
- SERA 14B uniquement après import/backend explicite et qualification séparée ;
- décision finale sur contextes et routes de production ;
- éventuelle stratégie cloud après mesure réelle qualité/coût.

## Non prétendu

- équivalence d'un modèle local compact avec un modèle frontier cloud ;
- tool-calling fiable tant que le gate E2E n'a pas été exécuté sur la machine cible ;
- débit garanti sur Intel Arc B580 avant benchmark réel ;
- résultat matériel inventé par la CI ;
- absence de risque d'injection de prompt en local ;
- déploiement automatique d'une clé cloud ;
- promotion automatique d'un modèle ou d'une nouvelle version runtime.
