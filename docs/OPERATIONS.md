# Opérations

## Routine

```powershell
.\menu.ps1 -Action audit
.\menu.ps1 -Action verify
```

Après changement de modèle ou de pilote GPU :

```powershell
.\menu.ps1 -Action benchmark
```

## Diagnostic

1. vérifier que le modèle est réellement installé ;
2. vérifier qu'Ollama répond en loopback ;
3. exécuter un smoke test sans outils ;
4. tester le tool-calling OpenClaw ;
5. comparer au dernier benchmark ;
6. seulement ensuite considérer une escalade cloud.

Ne masquez jamais un défaut local par un fallback cloud automatique pendant un diagnostic.
