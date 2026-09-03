# Modèles locaux

## Politique

OPENCLAW_LOCAL utilise une flotte **B580 right-sized, performance-only**. La flotte opérationnelle installée et routée contient **exactement trois modèles**, tous en Q4_K_M. Aucun petit modèle de secours ni fallback legacy caché n'est autorisé.

| Alias routé | Runtime Ollama | Taille registre indicative | Usage |
|---|---|---:|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | ~6,6 Go | orchestration, recherche, sécurité, release, raisonnement transversal, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | ~8,1 Go | architecture, rédaction, audit, contre-revue multimodale |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | ~9,0 Go | DevOps, software engineering agentique, outils dépôt, texte/code |

La source de vérité est `config/v1/model_catalog.yaml`. Le validateur CI exige que l'ensemble des alias **routés** reste exactement `{qwen-max, gemma-deep, devstral-devops}`.

L'alias `devstral-devops` est conservé pour compatibilité logique avec les routes, workspaces et états existants ; son runtime réel est désormais Qwen2.5 Coder 14B.

## Challenger obligatoire de sélection : Ministral 3 14B

La sélection finale du modèle deep ne se limite pas à Gemma. Le catalogue déclare un challenger de benchmark séparé :

```text
ministral-tool-calling -> ministral-3:14b-instruct-2512-q4_K_M
```

Ce challenger est **obligatoire avant la décision humaine de sélection du modèle deep**, principalement pour confronter Gemma 3 12B sur le **tool-calling natif** et la **réparation après retour d'outil en erreur**.

Important : Ministral ne devient pas pour autant un quatrième modèle opérationnel :

- `routing_active: false` ;
- il n'est référencé par aucun rôle ;
- il n'est pas un fallback local ;
- il ne compte pas dans `local_model_count: 3` ;
- il n'est pas inclus dans le HARD-40M des trois modèles routés ;
- son benchmark ne peut provoquer aucune promotion automatique ;
- une décision humaine explicite est obligatoire avant tout éventuel remplacement de `gemma-deep`.

Le contrat de comparaison est versionné dans `config/v1/qualification_policy.yaml` sous `model_selection_challenger`.

## Pourquoi cette architecture

La première qualification réelle de l'ancienne flotte 24–27B a montré qu'un modèle trop lourd pour les 12 Go de VRAM de la B580 pouvait perdre une part importante de son intérêt par offload CPU/GPU. La flotte 9B/12B/14B vise une zone de poids plus cohérente avec le matériel, sans fabriquer de revendication de performance avant mesure.

Le challenger Ministral répond à une autre question : **Gemma 3 12B est-il réellement le meilleur choix deep pour le workflow multi-agent lorsque le tool-calling compte ?** La réponse doit provenir d'un A/B réel sur la B580, pas d'une préférence théorique.

## Support logiciel vs qualification matérielle

Les trois modèles routés sont `required: true` parce qu'ils constituent la flotte fonctionnelle candidate. Cela ne signifie pas que leurs performances B580 sont déjà qualifiées.

Trois niveaux sont séparés :

1. **flotte opérationnelle candidate** : Qwen 3.5 9B + Gemma 3 12B + Qwen 2.5 Coder 14B ;
2. **challenger de sélection** : Ministral 3 14B, hors routage ;
3. **qualification matérielle** : TTFT, tokens/s, VRAM/RAM, stabilité, contexte, tool-calling, multimodalité et qualité réelle sur la workstation.

## Qwen 3.5 9B — `qwen-max`

`qwen3.5:9b-q4_K_M` couvre notamment :

- Chef des opérations ;
- Expert recherche ;
- Ingénieur sécurité ;
- Ingénieur Release/Forges ;
- raisonnement transversal et contre-revue lorsque Gemma produit.

Il participe également au parcours multimodal PDF/image.

## Gemma 3 12B — `gemma-deep`

`gemma3:12b-it-q4_K_M` est l'**incumbent deep** pour :

- Architecte solutions ;
- Rédacteur technique ;
- Auditeur qualité ;
- revue multimodale et documentation complexe.

Il reste candidat officiel, mais sa sélection définitive est conditionnée à la comparaison obligatoire contre Ministral sur les critères agentiques contractualisés.

## Qwen 2.5 Coder 14B — alias `devstral-devops`

`qwen2.5-coder:14b-instruct-q4_K_M` est le runtime nominal de l'Ingénieur DevOps : exploration de dépôts, édition multi-fichiers, automatisation, CI/CD, conteneurs, Kubernetes, IaC et scripts.

Dans le contrat OPENCLAW_LOCAL, il reste **text-only**. Lorsqu'une tâche dépend d'une image ou d'un PDF, Qwen 3.5 ou Gemma 3 réalise la lecture multimodale puis transmet un handoff traçable au spécialiste.

## Routage nominal

```text
Chef opérations       -> Qwen 3.5 9B
Expert recherche      -> Qwen 3.5 9B + Web
Architecte solutions  -> Gemma 3 12B
Ingénieur DevOps      -> Qwen 2.5 Coder 14B
Ingénieur sécurité    -> Qwen 3.5 9B
Release/Forges        -> Qwen 3.5 9B
Rédacteur technique   -> Gemma 3 12B
Auditeur qualité      -> Gemma 3 12B
                         -> Qwen 3.5 9B si producteur Gemma
```

Ministral n'apparaît pas dans ce routage tant qu'une preuve comparative et une décision humaine n'ont pas conduit à modifier le catalogue dans une PR dédiée.

## Politique de contexte

La cible nominale reste **8192 tokens** pour les trois modèles routés. Le contexte **16384** reste un stress de qualification HARD-40M.

La comparaison Gemma/Ministral est volontairement effectuée à **8192 tokens**, à charge comparable au nominal B580.

## Benchmark challenger Gemma vs Ministral

Installation explicite du challenger si nécessaire :

```powershell
ollama pull ministral-3:14b-instruct-2512-q4_K_M
```

Le dépôt ne télécharge pas ce modèle silencieusement pendant le benchmark.

Dry-run :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
```

Comparaison réelle :

```powershell
.\scripts\windows\23_compare_model_challenger.ps1
```

Contrat par défaut :

- Gemma 3 12B vs Ministral 3 14B ;
- Q4_K_M ;
- contexte 8192 ;
- 3 répétitions ;
- appel d'outil natif `read_file` ;
- retour contrôlé `file_not_found` ;
- réparation attendue via `list_files` ;
- mesure du taux de tool-intent et de réparation ;
- wall time, tokens/s et résidence VRAM lorsque disponibles ;
- aucune promotion automatique.

La preuve est écrite sous :

```text
benchmarks/results/tool_calling_challenger_*.json
```

Le contenu brut des réponses n'est pas persisté dans cette preuve ; le runner conserve une empreinte et les appels d'outils structurés utiles à l'audit.

## HARD-40M

Le HARD-40M continue d'exiger exactement :

```text
qwen-max
gemma-deep
devstral-devops
```

Si l'un de ces trois modèles échoue, la qualification de la flotte échoue. Le challenger Ministral constitue une **preuve de sélection séparée** ; il ne permet pas de contourner l'échec d'un des trois modèles actifs.

## Backends

Le modèle et le backend restent découplés. La V0.2 compare notamment Ollama/Vulkan, llama.cpp/SYCL, llama.cpp/Vulkan et le profil candidat `b580-hybrid`. Aucun backend ni modèle n'est auto-promu.

## Gate anti-régression

`scripts/45_validate_model_fleet.py` vérifie notamment :

- exactement trois modèles locaux routés ;
- les trois runtime IDs Q4_K_M attendus ;
- contexte nominal 8192 ;
- aucun retour des runtimes legacy ;
- qualification obligatoire des trois modèles ;
- indépendance Gemma/Qwen de l'Auditeur ;
- challenger Ministral exact et séparé du routage ;
- comparaison tool-calling/réparation obligatoire ;
- `automatic_promotion: false` et décision humaine obligatoire.
