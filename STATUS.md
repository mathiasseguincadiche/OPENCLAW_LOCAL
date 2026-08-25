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

## Candidat / à qualifier sur matériel réel

- Qwen 3.5 9B comme généraliste local ;
- Gemma 4 12B comme seconde famille locale ;
- SERA 14B comme spécialiste code/DevOps optionnel ;
- tailles de contexte optimales ;
- performances Vulkan/SYCL selon moteur réellement retenu ;
- stratégie d'escalade cloud après mesure de qualité/coût.

## Non prétendu

- équivalence d'un modèle local 9B/12B avec un modèle frontier cloud ;
- tool-calling fiable pour tout modèle/quantification ;
- débit garanti sur toute carte Intel Arc B580 ;
- absence de risque d'injection de prompt en local ;
- déploiement automatique d'une clé cloud.
