# Modèles locaux

## Politique

OPENCLAW_LOCAL utilise une flotte **B580 right-sized, performance-only**. La présence d'un modèle dans le catalogue signifie qu'il est pris en charge par la plateforme ; il n'existe pas de petit modèle de secours ni de candidat legacy caché.

La flotte locale supportée contient exactement trois modèles, tous quantifiés en **Q4_K_M** :

| Alias | Runtime Ollama | Taille registre indicative | Usage |
|---|---|---:|---|
| `qwen-max` | `qwen3.5:9b-q4_K_M` | ~6,6 Go | orchestration, recherche, sécurité, release, raisonnement transversal, multimodal |
| `gemma-deep` | `gemma3:12b-it-q4_K_M` | ~8,1 Go | architecture, rédaction, audit, contre-revue multimodale |
| `devstral-devops` | `qwen2.5-coder:14b-instruct-q4_K_M` | ~9,0 Go | DevOps, software engineering agentique, outils dépôt, texte/code |

La source de vérité opérationnelle est `config/v1/model_catalog.yaml`. Le validateur CI exige que l'ensemble des alias locaux soit **exactement** `{qwen-max, gemma-deep, devstral-devops}`.

L'alias `devstral-devops` est volontairement conservé comme **alias logique de compatibilité** : il évite de casser les routes, workspaces et états déjà créés, mais son runtime n'est plus Devstral ; c'est Qwen2.5 Coder 14B.

## Pourquoi cette flotte

La première qualification réelle de l'ancienne flotte 24–27B a montré qu'un modèle d'environ 18 Go ne pouvait pas résider entièrement dans les 12 Go de VRAM de la B580 et tombait autour de 4 tok/s avec offload CPU/GPU. La nouvelle flotte vise donc une zone de poids beaucoup plus cohérente avec 12 Go de VRAM, sans prétendre qu'une résidence complète ou un débit précis sont acquis avant mesure.

Le redimensionnement ne modifie pas les huit rôles et ne relâche pas les gates de qualification. Le but est d'obtenir davantage de travail réellement accéléré sur GPU, pas de fabriquer un PASS.

## Support logiciel vs qualification matérielle

Les trois modèles sont `required: true` parce qu'ils constituent la flotte fonctionnelle choisie. Cela ne signifie pas qu'une performance B580 a déjà été mesurée.

Deux affirmations sont donc séparées :

1. **support logiciel** : les trois modèles sont installés, exposés à OpenClaw et utilisés par le routeur ;
2. **qualification matérielle** : TTFT, tokens/s, VRAM/RAM, stabilité, contexte, tool-calling et qualité multimodale sont mesurés sur la workstation réelle.

Aucun benchmark public ne remplace la seconde étape.

## Qwen 3.5 9B Q4_K_M — `qwen-max`

`qwen3.5:9b-q4_K_M` est le modèle généraliste de performance pour :

- Chef des opérations ;
- Expert recherche, associé aux outils Web ;
- Ingénieur sécurité ;
- Ingénieur Release/Forges ;
- raisonnement transversal ou contre-revue lorsque la famille Gemma a produit le livrable.

Il sert aussi de modèle multimodal par défaut pour `imageModel` et `pdfModel`, avec Gemma 3 12B en fallback local.

## Gemma 3 12B Q4_K_M — `gemma-deep`

`gemma3:12b-it-q4_K_M` est utilisé pour :

- Architecte solutions ;
- Rédacteur technique ;
- Auditeur qualité ;
- revue multimodale et documentation complexe.

L'Auditeur bascule vers la famille Qwen lorsque le producteur est Gemma afin de préserver l'indépendance de famille lorsque cela est praticable.

## Qwen 2.5 Coder 14B Q4_K_M — alias `devstral-devops`

`qwen2.5-coder:14b-instruct-q4_K_M` est le runtime nominal de l'Ingénieur DevOps. Il est destiné à :

- exploration de dépôts ;
- édition multi-fichiers ;
- automatisation ;
- CI/CD ;
- conteneurs, Kubernetes et IaC ;
- utilisation d'outils agentiques ;
- scripts Bash/PowerShell/Python et configuration technique.

Ce modèle est **text-only dans le contrat OPENCLAW_LOCAL**. Lorsqu'une tâche DevOps dépend d'une image ou d'un PDF, Qwen 3.5 ou Gemma 3 réalise la lecture multimodale et transmet le contexte/provenance au spécialiste DevOps.

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

Les fallbacks locaux d'un rôle sont eux aussi limités à ces trois modèles. Une indisponibilité locale ne déclenche jamais automatiquement le cloud.

## Multimodalité

La couche Document Ingestion utilise :

- `pdf` pour les PDF ;
- `view_image` pour les images ;
- extraction locale déterministe pour DOCX/PPTX/XLSX ;
- `source_coverage[]` pour rendre explicite ce qui a réellement été lu.

Qwen 3.5 9B et Gemma 3 12B sont les modèles du parcours PDF/image OpenClaw. Qwen2.5 Coder reste un spécialiste texte/code et reçoit un handoff multimodal traçable lorsque nécessaire.

## Politique de contexte

La cible nominale est **8192 tokens** pour les trois modèles et les routeurs gérés. Le contexte **16384** reste volontairement présent dans la matrice de qualification afin de mesurer l'impact réel sur la B580.

Les fenêtres maximales annoncées par les familles de modèles ne sont pas utilisées automatiquement. Toute augmentation du contexte nominal exige des preuves de KV-cache, VRAM/RAM, TTFT, débit et stabilité.

## Qualification obligatoire des trois modèles

La commande nominale est :

```powershell
.\scripts\windows\03_pull_models.ps1
.\scripts\windows\07_run_qualification.ps1
```

Le gate automatique exige les trois alias :

```text
qwen-max
gemma-deep
devstral-devops
```

Si l'un des trois échoue, la qualification de la flotte échoue. Il n'existe aucun candidat local optionnel dont l'échec serait ignoré.

La réussite automatique conduit au maximum à `READY_FOR_MANUAL_QUALIFICATION`. Une revue humaine et les E2E réels restent requis avant toute affirmation matérielle.

## Backends

Le modèle et le backend restent découplés. La V0.2 compare :

- Ollama/Vulkan ;
- llama.cpp/SYCL ;
- llama.cpp/Vulkan ;
- le profil candidat `b580-hybrid`.

Voir `docs/RUNTIME_BACKENDS.md`.

## Gate anti-régression

`scripts/45_validate_model_fleet.py` vérifie notamment :

- exactement trois modèles locaux ;
- les trois runtime IDs attendus ;
- quantification Q4_K_M ;
- poids de registre borné pour le profil B580 ;
- contexte nominal 8192 ;
- `required: true` pour chacun ;
- aucun alias local hors flotte dans le routage ;
- aucune réapparition des anciens runtimes 24–27B dans les surfaces actives ;
- qualification obligatoire des trois modèles ;
- indépendance Gemma/Qwen de l'Auditeur ;
- configuration OpenClaw multimodale alignée ;
- handoff multimodal explicite vers le spécialiste DevOps text-only.

Ce gate est exécuté dans CI et Release.
