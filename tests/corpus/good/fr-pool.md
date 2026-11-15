# Pool de connexions

Le pool ouvre les connexions à la demande. Si aucune connexion n'est libre, l'appelant attend
ou en crée une nouvelle, tant que `max_size` n'est pas atteint.

Quand le pool est plein, `acquire_timeout` fixe la durée d'attente. La valeur par défaut est de
5 secondes. Avec 0, chaque acquisition en conflit échoue aussitôt.

Les connexions inactives sont fermées après `idle_timeout`. Le nettoyage s'exécute une fois par
minute : une connexion peut donc rester ouverte jusqu'à 60 secondes de plus.

Depuis la version 2.1.0, `max_size` vaut 25 au lieu de 10. Les déploiements qui reposaient sur
l'ancienne valeur doivent la fixer explicitement.

```toml
[pool]
max_size = 10
acquire_timeout = 5
```
