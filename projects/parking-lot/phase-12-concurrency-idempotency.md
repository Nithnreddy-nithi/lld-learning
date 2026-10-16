# Phase 12 — Concurrency, Race Conditions & Idempotency

## Why this matters

Single-threaded examples hide real failures:

- two gates attempt the final spot
- exit request is retried
- payment webhook is delivered twice
- two gates attempt to close the same ticket
- caller times out after success and retries

## Last-spot race

Bad timeline:

~~~text
Gate A reads spot A101 = free
Gate B reads spot A101 = free
Gate A assigns it
Gate B assigns it
~~~

Both passed the same application-level check.

## Pessimistic locking

~~~python
with transaction.atomic():
    spot = (
        ParkingSpot.objects
        .select_for_update(skip_locked=True)
        .filter(is_occupied=False)
        .first()
    )

    if spot is None:
        raise ParkingFullError()

    spot.is_occupied = True
    spot.save()
~~~

## Optimistic concurrency

Store a version:

~~~text
id=101, version=7
~~~

Update:

~~~sql
UPDATE parking_spot
SET ..., version = 8
WHERE id = 101 AND version = 7;
~~~

If affected rows = 0, someone changed it first.

## Atomic conditional update

Sometimes simplest:

~~~sql
UPDATE parking_spot
SET is_occupied = TRUE
WHERE id = ?
  AND is_occupied = FALSE;
~~~

Check row count.

## Idempotency

Idempotency means repeating the same logical request does not repeat the business effect.

Why retries happen:

~~~text
client -> server
server succeeds
response is lost
client times out
client retries
~~~

Without idempotency, the retry may double-charge or double-close.

## Idempotency record

Store:

- idempotency_key
- operation
- request fingerprint/hash
- status
- response/result
- created_at

Same key + same request:
- return previous result or current processing state.

Same key + different payload:
- reject.

## In-memory set is insufficient

~~~python
seen_keys = set()
~~~

fails across:
- multiple workers
- restart
- multiple servers

Use durable/shared storage where correctness requires it.

## Duplicate webhook

Payment providers may resend the same event. Persist provider_event_id with a unique constraint or maintain a processed-event table. Handler must be idempotent.

## Two exit gates

Both may try to close the same ticket. Lock ticket or use conditional transition:

~~~text
UPDATE ticket
SET status = CLOSED
WHERE id = ? AND status = PAID
~~~

Only one request should win.

## State Pattern vs concurrency

State machine says:

~~~text
PAID -> CLOSED is legal
~~~

Concurrency control says:

~~~text
only one simultaneous request performs that transition
~~~

Both are needed.

## Exactly once

Exactly-once message delivery is extremely hard across distributed systems.

Practical design:

~~~text
at-least-once delivery
+
idempotent consumer
=
exactly-once business effect (where enforceable)
~~~

## Deadlocks

Keep transactions short and acquire locks in consistent order.

## Main lesson

Every read→decision→write sequence should make you ask: what happens if another request changes the data between the read and the write?
