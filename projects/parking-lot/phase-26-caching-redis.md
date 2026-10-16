# Phase 26 — Caching & Redis

## Core rule

For this Parking Lot:

~~~text
PostgreSQL = durable source of truth
Redis      = fast temporary/derived/shared state
~~~

Redis should solve a concrete latency/throughput/coordination problem, not replace relational correctness.

## Best first Redis endpoint

~~~text
GET /parking-lots/{lot_id}/availability
~~~

Why?

- read-heavy
- aggregation may be repeated frequently
- a few seconds of staleness may be acceptable
- actual allocation will still revalidate in PostgreSQL

Example response:

~~~json
{
  "bike": 20,
  "compact": 15,
  "large": 4
}
~~~

## Cache-aside

~~~text
Client
  ↓
GET /availability
  ↓
Redis
  |  | HIT -> return cached result
  |
  MISS
   ↓
PostgreSQL aggregation
   ↓
store Redis with TTL
   ↓
return
~~~

Example:

~~~python
def get_availability(lot_id):
    key = (
        f"parking:v1:"
        f"lot:{lot_id}:"
        f"availability"
    )

    cached = redis.get(key)

    if cached is not None:
        return json.loads(cached)

    data = query_availability_from_db(
        lot_id
    )

    redis.setex(
        key,
        30,
        json.dumps(data),
    )

    return data
~~~

## TTL

TTL = Time To Live.

~~~python
redis.setex(
    key,
    30,
    value,
)
~~~

After 30 seconds the key expires.

TTL bounds how long stale derived data can survive.

## Cache invalidation

Entry changes availability.

~~~text
POST /entry
   ↓
PostgreSQL transaction
   ↓
COMMIT
   ↓
delete availability cache
~~~

Exit similarly invalidates after successful committed release.

Django:

~~~python
transaction.on_commit(
    lambda: redis.delete(
        f"parking:v1:lot:{lot_id}:availability"
    )
)
~~~

Why after commit? If transaction rolls back, the authoritative data did not change.

## Invalidation failure

Even on_commit is not perfectly reliable:

~~~text
DB commit succeeds
process crashes before Redis delete
~~~

Therefore short TTL is still valuable.

For highly reliable cross-system side effects, outbox/event-driven invalidation can be considered.

## Do not allocate from Redis cache

Bad:

~~~text
Redis says A101 free
→ blindly assign A101
~~~

Cache may be stale.

Actual write path should still use PostgreSQL transaction/locking:

~~~sql
SELECT ...
FOR UPDATE SKIP LOCKED;
~~~

So:

~~~text
Redis availability = read optimization / hint
PostgreSQL allocation = correctness
~~~

## Endpoint relationship

~~~text
GET  /parking-lots/{id}/availability
    -> Redis first

POST /parking-lots/{id}/entry
    -> PostgreSQL authoritative write
    -> invalidate availability cache

POST /parking-lots/{id}/exit
    -> PostgreSQL/payment authoritative flow
    -> invalidate availability cache
~~~

## Cache key design

Prefer deterministic namespaced/versioned keys:

~~~text
parking:v1:lot:1:availability
~~~

If response varies by floor/type, key must include those dimensions.

Version prefix makes future cache-shape changes easier.

## Cache granularity

Choices:

~~~text
whole lot
per floor
per spot type
~~~

Fine-grained keys improve targeted invalidation but increase complexity/key count.

Start simple.

## Redis Hash

Availability can be represented as a hash:

~~~text
HSET parking:lot:1:availability
    bike 120
    compact 55
    large 10
~~~

Useful for grouped values/counters.

## Idempotency coordination

For:

~~~text
POST /parking/exit
Idempotency-Key: abc123
~~~

Redis can quickly coordinate temporary processing:

~~~python
created = redis.set(
    "idempotency:exit:abc123",
    "processing",
    nx=True,
    ex=60,
)
~~~

NX = set only if key does not already exist.

But for financial correctness, Redis should not be the only protection. Use durable DB idempotency/uniqueness too.

## Rate limiting

Redis atomic counters are a good fit.

~~~python
key = f"rate:{user_id}:{minute}"

count = redis.incr(key)

if count == 1:
    redis.expire(key, 60)

if count > 100:
    raise RateLimitExceeded()
~~~

Response may be HTTP 429.

## Distributed locks

Redis locks can coordinate distributed processes such as:

~~~text
only one worker generates the daily report
~~~

But do not replace PostgreSQL row locks for DB row ownership when the protected resource itself lives in PostgreSQL.

Rule:

~~~text
DB lock -> protect DB transactional state
Redis lock -> distributed coordination
~~~

## Temporary counters

Redis is good for high-frequency, non-authoritative counters:

~~~text
cars entered today
dashboard metrics
~~~

If the number is financial/audit-critical, derive/store durable facts elsewhere.

## Cache stampede

If a popular key expires, thousands of requests may simultaneously miss and hit the DB.

Mitigations:

- single-flight/refresh lock
- stale-while-revalidate
- background refresh
- TTL jitter

## TTL jitter

Instead of every key expiring at exactly 300 sec:

~~~text
TTL = 300 + random(0..60)
~~~

This spreads expirations.

## Negative caching

Repeated request for nonexistent lot can hit DB every time.

Cache NOT_FOUND briefly:

~~~text
parking:lot:999999 = NOT_FOUND
TTL = 30
~~~

## Hot key

A single highly popular key may become a hotspot.

Only at large scale consider:

- splitting by floor/type
- local cache
- replicas
- sharded counters

Do not prematurely optimize.

## Local cache vs Redis

Local memory:
- fastest
- no network
- per-process only
- lost on restart
- hard cross-server invalidation

Redis:
- shared across app instances
- network hop
- central temporary state

## Useful Redis structures

SDE1 familiarity:

- String
- Hash
- List
- Set
- Sorted Set
- Streams

For this project:

- String → JSON cache/idempotency result
- Hash → availability counters
- Sorted Set → queues/rankings only if requirement appears
- Streams → possible event pipeline, but do not add when Celery/outbox already solves the need

## Redis + Celery

A common Django setup:

~~~text
Django
  ↓ enqueue
Redis broker
  ↓
Celery Worker
~~~

Example:

~~~python
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
~~~

This Redis role is message transport/result storage, not cache.

## Failure behavior

For ordinary cache:

~~~text
Redis down
→ fallback to PostgreSQL
→ system slower but correct
~~~

For security/rate limiting, fail-open vs fail-closed needs an explicit policy.

## Cache hit ratio

Measure:

~~~text
hits / total lookups
~~~

If hit ratio is tiny, cache may not be worth its complexity.

Also monitor:

- misses
- evictions
- memory
- Redis latency
- connections
- hot keys
- rate-limit rejects
- idempotency conflicts

## What Redis is for in our final Parking Lot

Initially:

1. availability read cache
2. rate limiting
3. temporary idempotency coordination
4. Celery broker later

Not as sole truth for:

- spot ownership
- ticket lifecycle
- payment truth
- payment history
- authoritative availability

## Interview answer

A strong summary:

> PostgreSQL remains the source of truth for spot allocation, tickets and payments because those require transactions and strong consistency. Redis is useful for high-read availability caching, rate limiting, short-lived idempotency coordination and background-task messaging. The availability cache can use cache-aside with a short TTL and invalidation after committed entry/exit transactions, while the actual spot assignment is still revalidated transactionally in PostgreSQL.
