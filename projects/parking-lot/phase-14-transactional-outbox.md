# Phase 14 — Transactional Outbox & Reliable Events

## The dual-write problem

Suppose closing a ticket must update PostgreSQL and publish TicketClosed.

### DB first

~~~text
DB commit succeeds
process crashes before publish
=> event lost
~~~

### Message first

~~~text
message published
DB transaction fails
=> consumers see an event for state that never committed
~~~

Neither ordering is atomic across two systems.

## Transactional Outbox

Store the event as a DB row in the same transaction as business state.

~~~text
BEGIN
  ticket -> CLOSED
  spot -> AVAILABLE
  INSERT outbox_event
COMMIT
~~~

Either all local changes commit, or none do.

## Outbox schema

Typical fields:

~~~text
event_id UUID UNIQUE
event_type
aggregate_type
aggregate_id
payload JSON/JSONB
status
attempt_count
created_at
published_at
next_attempt_at
last_error
~~~

## Django sketch

~~~python
with transaction.atomic():
    ticket = ticket_repo.get_for_update(ticket_id)
    spot = spot_repo.get_for_update(ticket.spot_id)

    ticket.close(exit_time)
    spot.release()

    ticket_repo.save(ticket)
    spot_repo.save(spot)

    OutboxEvent.objects.create(
        event_id=uuid4(),
        event_type="TicketClosed",
        aggregate_type="Ticket",
        aggregate_id=str(ticket.id),
        payload={
            "ticket_id": ticket.id,
            "spot_id": spot.id,
        },
    )
~~~

## Publisher

A background worker queries pending events, publishes them to broker, then marks them published.

~~~text
PENDING -> PROCESSING -> PUBLISHED
                   |
                   -> FAILED / DEAD_LETTER
~~~

## Why duplicates still happen

Worker may:

~~~text
publish event successfully
crash before mark PUBLISHED
restart
publish same event again
~~~

Therefore outbox normally provides at-least-once delivery.

## Consumer idempotency

Every event has stable event_id.

Consumer can store processed IDs:

~~~text
processed_event(event_id UNIQUE)
~~~

or enforce a natural business unique constraint.

## Publisher concurrency

Multiple workers can claim events using row locking/skip locked.

Do not hold DB row locks while waiting indefinitely on broker; a processing-claim model is often better for large systems.

## Ordering

If ordering matters per aggregate, aggregate_id can be used as partition/key information in systems such as Kafka. Global ordering is usually unnecessary and expensive.

## on_commit vs Outbox

transaction.on_commit avoids publishing before commit, but still has:

~~~text
commit succeeds
process crashes before callback publishes
~~~

Outbox closes that durability gap.

## Main lesson

Transactional Outbox solves reliable local state + event recording. It does not eliminate duplicate delivery, retries, or consumer idempotency.
