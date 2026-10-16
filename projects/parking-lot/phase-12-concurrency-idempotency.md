# Phase 12 — Concurrency + Idempotency

Last-spot race requires DB-level protection.

Tools: select_for_update, skip_locked, optimistic versioning, atomic conditional updates, DB constraints.

Idempotency means repeated logical request has one business effect. Store idempotency key, request fingerprint, status, and result. Same key + different payload should be rejected.

Correctness layers:
1. Domain validation
2. Transaction/locking
3. Database constraint
