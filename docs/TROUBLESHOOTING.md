# Troubleshooting

## Principe

Diagnostiquer `OPENCLAW_LOCAL` dans l'ordre : **code/configuration -> runtime -> modèles -> Gateway/OpenClaw -> Vulkan -> E2E -> qualification**.

Architecture V2 est **LLM local-only** : ne jamais utiliser un modèle externe pour masquer une panne locale. Si aucune route locale autorisée n'est viable, l'opération doit échouer avec une preuve exploitable.

Le choix GPU LLM est déjà fixé : **Vulkan uniquement**. Un incident GPU se diagnostique donc sur Ollama/Vulkan ou llama.cpp/Vulkan ; il ne déclenche pas une nouvelle compétition entre API.

## Flotte active de référence

```text
qwen-max          -> qwen3.5:9b-q4_K_M
gemma-deep        -> gemma4:12b-it-q4_K_M
devstral-devops   -> hf.co/mistralai/Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M
```

Challenger hors routage :

```text
granite-devops -> granite4.2:8b-q4_K_M
```

`devstral-devops` est un alias de compatibilité. Son runtime V2 est Ministral 3 14B Reasoning.

## Contextes à ne pas confondre

```text
8192  -> benchmark/HARD-40M nominal
16384 -> full-agent OpenClaw nominal
```

Les 6 cas 16K du HARD-40M restent des cas de stress du benchmark. Le full-agent OpenClaw utilise 16K comme fenêtre nominale d'orchestration afin d'absorber système, outils et réserve. **Aucune promotion à 32K n'est automatique.**

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

Si un contrôle échoue, corriger cette couche avant de lancer une qualification complète.

## 2. Mauvaise flotte après `git pull`

Symptômes :

- `ollama list` ne contient pas les trois runtimes V2 ;
- OpenClaw référence un runtime non déclaré dans le catalogue ;
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

Ne recopier jamais un ancien `qualified_model_identity.json` vers la flotte V2. Une migration de runtime impose de nouvelles preuves.

Les anciens modèles peuvent rester dans le cache Ollama tant que rien ne les route. Leur présence ne doit jamais être interprétée comme un fallback supporté.

## 3. Runtime OpenClaw inattendu

Symptôme : `configure-openclaw` ou `e2e` refuse de continuer parce que `openclaw --version` ne correspond pas au lock.

Correction :

```powershell
.\menu.ps1 -Action install-core
openclaw --version
.\menu.ps1 -Action configure-openclaw -DryRun
```

Le runtime est volontairement fail-closed. Ne modifiez pas le lock localement pour contourner le contrôle.

## 4. `context_overflow` au precheck OpenClaw

Symptôme :

```text
kind=context_overflow
message=Context overflow: prompt too large for the model (precheck).
```

Conserver le payload complet. Ne pas conclure automatiquement à un manque de contexte modèle : le problème peut venir du prompt système, des outils, d'un replay/compaction, d'une dérive de schéma ou d'une configuration provider.

Reprise :

```powershell
.\menu.ps1 -Action install-core
openclaw --version
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
```

Le patch nominal Ollama garde **16384** pour la fenêtre full-agent, tandis que le benchmark direct reste 8192.

Le renderer V2 conserve le contrat anti-injection de skills :

```text
agents.defaults.skills=[]
chaque agent.skills=[]
skills.limits.maxSkillsPromptChars=0
```

Dans les preuves `openclaw_prompt_admission_*.json`, contrôler notamment :

```text
PROMPT_ADMISSION_CONFIG_SKILL_LIMIT=0
PROMPT_ADMISSION_CONFIG_DEFAULT_SKILLS=0
PROMPT_ADMISSION_SYSTEM_CHARS=
PROMPT_ADMISSION_TOOLS_LISTCHARS=
PROMPT_ADMISSION_TOOLS_SCHEMACHARS=
PROMPT_ADMISSION_SKILLS_CHARS=0
```

Si `PROMPT_ADMISSION_SKILLS_CHARS` est non nul, la configuration nominale doit échouer. Si les skills sont à zéro mais que le precheck échoue encore sur une session fraîche, conserver le `systemPromptReport` complet avant toute modification du contexte.

Ne passer à 32K qu'après qualification dédiée et décision explicite ; jamais comme contournement automatique.

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

1. vérifier le processus Ollama ;
2. vérifier le port local ;
3. vérifier les variables d'environnement ;
4. exécuter `audit` puis `configure-local` ;
5. ne pas lancer la qualification tant que `/api/tags` ne répond pas.

## 7. Un modèle requis est absent

```powershell
ollama list
.\menu.ps1 -Action models
```

Les trois runtimes attendus sont exactement ceux du catalogue. Granite n'est requis que pour sa comparaison séparée lorsqu'elle est explicitement exécutée.

Si un téléchargement échoue, conserver l'erreur réseau/disque et corriger la cause ; ne pas modifier le catalogue pour contourner le téléchargement.

## 8. OpenClaw utilise encore un runtime non conforme

Régénérer la configuration :

```powershell
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
openclaw config validate --json
openclaw agents list --json
```

Le patch est généré depuis `config/v1/model_catalog.yaml` et `model_routing.yaml`. Ne corrigez pas manuellement `openclaw.json` comme solution durable.

OpenClaw peut persister le roster canonique sous `agents.entries` même si la surface compatible fournie est `agents.list`. Le E2E supporte les deux représentations prévues par le contrat.

## 9. Gateway indisponible

```powershell
openclaw gateway status --require-rpc --json
.\menu.ps1 -Action logs
```

Le E2E exige le transport Gateway réel. Un transport de secours non prévu n'est pas considéré comme une réussite.

## 10. VRAM inattendue

`verify` peut afficher la taille totale du modèle et la partie réellement chargée en VRAM via `/api/ps`.

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/ps
```

Sur une B580 12 Go, ne conclure ni à un full-offload ni à une panne uniquement à partir du nombre de paramètres. La résidence réelle, la RAM système et la stabilité doivent être observées.

## 11. Le spécialiste DevOps ne traite pas directement une image

C'est normal. `devstral-devops` / Ministral 3 Reasoning est text-only dans le contrat nominal.

Parcours attendu :

```text
PDF/image
 -> ingestion + Qwen/Gemma multimodal
 -> représentation textuelle + provenance
 -> handoff
 -> spécialiste DevOps
```

Ne pas ajouter artificiellement `image` au contrat du spécialiste pour contourner le workflow.

## 12. E2E agent ou tool-calling en échec

```powershell
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Vérifier :

- version OpenClaw conforme au lock ;
- modèle primaire réellement configuré ;
- provider local attendu ;
- absence de fallback transport/provider non prévu ;
- permissions du workspace ;
- disponibilité des outils requis ;
- timeout ;
- marqueur/artefact attendu réellement créé.

Une réponse textuelle « ça a marché » n'est pas une preuve si le fichier ou l'artefact attendu n'existe pas.

## 13. Backend llama.cpp/Vulkan géré ne charge pas Gemma/Ministral

```powershell
.\menu.ps1 -Action intel-vulkan-setup -DryRun
.\menu.ps1 -Action intel-vulkan-setup
.\menu.ps1 -Action intel-vulkan-verify
```

Le profil géré attend les modèles déclarés dans `runtime_versions.json` : Gemma 4 12B et Ministral 3 14B Reasoning pour le chemin Vulkan.

Vérifier dans cet ordre :

1. Intel Arc B580 détectée ;
2. pilote GPU actif ;
3. archive llama.cpp conforme au SHA-256 verrouillé ;
4. GGUF local réellement résolu ;
5. endpoint `127.0.0.1:8081/v1` joignable ;
6. processus suivi par l'état géré ;
7. absence d'un autre processus GPU consommant anormalement la VRAM ;
8. inventaire `/models?reload=1` conforme.

Le choix Vulkan est un invariant du projet. Une panne se corrige sur ce chemin au lieu de réintroduire une API GPU écartée.

## 14. Profil `b580-hybrid` incohérent

Vérifier la configuration générée plutôt que de supposer une répartition :

```powershell
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid -DryRun
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Répartition attendue :

```text
qwen-max        -> Ollama/Vulkan
gemma-deep      -> llama.cpp/Vulkan
devstral-devops -> llama.cpp/Vulkan
image/PDF       -> Ollama/Vulkan
```

Rollback immédiat :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan
.\menu.ps1 -Action intel-vulkan-stop
```

Tous les providers du profil hybride restent locaux et Vulkan.

## 15. Qualification HARD-40M échoue

La qualification reste fail-closed. **Ne modifiez ni les seuils ni le nombre de cas pour transformer un échec en succès.**

Conserver :

- transcript de qualification ;
- `benchmark_*.json` ;
- inventaire ;
- identité candidate des modèles ;
- version du pilote ;
- commit Git exact.

Classer l'échec : API/runtime, timeout, sortie tronquée, check sémantique, débit/TTFT, budget global 40 min ou dérive d'identité.

Le HARD-40M conserve 30 cas : 24 à 8K et 6 à 16K. Le full-agent OpenClaw 16K ne modifie pas ces exigences.

Ce gate modèle est distinct du choix de l'API GPU : il ne demande aucune re-comparaison entre backends.

## 16. Challenger Granite échoue

Le challenger ne doit jamais bloquer le routage nominal des trois modèles, mais une comparaison explicitement lancée doit produire un verdict exploitable.

```powershell
ollama pull granite4.2:8b-q4_K_M
.\scripts\windows\23_compare_model_challenger.ps1 -DryRun
.\scripts\windows\23_compare_model_challenger.ps1
```

Un échec du challenger signifie « aucune preuve de remplacement ». Il ne déclenche aucune promotion automatique et ne change pas `devstral-devops`.

## 17. Anciennes preuves après migration

Les preuves d'une flotte précédente restent historiques. Elles peuvent expliquer une décision de right-sizing, mais elles ne valent pas qualification V2, preuve de stabilité du runtime Vulkan actif, preuve de contexte étendu ou attestation V1.

Toute nouvelle attestation doit référencer les nouveaux digests/quantifications et le runtime réellement utilisé.

## 18. Projet bloqué

```powershell
python .\scripts\32_orchestrate_project.py --project <id> --action status
```

Vérifier phases, clarifications, tentatives, `source_coverage`, Artifact Exchange et preuves de validation. Une clarification humaine ne doit pas être contournée par une réponse inventée.

## 19. Document illisible ou ingestion incomplète

Un document `UNREADABLE`, un index périmé ou une `source_coverage` incomplète bloque l'analyse. Corriger l'ingestion ou déclarer explicitement l'information manquante.

Ne jamais présenter un PDF scanné comme « lu » si seule une extraction vide a été obtenue.

## 20. Demande cloud refusée

C'est le comportement normal d'Architecture V2. `src/clawlocal/routing.py` et `scripts/27_route_openclaw.py` conservent des paramètres historiques uniquement pour **échouer fermement** et éviter une régression silencieuse.

Aucune clé de fournisseur LLM en ligne n'est nécessaire pour l'inférence de la plateforme.

## 21. Collecter un support bundle

Utiliser les scripts de support du dépôt et joindre uniquement les preuves nécessaires après redaction des secrets. Les prompts, réponses et documents privés ne doivent pas être inclus par défaut.

## 22. Ordre de reprise recommandé

Après correction d'un incident de runtime/modèle/backend :

```powershell
.\menu.ps1 -Action install-core
.\menu.ps1 -Action configure-openclaw -DryRun
.\menu.ps1 -Action configure-openclaw
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
.\menu.ps1 -Action intel-vulkan-verify
.\menu.ps1 -Action e2e -DryRun
.\menu.ps1 -Action e2e
```

Pour le profil hybride :

```powershell
.\menu.ps1 -Action configure-openclaw -Backend b580-hybrid
.\menu.ps1 -Action e2e -Backend b580-hybrid
```

Ne relancer une qualification lourde que si le contrat de release ou une dérive d'identité l'exige. La résolution d'un incident Vulkan ne nécessite pas de rouvrir le choix de l'API GPU.
