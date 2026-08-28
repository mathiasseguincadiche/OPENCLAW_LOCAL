# Préparer une release

## Agent principal

`ingenieur-release-forges`.

## Prérequis

Livrables validés, tests `PASS`, version cible, changelog, état Git propre et règles de publication connues.

## Étapes

1. vérifier ce qui entre dans la release ;
2. contrôler version et changelog ;
3. générer package et hashes ;
4. vérifier CI et règles de branche ;
5. préparer PR/MR si nécessaire ;
6. obtenir les approbations ;
7. publier ;
8. revalider depuis le distant ;
9. conserver les preuves.

La publication est un workflow distinct de la simple réussite locale.