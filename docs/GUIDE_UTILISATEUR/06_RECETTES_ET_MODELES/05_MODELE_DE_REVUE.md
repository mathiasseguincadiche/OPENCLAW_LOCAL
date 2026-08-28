# Modèle de revue

```text
OBJET À REVOIR
<livrable / changement / package>

SOURCES DE VÉRITÉ
- <consignes>
- <plan>
- <critères>

PREUVES FOURNIES
- <tests/logs/hashes>

CONTRÔLE DEMANDÉ
Pour chaque critère : PASS, FAIL ou PREUVE MANQUANTE.
Ne corrige pas silencieusement le livrable.
Liste les écarts, leur impact, la tâche responsable et le contrôle à rejouer après correction.
```

Agent recommandé : `auditeur-qualite`, avec `ingenieur-securite` pour les critères sécurité.