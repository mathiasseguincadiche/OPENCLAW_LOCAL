# Corriger un problème

## Méthode de diagnostic

1. reproduire le symptôme ;
2. conserver le log/erreur exact ;
3. identifier la couche concernée ;
4. formuler une hypothèse testable ;
5. effectuer le test le moins destructif ;
6. corriger la cause, pas seulement le symptôme ;
7. rejouer le contrôle qui échouait ;
8. exécuter les contrôles de régression ;
9. documenter la preuve.

## Choisir l'agent

Infra/runtime → DevOps ; schéma/architecture → Architecte + DevOps ; sécurité → Sécurité ; incohérence de résultat → Auditeur.

Ne relancez pas en boucle une installation ou un workflow sans lire le `FAIL` et le transcript.