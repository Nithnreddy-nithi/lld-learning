# Phase 13 — Transaction Boundaries & Failure Recovery

## The difficult exit workflow

Exit may involve:

- ticket
- pricing
- payment attempt
- external payment provider
- spot
- outbox/event
- receipt

A database transaction protects local DB state only.

## Bad design

~~~text
BEGIN DB transaction
lock ticket
call payment provider for 5 seconds
update spot
COMMIT
~~~

Problems:

- long locks
- poor throughput
- external timeout
- DB rollback cannot undo successful external charge

## Better payment flow

### Step 1 — prepare locally

Short DB transaction:

~~~text
validate ticket
create PaymentAttempt(PENDING/PROCESSING)
store stable payment reference
commit
~~~

### Step 2 — external call

Outside DB transaction:

~~~text
call gateway using stable idempotency reference
~~~

### Step 3 — finalize locally

Short transaction:

~~~text
lock payment/ticket/spot
if already finalized -> return safely
mark payment SUCCESS
mark ticket PAID/CLOSED
release spot
write outbox event
commit
~~~

## Timeout is not failure

Suppose request times out while provider is processing.

You do not know whether provider:

- charged successfully
- failed
- is still processing

Use state such as:

~~~text
UNKNOWN
PROCESSING
~~~

instead of immediately marking FAILED.

## Stable internal PaymentAttempt

Persist before calling provider:

~~~text
payment_attempt_id
ticket_id
amount
idempotency_key
provider
status
~~~

This gives retries/webhooks/reconciliation a stable local object to update.

## Webhook recovery

Provider later calls:

~~~text
payment_succeeded(provider_reference)
~~~

Verify signature, normalize provider event, and apply an idempotent local transition.

## Reconciliation

Periodic job finds old PROCESSING/UNKNOWN payments and asks provider for current status.

This repairs disagreements.

## Retry policy

Classify failures:

- business failure: insufficient balance → do not blindly retry
- transient technical: timeout/503 → retry with backoff
- permanent configuration: invalid credentials → alert
- unknown outcome → reconcile before duplicating action

Use bounded retries and jitter.

## Compensation

If provider succeeded but business operation later needs reversal, perform an explicit business action:

~~~text
RefundPaymentCommand
~~~

This is compensation, not rollback.

## Saga intuition

For workflows spanning independent systems, you can model multiple steps plus compensation. Current Parking Lot can remain explicit orchestration; no need to introduce a full distributed Saga framework.

## Main lesson

Transaction boundaries are designed from invariants and failure modes, not simply by wrapping the entire method in atomic().
