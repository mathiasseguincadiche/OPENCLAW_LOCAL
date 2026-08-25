# Installation Windows 11

## Préconditions

- Windows 11 Pro x64 ;
- PowerShell 7 ;
- Python 3.12+ ;
- OpenClaw installé selon sa documentation ;
- pilotes GPU à jour ;
- Ollama installé nativement sous Windows.

## Parcours

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action configure-local -DryRun
.\menu.ps1 -Action configure-local
.\menu.ps1 -Action models
.\menu.ps1 -Action verify
```

Le backend Ollama de référence écoute sur `http://127.0.0.1:11434`. Ne l'exposez pas sur le LAN sans besoin explicite, authentification/filtrage adapté et revue de sécurité.

## OpenClaw

Le projet utilise l'intégration native Ollama d'OpenClaw. Le provider local doit utiliser l'URL native Ollama sans suffixe `/v1` afin de conserver le tool-calling attendu.

L'installation n'ajoute jamais de clé cloud. Le cloud reste optionnel et séparé.
