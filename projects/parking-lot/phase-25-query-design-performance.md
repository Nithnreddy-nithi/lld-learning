# Phase 25 — Query Design & Performance

Performance design begins with access patterns.

Ask:

- What queries run most often?
- Which paths are latency-sensitive?
- Which tables become large?
- What rows are frequently updated?
- What needs locking?
- What data is actually required by the endpoint?

## Query 1 — allocate an available spot

For a CAR compatible with COMPACT/LARGE:

~~~sql
SELECT
    id,
    floor_id,
    spot_code,
    spot_type
FROM parking_spot
WHERE is_active = TRUE
  AND is_occupied = FALSE
  AND spot_type IN ('compact', 'large')
ORDER BY floor_id, spot_code
LIMIT 1
FOR UPDATE SKIP LOCKED;
~~~

This avoids:

~~~python
spots = list(
    ParkingSpot.objects.filter(
        is_occupied=False
    )
)
~~~

followed by Python iteration across thousands of rows.

## Potential partial index

~~~sql
CREATE INDEX ix_available_spot
ON parking_spot(
    spot_type,
    floor_id,
    spot_code
)
WHERE is_active = TRUE
  AND is_occupied = FALSE;
~~~

Exact column order depends on the dominant filter/order patterns.

## Django

~~~python
with transaction.atomic():
    spot = (
        ParkingSpot.objects
        .select_for_update(
            skip_locked=True
        )
        .filter(
            is_active=True,
            is_occupied=False,
            spot_type__in=[
                SpotType.COMPACT,
                SpotType.LARGE,
            ],
        )
        .order_by(
            "floor_id",
            "spot_code",
        )
        .first()
    )
~~~

## Query 2 — availability counts

~~~sql
SELECT
    floor_id,
    spot_type,
    COUNT(*) AS available_count
FROM parking_spot
WHERE is_active = TRUE
  AND is_occupied = FALSE
GROUP BY floor_id, spot_type;
~~~

Django:

~~~python
availability = (
    ParkingSpot.objects
    .filter(
        is_active=True,
        is_occupied=False,
    )
    .values(
        "floor_id",
        "spot_type",
    )
    .annotate(
        available_count=Count("id")
    )
)
~~~

Do not fetch all spot rows and count in Python.

## Query 3 — open ticket by vehicle

~~~sql
SELECT *
FROM parking_ticket
WHERE vehicle_plate = ?
  AND status IN (
      'active',
      'payment_pending',
      'paid',
      'lost'
  )
ORDER BY entry_time DESC
LIMIT 1;
~~~

Partial index:

~~~sql
CREATE INDEX ix_open_ticket_vehicle
ON parking_ticket(
    vehicle_plate,
    entry_time DESC
)
WHERE status IN (
    'active',
    'payment_pending',
    'paid',
    'lost'
);
~~~

If most tickets are closed, this index remains much smaller than a full history index.

## Query 4 — vehicle history

~~~sql
SELECT *
FROM parking_ticket
WHERE vehicle_plate = ?
ORDER BY entry_time DESC, id DESC
LIMIT 20;
~~~

Index:

~~~sql
CREATE INDEX ix_ticket_vehicle_history
ON parking_ticket(
    vehicle_plate,
    entry_time DESC,
    id DESC
);
~~~

## Keyset pagination

Large OFFSET becomes expensive.

Instead of:

~~~sql
OFFSET 500000 LIMIT 20
~~~

use last-seen cursor:

~~~sql
WHERE vehicle_plate = ?
  AND (
      entry_time < ?
      OR (
          entry_time = ?
          AND id < ?
      )
  )
ORDER BY entry_time DESC, id DESC
LIMIT 20;
~~~

ID is a tiebreaker for equal timestamps.

## Query 5 — payment attempts

~~~sql
SELECT *
FROM payment_attempt
WHERE ticket_id = ?
ORDER BY created_at DESC;
~~~

Index:

~~~sql
CREATE INDEX ix_payment_ticket_created
ON payment_attempt(
    ticket_id,
    created_at DESC
);
~~~

## Query 6 — ready outbox events

~~~sql
SELECT *
FROM outbox_event
WHERE status = 'pending'
  AND (
      next_attempt_at IS NULL
      OR next_attempt_at <= NOW()
  )
ORDER BY created_at
LIMIT 100
FOR UPDATE SKIP LOCKED;
~~~

Multiple workers can claim different rows.

## N+1

Bad:

~~~python
tickets = ParkingTicket.objects.all()

for ticket in tickets:
    print(
        ticket.parking_spot.floor.name
    )
~~~

Potentially one query for tickets + many spot/floor queries.

Use select_related for forward FK/OneToOne:

~~~python
tickets = (
    ParkingTicket.objects
    .select_related(
        "parking_spot",
        "parking_spot__floor",
    )
)
~~~

Use prefetch_related for reverse FK/ManyToMany:

~~~python
floors = (
    ParkingFloor.objects
    .prefetch_related("spots")
)
~~~

Mental rule:

~~~text
select_related   -> JOIN -> FK / OneToOne
prefetch_related -> extra query + Python mapping -> reverse FK / M2M
~~~

## Fetch only what is needed

Dashboard aggregation can use .values() instead of constructing full model objects.

Be careful with .only(): accessing a deferred field later may trigger extra queries.

## exists() / count()

Use:

~~~python
queryset.exists()
queryset.count()
~~~

when you only need existence/count, rather than loading rows.

## EXPLAIN ANALYZE

Do not guess about indexes.

Inspect:

- Seq Scan
- Index Scan
- Bitmap Scan
- joins
- sorts
- estimated vs actual rows
- execution time

Sequential scan is not always bad for tiny/high-selectivity-cost tables.

## Composite indexes

B-tree index:

~~~text
(floor_id, spot_type, spot_code)
~~~

naturally supports leftmost-prefix patterns better than arbitrary trailing-column-only lookup.

## Low-cardinality columns

Standalone index on:

~~~text
is_occupied
~~~

may be weak because only true/false exist. A partial index for available rows plus useful sorting/filter columns can be far better.

## Hot rows

Avoid one global row:

~~~text
parking_lot.available_spot_count
~~~

updated for every entry/exit under heavy load. It becomes a contention point.

Possible alternatives:

- derive counts
- partition counters by floor/type
- cached/read-model counters

Only optimize if real load requires it.

## Redis comes after SQL hygiene

Order:

1. correct query
2. appropriate index
3. remove N+1
4. fetch fewer rows/columns
5. pagination
6. transaction/lock tuning
7. measure
8. cache if justified

## Write vs read model

Write side:
- invariants
- locks
- aggregates

Read side:
- optimized joins/aggregations/projections

A selector/query-service layer can be useful for complex reads.

## Lock duration

Correctness and performance overlap. Holding locks around external network calls reduces throughput.

Keep DB critical sections short.

## Main lesson

For every important endpoint ask:

~~~text
What exact SQL runs?
How many rows does it touch?
What index supports it?
How many queries occur?
Does it lock?
How long?
Can aggregation happen in SQL?
Can stale data be tolerated?
~~~
