# Chargement de la configuration

Le programme lit ses réglages dans `config.toml`. Si un champ obligatoire manque, il s'arrête avec le code 2.

## Ordre de recherche

1. Le chemin donné par l'option `--config`.
2. La variable d'environnement `APP_CONFIG`.
3. Le fichier `config.toml` du répertoire courant.

Une étape ne s'applique que si la précédente n'a rien trouvé. Les fichiers ne sont pas fusionnés.

## Comportement en cas d'échec

| Cas | Comportement |
|---|---|
| Fichier absent | Démarrage avec les valeurs intégrées |
| Erreur de syntaxe | Refus de démarrer, numéro de ligne affiché |
| Valeur hors limites | Refus de démarrer, champ et plage affichés |

Les numéros de ligne commencent à 1 et comptent les commentaires.
Le message d'erreur cite le texte exact : « Valeur invalide. Voir la plage. »
