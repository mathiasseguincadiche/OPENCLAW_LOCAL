# État du projet

## Implémenté dans v0.1.0

- structure de dépôt, gouvernance et CI ;
- huit rôles et séparation producteur/auditeur ;
- catalogue local-first et politique d'escalade ;
- profil matériel Intel Arc B580 12 Go ;
- audit Windows sans mutation ;
- préparation Ollama, téléchargement contrôlé et smoke test local ;
- benchmark simple reproductible ;
- validateurs de dépôt/configuration ;
- documentation d'installation, d'architecture, d'exploitation et de sécurité.

## Phase 2 — outillage de qualification implémenté

- inventaire Windows matériel/runtime sans secret ;
- suite de benchmark DevOps versionnée ;
- mesures via API native Ollama en streaming ;
- contextes requis 8K et 16K, 32K optionnel ;
- gate automatique fonctionnel/performance/contexte ;
- preuve locale JSON hors Git ;
- politique de promotion manuelle uniquement ;
- orchestrateur PowerShell de qualification complète ;
- tests unitaires du moteur d'évaluation.

## Candidat / à exécuter sur matériel réel

- Qwen 3.5 9B comme généraliste local ;
- Gemma 4 comme seconde famille locale ;
- SERA 14B comme spécialiste code/DevOps optionnel ;
- qualification réelle 8K/16K sur Intel Arc B580 ;
- tool-calling réel via OpenClaw ;
- correction après retour d'outil ;
- trois exécutions stables ;
- décision finale sur les contextes et routes de production ;
- stratégie d'escalade cloud après mesure de qualité/coût.

## Non prétendu

- équivalence d'un modèle local 9B/12B avec un modèle frontier cloud ;
- tool-calling fiable pour tout modèle/quantification ;
- débit garanti sur toute carte Intel Arc B580 ;
- résultat de benchmark tant que la suite n'a pas été exécutée sur la workstation ;
- absence de risque d'injection de prompt en local ;
- déploiement automatique d'une clé cloud.
