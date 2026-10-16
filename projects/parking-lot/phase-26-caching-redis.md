# Phase 26 — Caching + Redis

Core rule:
```text
PostgreSQL = source of truth
Redis      = speed / temporary / derived state
```

Best first endpoint:
```text
GET /parking-lots/{lot_id}/availability
```

Use cache-aside with a deterministic versioned key and short TTL.

```text
GET /availability -> Redis HIT return
                  -> MISS -> DB -> cache -> return

POST /entry -> DB commit -> invalidate availability cache
POST /exit  -> DB commit -> invalidate availability cache
```

Other uses: rate limiting, temporary idempotency coordination, counters, short distributed coordination, Celery broker/result backend.

Do not use Redis as sole truth for spot allocation, ticket lifecycle, or payment history.
