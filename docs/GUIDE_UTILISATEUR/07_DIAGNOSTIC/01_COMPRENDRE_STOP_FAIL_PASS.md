# Comprendre STOP, FAIL et PASS

## PASS

Le contrôle exécuté a satisfait son critère.

## FAIL

Le contrôle a été exécuté et a échoué. Lire la preuve avant de relancer.

## STOP

Le workflow s'arrête volontairement parce qu'une condition externe est requise : clarification humaine, correction, review ou approbation finale.

## Méthode

1. identifier le type ;
2. lire le message complet ;
3. trouver la preuve associée ;
4. agir sur la cause ;
5. reprendre à l'étape prévue.

Ne traitez pas `CLARIFICATION_REQUIRED` comme une panne et ne traitez pas un `FAIL` comme une simple demande de confirmation.