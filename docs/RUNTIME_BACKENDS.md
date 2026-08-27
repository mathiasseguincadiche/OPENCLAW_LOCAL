# Backends d'inférence locale

## Objectif

La V0.2 ne lie pas définitivement la plateforme à un seul backend GPU. Le contrat `config/v1/runtime_backends.yaml` décrit les backends locaux à comparer sur la workstation Windows 11 + Intel Arc B580.

## Backends V0.2

| ID | Provider | Accélération | Statut |
|---|---|---|---|
| `ollama-vulkan` | Ollama | Vulkan | nominal, qualification requise |
| `llama-cpp-sycl` | llama.cpp | SYCL | candidat |
| `llama-cpp-vulkan` | llama.cpp | Vulkan | candidat |

Le mot **nominal** signifie « chemin d'installation V0.2 », pas « vainqueur de performance ». Aucun backend n'est promu sur la seule base d'une documentation ou d'un benchmark externe.

## Règles de qualification

La comparaison Intel Arc doit mesurer, lorsque possible avec le même modèle et la même quantification :

- TTFT ;
- tokens/seconde ;
- VRAM ;
- RAM ;
- stabilité ;
- tool calling OpenClaw ;
- erreurs ou sorties corrompues ;
- comportement aux contextes 8K/16K et éventuellement 32K.

Le contrat `qualification_policy.yaml` impose `automatic_winner_promotion: false`.

## Ollama/Vulkan

Ollama reste le chemin nominal car il simplifie :

- téléchargement et inventaire des modèles ;
- API locale ;
- intégration OpenClaw ;
- gestion quotidienne.

L'API doit rester liée à `127.0.0.1` et ne doit pas être exposée au LAN par défaut.

## llama.cpp/SYCL et Vulkan

Les variantes llama.cpp restent des candidats de qualification afin de déterminer si la B580 obtient un meilleur compromis débit/latence/VRAM que le parcours Ollama.

La V0.2 n'installe pas silencieusement un backend candidat et ne route pas vers lui sans import, configuration et preuve E2E.

## LOCAL_FAST et LOCAL_DEEP

Le backend et la classe de modèle sont deux notions différentes :

```text
Modèle
  ├── LOCAL_FAST
  └── LOCAL_DEEP

Backend
  ├── Ollama/Vulkan
  ├── llama.cpp/SYCL
  └── llama.cpp/Vulkan
```

Un changement de backend ne doit pas imposer de réécrire les rôles OpenClaw ni les politiques d'escalade.

## Preuve matérielle obligatoire

Les performances B580 ne sont pas stockées comme vérités dans Git tant qu'elles n'ont pas été mesurées sur la machine cible. Les rapports locaux restent sous l'état runtime/proofs et ne deviennent publiables qu'après revue et redaction.
