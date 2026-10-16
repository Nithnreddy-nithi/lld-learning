# Phase 24 — Database Schema

Core tables:
parking_lot, parking_floor, parking_spot, parking_ticket, payment_attempt, outbox_event.

Important constraints:
```sql
UNIQUE (parking_lot_id, floor_number)
UNIQUE (floor_id, spot_code)

CREATE UNIQUE INDEX ux_open_ticket_per_spot
ON parking_ticket(parking_spot_id)
WHERE status IN ('active', 'payment_pending', 'paid', 'lost');

CHECK (status <> 'closed' OR exit_time IS NOT NULL)
```

PaymentAttempt supports retries and stores amount_minor, currency, method, status, provider, provider_reference, idempotency_key.

Database is a correctness layer as well as storage.
