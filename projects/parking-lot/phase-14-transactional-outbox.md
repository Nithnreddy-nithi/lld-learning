# Phase 14 — Transactional Outbox

Solve DB + message dual-write by storing business changes and OutboxEvent in one transaction.

```text
BEGIN
  update ticket
  release spot
  insert outbox_event
COMMIT
```

Worker publishes pending events later. Delivery is generally at-least-once, so consumers must be idempotent.

Lifecycle can be PENDING -> PROCESSING -> PUBLISHED with retry/dead-letter handling.
