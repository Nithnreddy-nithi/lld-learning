# Phase 24 — Database Schema Design

Now translate the domain into PostgreSQL while considering constraints, history, concurrency, and query patterns.

## Core tables

- parking_lot
- parking_floor
- parking_spot
- parking_ticket
- payment_attempt
- outbox_event

One domain class does not automatically equal one table.

## parking_lot

~~~sql
CREATE TABLE parking_lot (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
~~~

Internal id and business-readable code can coexist.

## parking_floor

~~~sql
CREATE TABLE parking_floor (
    id BIGSERIAL PRIMARY KEY,
    parking_lot_id BIGINT NOT NULL
        REFERENCES parking_lot(id),
    floor_number INTEGER NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        parking_lot_id,
        floor_number
    )
);
~~~

Floor 1 may exist in many lots, but only once per lot.

## parking_spot

~~~sql
CREATE TABLE parking_spot (
    id BIGSERIAL PRIMARY KEY,
    floor_id BIGINT NOT NULL
        REFERENCES parking_floor(id),
    spot_code VARCHAR(50) NOT NULL,
    spot_type VARCHAR(20) NOT NULL,
    is_occupied BOOLEAN NOT NULL DEFAULT FALSE,
    vehicle_plate VARCHAR(30),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        floor_id,
        spot_code
    )
);
~~~

### Boolean vs status

Boolean is enough for AVAILABLE/OCCUPIED.

If requirements add:

- RESERVED
- OUT_OF_SERVICE
- MAINTENANCE

a status enum/string becomes more expressive.

## Duplicated occupancy state

If you store both:

~~~text
spot.is_occupied
open ticket exists
~~~

you now have two representations of occupancy. Keep them consistent in the same transaction and add DB constraints where possible.

## parking_ticket

~~~sql
CREATE TABLE parking_ticket (
    id BIGSERIAL PRIMARY KEY,
    ticket_code VARCHAR(50) NOT NULL UNIQUE,
    parking_lot_id BIGINT NOT NULL
        REFERENCES parking_lot(id),
    parking_spot_id BIGINT NOT NULL
        REFERENCES parking_spot(id),
    vehicle_plate VARCHAR(30) NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
~~~

Status check:

~~~sql
CHECK (
    status IN (
        'active',
        'payment_pending',
        'paid',
        'lost',
        'closed'
    )
)
~~~

Closed ticket invariant:

~~~sql
CHECK (
    status <> 'closed'
    OR exit_time IS NOT NULL
)
~~~

Do not make a constraint stricter than the real workflow.

## One open ticket per spot

Normal UNIQUE(parking_spot_id) would prevent historical reuse of a spot.

Use PostgreSQL partial unique index:

~~~sql
CREATE UNIQUE INDEX ux_open_ticket_per_spot
ON parking_ticket (parking_spot_id)
WHERE status IN (
    'active',
    'payment_pending',
    'paid',
    'lost'
);
~~~

A spot can have many historical closed tickets, but only one current open session.

## payment_attempt

Payment retries mean one Ticket may have many attempts.

~~~sql
CREATE TABLE payment_attempt (
    id BIGSERIAL PRIMARY KEY,
    payment_code VARCHAR(50) NOT NULL UNIQUE,
    ticket_id BIGINT NOT NULL
        REFERENCES parking_ticket(id),
    amount_minor BIGINT NOT NULL,
    currency CHAR(3) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    provider VARCHAR(50),
    provider_reference VARCHAR(100),
    idempotency_key VARCHAR(100),
    failure_code VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (amount_minor >= 0)
);
~~~

Store Money as minor units + currency or exact NUMERIC, not float.

Possible provider uniqueness:

~~~sql
UNIQUE(provider, provider_reference)
~~~

when provider guarantees that semantics.

## outbox_event

~~~sql
CREATE TABLE outbox_event (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);
~~~

Partial publisher index:

~~~sql
CREATE INDEX ix_outbox_pending
ON outbox_event(created_at)
WHERE status = 'pending';
~~~

## Spot-allocation index

Example:

~~~sql
CREATE INDEX ix_spot_availability
ON parking_spot(
    floor_id,
    spot_type,
    spot_code
)
WHERE is_occupied = FALSE
  AND is_active = TRUE;
~~~

Design indexes from queries, not from columns independently.

## Vehicle table?

Do not add a separate Vehicle table unless Vehicle becomes a persisted first-class concept with:

- owner
- subscription
- blacklist
- profile/history

A license plate snapshot directly on Ticket can be useful historical data.

## Deletion

Do not blindly cascade-delete historical tickets/payments.

Configuration entities may use:

~~~text
is_active = false
~~~

rather than hard deletion.

Ticket/payment history should usually remain auditable.

## Timestamp distinction

~~~text
created_at/updated_at = persistence timestamps
entry_time/exit_time  = business timestamps
~~~

They are not interchangeable.

## DB validation + application validation

Use both:

Application:
- meaningful domain error

Database:
- final integrity protection against concurrency, scripts, bugs, alternate writers

## Entry transaction

~~~text
BEGIN
SELECT available spot FOR UPDATE SKIP LOCKED
UPDATE spot -> occupied
INSERT ticket
INSERT outbox event
COMMIT
~~~

## Main lesson

The database is not just storage. It is another correctness layer alongside domain logic and transaction/locking rules.
