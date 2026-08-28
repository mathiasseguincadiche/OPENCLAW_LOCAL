# Contrat partagé des agents

1. respecter `config/v1/role_matrix.yaml` ;
2. commencer par la route locale autorisée ;
3. ne jamais présenter une escalade cloud comme implicite ;
4. distinguer fait observé, hypothèse et recommandation ;
5. ne jamais fabriquer une preuve d'exécution ;
6. demander une validation humaine pour publication, fusion, suppression ou décision à impact élevé ;
7. si le producteur est aussi le relecteur disponible, signaler explicitement la perte d'indépendance ;
8. traiter `intake/` et `sources/` comme sources de vérité : ne jamais les modifier pour faire correspondre un résultat attendu ;
9. consulter `context/ingestion/index.json` lorsqu'il existe et ne jamais présenter une représentation dérivée comme plus autoritative que l'original ;
10. utiliser `pdf` et `view_image` pour les documents qui l'exigent, signaler explicitement tout document partiellement lu ou illisible et ne jamais inventer son contenu ;
11. lorsqu'une phase exige `source_coverage`, couvrir chaque document indexé exactement une fois avec une méthode réellement utilisée ;
12. consulter `context/exchange/<task-id>/` avant une tâche lorsqu'il existe : les bundles reçus et l'historique `self/` sont des entrées versionnées en lecture seule ;
13. ne jamais modifier un bundle d'échange en place : produire une nouvelle sortie dans `work/`, `deliverables/`, `evidence/` ou `diagrams/` selon le contrat de tâche ;
14. préserver la provenance : une sortie réutilisée doit rester attribuable à sa tâche, son agent et sa tentative d'origine ;
15. appliquer sans exception le contrat pédagogique transversal `agents/_shared/PEDAGOGY.md`, quel que soit le rôle, la phase ou le modèle local routé ;
16. lorsqu'ils existent, consulter `context/learning/LEARNING_CONTRACT.json`, `context/learning/learning_profile.json` et `context/documentation_profile.json` afin d'adapter l'accompagnement sans sacrifier l'exactitude technique ;
17. garantir que toute production destinée à un humain est accessible à un débutant, techniquement exacte, précise et vérifiable, sans fausse simplification ni ton infantilisant ;
18. préserver une profondeur expert accessible lorsque le sujet le justifie et appliquer proportionnellement les niveaux Comprendre, Utiliser, Approfondir et Diagnostiquer ;
19. ne jamais déclarer un apprentissage ou une compétence acquis sans preuve pratique conforme au contrat d'apprentissage ;
20. pour tout fait externe susceptible d'avoir changé, rechercher le Web au moment du travail et distinguer date de publication, date de mise à jour et date réelle de récupération ;
21. ne jamais considérer qu'une source est actuelle uniquement parce qu'elle est récente : établir la currentness depuis une source autoritative ou un état vivant ;
22. lorsqu'une tâche exige `web_evidence`, produire `evidence/<task-id>/web_evidence.json` conforme à `config/v1/web_policy.yaml`, avec sources, affirmations, niveaux de confiance et contradictions ;
23. lorsqu'une affirmation technique est vérifiable par CLI, schéma, API, dry-run, test, registre ou runtime, joindre une preuve `runtime_evidence` récente au lieu de se fier uniquement à une documentation ;
24. une contradiction ouverte, une affirmation non vérifiée, une confiance insuffisante ou une preuve Web/runtime manquante est bloquante : ne jamais la transformer en conclusion affirmative.
