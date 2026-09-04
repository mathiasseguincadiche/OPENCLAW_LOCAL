# Troubleshooting

## Principe

Diagnostiquer `OPENCLAW_LOCAL` dans l'ordre : **code/configuration → runtime → modèles → Gateway/OpenClaw → backend GPU → E2E → qualification**. Ne jamais activer le cloud pour masquer une panne locale.

## Flotte active de référence

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma3:12b-it-q4_K_M
devstral-devops   -> qwen2.5-coder:14b-instruct-q4_K_M
```

Le nom `devstral-devops` est un alias de compatibilité. Le runtime réel est Qwen 2.5 Coder 14B.

Le **benchmark direct B580** reste nominal à **8192 tokens**. Le **full-agent OpenClaw nominal** est configuré à **16384 tokens** pour l'orchestration ; cette valeur ne constitue pas une promotion du benchmark 16K. Un éventuel essai OpenClaw 32K reste un candidat matériel séparé et ne doit pas être activé sans preuve B580.

Le runtime OpenClaw supporté est **2026.9.1**. Après un `git pull` qui modifie `runtime_versions.json`, exécuter `install-core` avant de reconfigurer OpenClaw.

## 1. Vérification minimale

Depuis la racine du dépôt :

```powershell
.\menu.ps1 -Action logs
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
openclaw --version
openclaw config validate --json
openclaw agents list --json
openclaw gateway status --require-rpc --json
```

Si un de ces contrôles échoue, corriger cette couche avant de lancer une qualification complète.

## 2. Mauvaise flotte après `git pull`

Symptômes :

- `ollama list` montre seulement les anciens 24–27B ;
- OpenClaw référence un ancien runtime ;
- `verify` signale un modèle requis absent ;
- le fingerprint qualifié est `INVALIDATED`.

Correction :

```powershell
.\menu.ps1 -Action models -DryRun
.\menu.ps1 -Action models
.\menu.ps1 -Action install-core
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Ne recopier jamais un ancien `qualified_model_identity.json` vers la nouvelle flotte. Une migration de runtime impose de nouvelles preuves.

Les anciens modèles peuvent être supprimés ultérieurement avec les outils Ollama après vérification que rien ne les référence encore. La migration ne doit pas détruire automatiquement des preuves ou artefacts historiques.

## 3. Runtime OpenClaw inattendu

Symptôme : `configure-openclaw` ou `e2e` refuse de continuer parce que `openclaw --version` ne correspond pas au lock.

Correction :

```powershell
.\menu.ps1 -Action install-core
openclaw --version
.\menu.ps1 -Action configure-openclaw -DryRun
```

Le runtime est volontairement fail-closed. Ne modifier pas le lock localement pour contourner le contrôle.

## 4. `context_overflow` au precheck OpenClaw

Symptôme :

```text
kind=context_overflow
message=Context overflow: prompt too large for the model (precheck).
```

OpenClaw 2026.9.1 ne doit plus rejeter un tour uniquement parce que son estimation conservative de pression pré-prompt ordinaire dépasse le budget : cette estimation est diagnostique. Un `context_overflow (precheck)` reste toutefois possible lorsqu'un checkpoint canonique de replay/compaction ne tient réellement pas dans la fenêtre active. Il faut donc conserver la preuve au lieu d'assimiler automatiquement l'erreur à un défaut du modèle.

Reprise :

```powershell
.\menu.ps1 -Action install-core
openclaw --version
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Attendu : `openclaw --version` contient `2026.9.1`.

Le patch nominal Ollama garde **16384** pour `contextWindow`, `contextTokens` et `num_ctx`, tout en conservant le benchmark direct à 8192. Il ne réactive pas les anciens overrides `reserveTokens`/`reserveTokensFloor`.

Le renderer final force également `skills: []` pour les huit agents nominaux. Quand `configure-openclaw` échoue, vérifier les preuves `openclaw_prompt_admission_*.json` et les lignes :

```text
PROMPT_ADMISSION_SYSTEM_CHARS=
PROMPT_ADMISSION_TOOLS_LISTCHARS=
PROMPT_ADMISSION_TOOLS_SCHEMACHARS=
PROMPT_ADMISSION_SKILLS_CHARS=
```

`PROMPT_ADMISSION_SKILLS_CHARS` doit rester à zéro sur le chemin nominal géré. Si 16K échoue encore sur une session fraîche sous 2026.9.1, conserver le payload complet : il devient une preuve exploitable pour distinguer replay/compaction, schéma, provider et pression mémoire réelle.

Ne passer à 32K qu'après un PASS 16K propre et comme **qualification d'orchestration B580 séparée**, jamais comme contournement automatique.

## 5. `OLLAMA_MODELS` pointe au mauvais endroit

Afficher :

```powershell
$env:OPENCLAW_LOCAL_ROOT
$env:OLLAMA_MODELS
```

Le stockage géré attendu est :

```text
<OPENCLAW_LOCAL_ROOT>\models\ollama
```

Reconfigurer :

```powershell
.\menu.ps1 -Action configure-local
```

Puis rouvrir PowerShell si une variable utilisateur vient d'être modifiée.

## 6. Ollama n'est pas joignable

Tester le loopback :

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Si l'API échoue :

1. vérifier que le processus Ollama existe ;
2. vérifier le port local ;
3. vérifier les variables d'environnement ;
4. exécuter `audit` puis `configure-local` ;
5. ne pas lancer la qualification tant que `/api/tags` ne répond pas.

## 7. Un modèle requis est absent

```powershell
ollama list
.\menu.ps1 -Action models
```

Les trois runtimes attendus sont exactement ceux du catalogue. Aucun quatrième fallback local n'est requis.

Si `ollama pull` échoue, conserver l'erreur réseau/disque et corriger la cause ; ne pas modifier le catalogue pour contourner le téléchargement.

## 8. OpenClaw utilise encore un ancien modèle

Régénérer la configuration :

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
openclaw config validate --json
openclaw agents list --json
```

Le patch est généré depuis `config/v1/model_catalog.yaml` et `model_routing.yaml`. Ne pas corriger manuellement `openclaw.json` comme solution durable.

OpenClaw 2026.9.x peut persister le roster canonique sous `agents.entries` même si le patch est fourni via `agents.list`. Le E2E supporte les deux représentations.

## 9. Gateway indisponible

```powershell
openclaw gateway status --require-rpc --json
```

Puis examiner :

```powershell
.\menu.ps1 -Action logs
```

Le E2E exige le transport Gateway réel. Un fallback vers un transport embedded n'est pas considéré comme une réussite.

## 10. `verify` répond mais la VRAM semble étrange

`verify` peut afficher la taille totale du modèle et la partie réellement chargée en VRAM via `/api/ps`.

Sur la B580 12 Go, ne conclure ni à un full-offload ni à une panne uniquement à partir du nombre de paramètres. Vérifier la mesure effective :

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/ps
```

L'objectif de la nouvelle flotte Q4_K_M est de réduire la pression mémoire observée avec les anciens 24–27B. Cette amélioration doit néanmoins être mesurée, pas supposée.

## 11. Le spécialiste DevOps ne traite pas directement une image

C'est normal. `devstral-devops` / Qwen 2.5 Coder 14B est text-only.

Le parcours attendu est :

```text
PDF/image
 -> ingestion + Qwen/Gemma multimodal
 -> représentation textuelle/provenance
 -> handoff
 -> spécialiste DevOps
```

Si une tâche demande au spécialiste d'interpréter directement une image, corriger le workflow plutôt que d'ajouter artificiellement `image` à son contrat.

## 12. E2E agent ou tool-calling en échec

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Le script écrit un diagnostic JSON dans `proofs` lorsqu'un payload applicatif est incohérent.

Vérifier :

- version OpenClaw conforme au lock ;
- modèle primaire réellement configuré ;
- provider attendu ;
- absence de fallback transport/provider ;
- permissions du workspace ;
- disponibilité de `write/read` ou du mécanisme de découverte d'outils ;
- timeout de l'appel ;
- contenu exact du marqueur attendu.

Ne considérer aucune réponse textuelle « ça a marché » comme preuve si le fichier ou l'artefact attendu n'existe pas réellement.

## 13. Backend SYCL ne charge pas un modèle

Prévisualiser puis installer :

```powershell
.\menu.ps1 -Action intel-sycl-setup -DryRun
.\menu.ps1 -Action intel-sycl-setup
.\menu.ps1 -Action intel-sycl-verify
```

Pour isoler un modèle :

```powershell
.\menu.ps1 -Action intel-sycl-diagnose -Model qwen3.5:9b-q4_K_M
```

ou :

```powershell
.\menu.ps1 -Action intel-sycl-diagnose -Model gemma3:12b-it-q4_K_M
.\menu.ps1 -Action intel-sycl-diagnose -Model qwen2.5-coder:14b-instruct-q4_K_M
```

Le diagnostic distingue notamment full-offload, auto-offload et CPU-only. Conserver stdout/stderr et le JSON de preuve.

## 14. Backend Vulkan géré ne charge pas Gemma/Qwen Coder

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

Le profil géré attend exactement les deux modèles textuels routés vers Vulkan dans `runtime_versions.json`.

Avant Vulkan, le serveur SYCL suivi est arrêté pour éviter une contention de VRAM. Si un autre processus GPU consomme la mémoire, l'identifier avant de conclure à un défaut du modèle.

## 15. Profil hybride incohérent

Routage attendu :

```text
qwen-max        -> ollama/qwen3.5:9b-q4_K_M
gemma-deep      -> intel-vulkan/gemma3:12b-it-q4_K_M
devstral-devops -> intel-vulkan/qwen2.5-coder:14b-instruct-q4_K_M
```

Vérifier :

```powershell
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Rollback immédiat :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
```

## 16. Qualification HARD-40M échoue

La qualification reste fail-closed. Ne modifier ni les seuils ni le nombre de cas pour transformer un échec en succès.

Conserver :

- transcript de qualification ;
- `benchmark_*.json` ;
- inventaire ;
- identité candidate des modèles ;
- version du pilote ;
- commit Git exact.

Classer l'échec :

- API/runtime ;
- timeout individuel ;
- sortie tronquée ;
- check sémantique ;
- débit/TTFT ;
- budget global 40 min ;
- dérive d'identité.

Le 16K HARD-40M reste un **stress qualifiant du benchmark**. Le fait qu'OpenClaw utilise 16K pour son orchestration ne transforme pas ce stress en promotion de performance, et un résultat HARD-40M 16K ne doit pas être falsifié pour justifier un changement de contexte runtime.

## 17. Qwen native thinking atteint la limite

Les trois probes Qwen natifs restent bornés à 1024 tokens dans le protocole actif. Atteindre la borne reste une troncature et un échec.

Si cela arrive avec la nouvelle flotte, inspecter la sortie, `done_reason`, `eval_count`, temps mural et volume de thinking. Ne relever pas automatiquement la limite sans diagnostic et justification.

## 18. Anciennes preuves après migration

Les preuves produites avec les anciens modèles 24–27B sont conservées comme historique de la décision de right-sizing. Elles peuvent expliquer pourquoi la flotte a changé, mais elles ne valent pas :

- qualification des nouveaux modèles ;
- promotion du backend hybride ;
- preuve de contexte 16K ;
- attestation V1.

Toute nouvelle attestation doit référencer les nouveaux digests/quantifications.

## 19. Projet bloqué

Afficher l'état :

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

Vérifier les phases, clarifications, tentatives, `source_coverage`, Artifact Exchange et preuves de validation. Une clarification humaine ne doit pas être contournée par une réponse inventée.

## 20. Document illisible ou ingestion incomplète

Un document `UNREADABLE`, un index périmé ou une `source_coverage` incomplète bloque l'analyse. Corriger l'ingestion ou déclarer explicitement l'information manquante.

Ne jamais présenter un PDF scanné comme « lu » si seule une extraction vide a été obtenue.

## 21. Cloud refusé

Un refus est normal si une précondition manque. Vérifier :

- `OPENCLAW_LOCAL_CLOUD_ENABLED` ;
- motif versionné ;
- rôle autorisé ;
- tentative Web locale si requise ;
- budget ;
- approbation humaine si requise ;
- clé locale disponible.

Le cloud n'est pas un mécanisme de haute disponibilité automatique.

## 22. Collecter un support bundle

Utiliser les scripts de support du dépôt et joindre uniquement les preuves nécessaires après redaction des secrets. Les prompts, réponses et documents privés ne doivent pas être inclus par défaut.

## 23. Ordre de reprise recommandé

Après correction d'un incident de runtime/modèle/backend :

```powershell
.\menu.ps1 -Action install-core
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action e2e -DryRun
```

Puis lancer le E2E réel uniquement si tous ces prérequis sont sains :

```powershell
.\menu.ps1 -Action e2e
```

Puis seulement si le runtime est sain :

```powershell
.\menu.ps1 -Action qualification -DryRun
.\menu.ps1 -Action qualification
```

Une qualification réussie conduit au maximum au verdict automatique prévu par le contrat ; V1 reste soumise aux autres preuves et à l'approbation humaine.
