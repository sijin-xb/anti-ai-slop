# Codes d'erreur de l'API

## Format

Toute erreur renvoie un objet JSON avec `code`, `message` et `request_id`.

| Code | HTTP | Cause |
|---|---|---|
| `AUTH_EXPIRED` | 401 | Jeton expiré, renouveler avec `POST /v1/token` |
| `RATE_LIMITED` | 429 | Quota atteint, respecter l'en-tête `Retry-After` |
| `VALIDATION` | 400 | Champ invalide, le message nomme le champ |

## Exemples

```bash
curl -s https://api.example.com/v1/items -H "Authorization: Bearer $TOKEN"
```

Une réponse 429 contient `Retry-After` en secondes ; renvoyer la requête avant ce délai
produit une nouvelle erreur 429. Le `request_id` doit accompagner tout signalement.
