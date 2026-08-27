# Modèles locaux

## Politique

OPENCLAW_LOCAL utilise une flotte **performance-only**. La présence d'un modèle dans le catalogue signifie qu'il est pris en charge par la plateforme ; il n'existe pas de petit modèle de secours ni de candidat legacy caché.

La flotte locale supportée contient exactement trois modèles :

| Alias | Runtime Ollama | Classe | Usage |
|---|---|---|---|
| `qwen-max` | `qwen3.8:27b` | LOCAL_MAX | orchestration, recherche, sécurité, release, raisonnement transversal |
| `gemma-deep` | `gemma4:26b` | LOCAL_DEEP | architecture, rédaction, audit, contre-revue multimodale |
| `devstral-devops` | `devstral-small-2:24b` | LOCAL_SPECIALIST | DevOps, software engineering agentique, outils dépôt |

La source de vérité opérationnelle est `config/v1/model_catalog.yaml`. Le validateur CI exige que l'ensemble des alias locaux soit **exactement** `{qwen-max, gemma-deep, devstral-devops}`.

## Support logiciel vs qualification matérielle

Les trois modèles sont `required: true` parce qu'ils constituent la flotte fonctionnelle choisie. Cela ne signifie pas qu'une performance B580 a déjà été mesurée.

Deux affirmations sont donc séparées :

1. **support logiciel** : les trois modèles sont installés, exposés à OpenClaw et utilisés par le routeur ;
2. **qualification matérielle** : TTFT, tokens/s, VRAM/RAM, stabilité, contexte, tool-calling et qualité multimodale sont mesurés sur la workstation réelle.

Aucun benchmark public ne remplace la seconde étape.

## Qwen 3.8 27B — LOCAL_MAX

`qwen3.8:27b` est le modèle généraliste de performance pour :

- Chef des opérations ;
- Expert recherche, associé aux outils Web ;
- Ingénieur sécurité ;
- Ingénieur Release/Forges ;
- raisonnement transversal ou contre-revue lorsque la famille Gemma a produit le livrable.

Il sert aussi de modèle multimodal par défaut pour `imageModel` et `pdfModel`, avec Gemma 4 26B en fallback local.

## Gemma 4 26B — LOCAL_DEEP

`gemma4:26b` est utilisé pour :

- Architecte solutions ;
- Rédacteur technique ;
- Auditeur qualité ;
- revue multimodale et documentation complexe.

L'Auditeur bascule vers la famille Qwen lorsque le producteur est Gemma afin de préserver l'indépendance de famille lorsque cela est praticable.

## Devstral Small 2 24B — LOCAL_SPECIALIST

`devstral-small-2:24b` est le modèle nominal de l'Ingénieur DevOps. Il est destiné à :

- exploration de dépôts ;
- édition multi-fichiers ;
- automatisation ;
- CI/CD ;
- conteneurs, Kubernetes et IaC ;
- utilisation d'outils agentiques.

Il est également déclaré multimodal selon les capacités exposées par le runtime Ollama ; la qualité réelle de vision reste à valider E2E sur la workstation.

## Routage nominal

```text
Chef opérations       -> Qwen 3.8 27B
Expert recherche      -> Qwen 3.8 27B + Web
Architecte solutions  -> Gemma 4 26B
Ingénieur DevOps      -> Devstral Small 2 24B
Ingénieur sécurité    -> Qwen 3.8 27B
Release/Forges        -> Qwen 3.8 27B
Rédacteur technique   -> Gemma 4 26B
Auditeur qualité      -> Gemma 4 26B
                         -> Qwen 3.8 27B si producteur Gemma
```

Les fallbacks locaux d'un rôle sont eux aussi limités à ces trois modèles. Une indisponibilité locale ne déclenche jamais automatiquement le cloud.

## Multimodalité

La couche Document Ingestion utilise :

- `pdf` pour les PDF ;
- `view_image` pour les images ;
- extraction locale déterministe pour DOCX/PPTX/XLSX ;
- `source_coverage[]` pour rendre explicite ce qui a réellement été lu.

Qwen 3.8 27B et Gemma 4 26B sont les modèles par défaut du parcours PDF/image OpenClaw. Devstral peut traiter les documents utiles au DevOps, mais l'original reste immuable et la provenance reste conservée.

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
- llama.cpp/Vulkan.

Voir `docs/RUNTIME_BACKENDS.md`.

## Contexte

Les fenêtres maximales annoncées par les modèles ne sont pas utilisées automatiquement. OPENCLAW_LOCAL conserve un contexte opérationnel prudent et l'augmente uniquement après mesure de l'impact KV-cache, VRAM/RAM, TTFT et débit.

## Gate anti-régression

`scripts/45_validate_model_fleet.py` vérifie notamment :

- exactement trois modèles locaux ;
- les trois runtime IDs attendus ;
- `required: true` pour chacun ;
- aucun alias local hors flotte dans le routage ;
- aucune réapparition des anciens runtimes dans les surfaces actives ;
- qualification obligatoire des trois modèles ;
- indépendance Gemma/Qwen de l'Auditeur ;
- configuration OpenClaw multimodale alignée.

Ce gate est exécuté dans CI et Release.
