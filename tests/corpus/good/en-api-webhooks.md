# API Reference: Webhooks

## `POST /v1/webhooks`

Subscribe an HTTPS endpoint to event types.

### Request

| Field | Type | Required | Default |
|---|---|---|---|
| `url` | string | yes | — |
| `events` | array of string | yes | — |
| `secret` | string | no | generated |
| `enabled` | boolean | no | `true` |

`url` must use HTTPS and resolve to a public address. Requests to private
ranges are rejected with `400 private_address`.

Supported events are `item.created`, `item.updated`, `item.deleted`, and
`ping`. An empty `events` array is rejected; omit the field's value rather than
sending an empty list if no events are wanted at creation time.

### Response `201`

```json
{
  "id": "wh_01HZX3K9",
  "url": "https://example.com/hook",
  "events": ["item.created"],
  "secret": "whsec_...",
  "enabled": true,
  "created_at": "2026-11-15T12:00:00Z"
}
```

The `secret` field is returned only in the creation response. It is not
retrievable afterwards.

### Errors

| Status | Code | Condition |
|---|---|---|
| 400 | `invalid_url` | URL is not HTTPS or is malformed |
| 400 | `private_address` | URL resolves to a private range |
| 409 | `duplicate_url` | an enabled webhook already uses this URL |

## Delivery

Each delivery carries an `X-Signature` header: the hex HMAC-SHA256 of the raw
request body using `secret`. Retries occur at 1, 5, 30 minutes and 2, 6, 24
hours. After the seventh failure the webhook is disabled and a
`webhook.disabled` event is sent to the account owner.

Delivery is at-least-once. Receivers must deduplicate on the `X-Delivery-Id`
header, which is stable across retries.
