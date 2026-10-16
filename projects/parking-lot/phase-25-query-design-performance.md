# Phase 25 — Query Design + Performance

Allocate spot with filtering/order/locking in SQL, not by loading huge candidate sets into Python.

```sql
SELECT id, floor_id, spot_code, spot_type
FROM parking_spot
WHERE is_active = TRUE
  AND is_occupied = FALSE
  AND spot_type IN ('compact', 'large')
ORDER BY floor_id, spot_code
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

Use indexes based on access patterns, avoid N+1, use select_related/prefetch_related appropriately, use keyset pagination for deep histories, inspect EXPLAIN ANALYZE, and keep lock duration short.

Fix SQL/index/query shape before adding cache.
