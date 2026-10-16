# Phase 11 — API / DRF Mapping

```text
Client -> DRF View -> Serializer -> Application Service -> Domain/Strategy -> Repository/ORM -> PostgreSQL
```

View handles HTTP. Serializer handles transport validation. Service handles use-case orchestration. Domain owns invariants.

Prefer use-case endpoints such as POST /parking/exit rather than PATCH status=closed that bypasses workflow.
