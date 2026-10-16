# Phase 13 — Transaction Boundaries + Failure Recovery

DB transactions cannot roll back external payment providers.

Better flow:
1. Short DB tx: validate + create PaymentAttempt(PENDING)
2. Call gateway outside DB tx
3. Short DB tx: finalize payment/ticket/spot

Timeout may mean UNKNOWN, not FAILED.

Recovery: provider idempotency key, webhook, reconciliation, bounded retries, compensation such as refund.
