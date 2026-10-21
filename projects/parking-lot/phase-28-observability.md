# Phase 28 — Observability

## Why observability exists

A production backend can be logically correct and still be impossible to operate.

When a user says:

> My parking exit failed.

you need to answer:

- Which request failed?
- Which ticket/payment was involved?
- Was PostgreSQL slow?
- Was Redis unavailable?
- Did Celery retry?
- Did the payment provider timeout?
- Did a DB transaction deadlock?
- Did the outbox event publish?
- How often is this happening?

Observability is the ability to understand a running system from the information it emits.

The three core pillars are:

```text
Logs
Metrics
Traces
```

We also care about correlation IDs, alerts, health checks, error tracking, and business metrics.

## 1. Logging

Bad:

```python
print("payment failed")
```

Better:

```python
logger.error(
    "payment_failed",
    extra={
        "ticket_id": ticket_id,
        "payment_id": payment_id,
        "provider": "razorpay",
        "attempt": attempt_number,
    },
)
```

A useful log should answer what happened, where, for which business entity/request, and with what outcome.

## 2. Log levels

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

DEBUG: detailed developer diagnostics.

INFO: normal meaningful events such as vehicle_parked, ticket_closed, payment_succeeded.

WARNING: recoverable unexpected conditions such as retry_scheduled, provider_slow, redis_temporarily_unavailable.

ERROR: failed operations such as payment_failed_after_retries, deadlock, outbox_publish_failed.

CRITICAL: severe system-level failure such as database_unreachable.

## 3. Structured logging

Prefer structured fields over giant strings.

```json
{
  "event": "payment_failed",
  "ticket_id": "T123",
  "payment_id": "P456",
  "provider": "razorpay",
  "retry_count": 2,
  "request_id": "req-abc"
}
```

This lets log systems filter and aggregate reliably.

## 4. Request ID / Correlation ID

One request may touch:

```text
DRF -> service -> PostgreSQL -> Redis -> payment adapter -> outbox -> Celery
```

Give it a correlation ID:

```text
request_id=req-123
```

Every relevant log contains that ID.

Async tasks must propagate it explicitly:

```python
send_receipt.delay(
    ticket_id=ticket.id,
    request_id=request_id,
)
```

## 5. Business IDs and request IDs

Use both where useful.

Request ID identifies one technical execution.

Business IDs such as ticket_id/payment_id connect multiple retries or async operations belonging to the same business workflow.

## 6. Never log secrets

Do not log:

- passwords
- JWT/access tokens
- API keys
- card data
- raw secret headers
- full webhook signatures

Prefer internal IDs or masked sensitive values.

## 7. Metrics

Logs answer:

```text
What happened in this case?
```

Metrics answer:

```text
How is the system behaving overall?
```

Examples:

- requests/sec
- error rate
- latency
- active tickets
- available spots
- payment success rate
- Celery queue depth
- Redis hit ratio
- DB connections

## 8. Counters

Counters only increase.

Examples:

```text
parking_entries_total
parking_exits_total
payment_attempts_total
payment_failures_total
outbox_publish_failures_total
```

## 9. Gauges

Gauges move up and down.

Examples:

```text
available_spots
active_tickets
celery_queue_depth
db_connections_in_use
redis_memory_bytes
```

## 10. Histograms and latency

Histograms measure distributions such as:

```text
request_duration_seconds
payment_provider_latency_seconds
db_query_duration_seconds
spot_allocation_duration_seconds
```

Look at p50/p95/p99, not only average.

```text
average = 100 ms
p99 = 5 sec
```

can still mean a serious tail-latency problem.

## 11. Golden signals

A useful operational model:

```text
Latency
Traffic
Errors
Saturation
```

Parking examples:

Latency:
- /entry duration
- /exit duration
- provider latency
- DB latency

Traffic:
- entry requests/sec
- exit requests/sec
- availability requests/sec

Errors:
- 5xx
- payment technical failures
- task failures
- DB deadlocks

Saturation:
- DB connection usage
- worker utilization
- Celery queue backlog
- Redis memory
- CPU

## 12. Business metrics

Useful Parking Lot metrics:

```text
active_tickets
available_spots_by_type
parking_entries_total
parking_exits_total
parking_full_rejections_total
payment_success_total
payment_failure_total
payment_unknown_total
average_parking_duration
revenue_total
lost_ticket_count
```

Technical health can be green while business behavior is bad.

## 13. Metric labels

Useful labels include provider, endpoint, status, vehicle_type, spot_type.

Avoid high-cardinality labels:

```text
ticket_id
request_id
vehicle_plate
```

These belong in logs/traces, not metrics labels.

## 14. Tracing

Tracing follows one workflow across components.

```text
POST /parking/exit              650 ms
|
+-- validation                    2 ms
+-- load ticket                  15 ms
+-- pricing                       1 ms
+-- payment provider            520 ms
+-- finalize DB transaction      30 ms
+-- enqueue receipt               5 ms
```

This immediately shows where time is spent.

## 15. Spans

A trace contains spans.

Typical spans:

- HTTP request
- DB query
- Redis GET
- payment API call
- Celery task
- outbox publish

A span usually records operation, duration, status, service, and safe correlation metadata.

## 16. Logs vs metrics vs traces

```text
Logs    = detailed event records
Metrics = aggregated numeric behavior
Traces  = one request's journey/timing
```

Example:

Metric says payment failure rate is 12%.

Trace shows provider call timed out.

Logs show payment_id, provider, retry count, and error.

## 17. Error tracking

Unhandled exceptions should be captured centrally with:

- exception type
- stack trace
- endpoint
- request ID
- release/version
- safe entity IDs
- frequency
- first/last seen

Do not rely on manually reading terminal output.

## 18. Entry endpoint observability

For POST /parking-lots/{id}/entry:

Useful logs:

```text
entry_started
spot_selected
ticket_created
entry_completed
parking_full
allocation_conflict
```

Useful metrics:

```text
entry_requests_total
entry_success_total
parking_full_total
entry_duration_seconds
spot_allocation_duration_seconds
allocation_retries_total
```

Useful trace:

```text
HTTP entry
 -> validation
 -> available-spot query
 -> row lock
 -> ticket insert
 -> outbox insert
```

## 19. Exit endpoint observability

Useful logs:

```text
exit_started
fee_calculated
payment_attempt_created
payment_provider_called
payment_succeeded
payment_failed
payment_unknown
ticket_closed
spot_released
exit_completed
```

Metrics:

```text
exit_requests_total
exit_duration_seconds
payment_attempt_total
payment_failure_total
payment_unknown_total
payment_provider_latency_seconds
```

## 20. PostgreSQL metrics

Monitor:

- query latency
- slow queries
- connections used/max
- lock waits
- deadlocks
- transaction duration
- CPU/I/O
- replication lag when applicable

Parking warning signs:

```text
spot allocation latency rising
deadlocks increasing
connection pool nearly exhausted
long-running exit transactions
```

## 21. Redis metrics

Monitor:

- cache hit/miss ratio
- command latency
- memory
- evictions
- connections
- expired keys
- CPU/network

Parking-specific:

```text
availability_cache_hit_ratio
availability_cache_miss_total
idempotency_conflict_total
rate_limit_rejection_total
```

## 22. Celery metrics

Monitor:

```text
queue depth
oldest queued task age
task runtime
success/failure
retry count
worker count
timeouts
permanently failed tasks
```

Oldest task age can be more meaningful than queue count alone.

## 23. Payment-provider metrics

Track per provider:

```text
request count
success rate
business decline rate
technical failure rate
timeout rate
p50/p95/p99 latency
unknown outcome count
webhook delay
reconciliation corrections
```

Do not mix a card decline with a provider timeout; they are different failure categories.

## 24. Outbox metrics

Monitor:

```text
pending_outbox_count
oldest_pending_event_age
publish_success_total
publish_failure_total
publish_retry_total
dead_letter_count
```

Oldest pending event age is a strong signal of a stuck publisher.

## 25. Health checks

Typical endpoints:

```text
/health/live
/health/ready
```

Liveness asks whether the process is alive.

Readiness asks whether the instance is ready to receive traffic.

Do not make liveness depend on every external dependency, or orchestrators may restart healthy processes during dependency outages.

## 26. Alerts

Metrics without alerts require someone to stare at dashboards.

Good alerts are actionable.

Examples:

```text
/exit 5xx > 5% for 10 minutes
payment provider timeout rate > 10%
oldest outbox event > 5 minutes
reconciliation queue oldest task > 10 minutes
```

Prefer user-impact symptoms over noisy transient internal fluctuations.

## 27. SLI / SLO intuition

SLI = measured indicator.

Example:

```text
successful valid parking-entry percentage
```

SLO = target.

Example:

```text
99.9% of valid entry requests complete within 500 ms,
excluding expected parking-full responses.
```

Understand the concept; a full SRE program is not required for this project.

## 28. Business rejection vs system error

Parking full is usually a business outcome, not a 500.

Do not mix:

```text
parking_full
invalid_ticket
payment_declined
```

with:

```text
DB unavailable
uncaught exception
provider timeout
```

Your metrics should distinguish them.

## 29. Request-ID middleware concept

```python
import uuid

class RequestIdMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (
            request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        request.request_id = request_id

        response = self.get_response(request)
        response["X-Request-ID"] = request_id

        return response
```

In production, validate/truncate externally supplied IDs.

## 30. Service logging

```python
logger.info(
    "parking_entry_started",
    extra={
        "request_id": request_id,
        "parking_lot_id": lot_id,
        "vehicle_type": vehicle_type,
    },
)

result = service.park_vehicle(...)

logger.info(
    "parking_entry_completed",
    extra={
        "request_id": request_id,
        "ticket_id": result.ticket_id,
        "spot_id": result.spot_id,
    },
)
```

Stable event names make dashboards/searches easier.

## 31. Exception logging

Prefer:

```python
except PaymentGatewayTimeout:
    logger.exception(
        "payment_gateway_timeout",
        extra={
            "request_id": request_id,
            "payment_id": payment_id,
            "provider": provider,
        },
    )
    raise
```

Do not log the same stack trace at every layer.

## 32. Metrics instrumentation concept

Prometheus-style conceptual code:

```python
ENTRY_REQUESTS.inc()

with ENTRY_DURATION.time():
    result = service.park_vehicle(...)
```

Payment:

```python
PAYMENT_ATTEMPTS.labels(
    provider="razorpay",
).inc()

with PAYMENT_LATENCY.labels(
    provider="razorpay",
).time():
    gateway.charge(...)
```

Never use ticket_id as a metric label.

## 33. Trace instrumentation concept

```text
parking.exit
  -> ticket.load
  -> pricing.calculate
  -> payment.charge
  -> exit.finalize_transaction
  -> receipt.enqueue
```

OpenTelemetry-style instrumentation is a common implementation approach, but the architectural idea matters more than one library.

## 34. Audit log vs application log

Application log:

```text
technical operational event
may rotate/expire
```

Audit log:

```text
durable security/business record
who did what and when
```

Example audit record:

```text
ADMIN U100 manually opened gate G2
reason=emergency
timestamp=...
```

Do not assume ordinary app logs satisfy audit requirements.

## 35. Sampling

At huge traffic, tracing every normal request can be expensive.

Possible policy:

```text
sample 1% of healthy traces
retain more/all error traces
```

But financial/business truth must never depend on sampled tracing.

## 36. Dashboard layout

A useful project dashboard could have:

API:
- request rate
- p50/p95/p99 latency
- 4xx/5xx

Parking:
- available spots
- active tickets
- parking-full rate

Payments:
- success/failure/unknown
- provider latency

DB:
- connections
- query latency
- locks/deadlocks

Redis:
- hit ratio
- evictions
- latency

Celery:
- queue depth
- oldest task
- failures/retries

Outbox:
- pending count
- oldest pending age

## 37. Failure example — slow exits

Metrics:

```text
POST /exit p95 = 4.2 s
```

Trace:

```text
pricing = 2 ms
DB = 20 ms
payment provider = 3.9 s
finalize = 25 ms
```

Logs then reveal provider timeout/retry details.

Now debugging is evidence-driven.

## 38. Failure example — delayed receipt

HTTP and payment metrics are healthy.

Celery shows:

```text
receipt queue oldest task age = 42 minutes
```

Worker utilization is saturated.

Problem is background capacity, not the exit endpoint.

## 39. Failure example — stale availability

Compare:

- Redis cached count
- cache age
- invalidation failures
- DB authoritative count

Even if Redis is stale, allocation remains correct because writes still validate against PostgreSQL.

## 40. Common mistakes

1. Using print() instead of structured logs.
2. Logging secrets.
3. No request/correlation ID.
4. Too much INFO noise.
5. High-cardinality metric labels.
6. Monitoring HTTP only and ignoring async infrastructure.
7. Alerts on every transient blip.
8. Mixing business rejection with system failure.
9. Logging one exception multiple times.
10. No queue-age metric.
11. Looking only at averages instead of p95/p99.
12. Treating logs/traces as business source of truth.
13. No readiness/liveness distinction.
14. No business-workflow dashboard.

## 41. What to implement first

For an SDE1-quality Parking Lot project:

- structured logs
- request ID
- safe ticket/payment/lot IDs in logs
- request/error/latency metrics
- payment success/failure/latency metrics
- Celery success/failure/retry metrics
- DB slow-query visibility
- Redis hit/miss metrics

Then:

- distributed tracing
- dashboards
- alert rules
- outbox lag metrics
- basic SLOs

## 42. Architecture

```text
                 Client
                   |
                   v
                DRF API
                   |
          logs / metrics / traces
                   |
                   v
          Application Services
            /      |       \
           v       v        v
      PostgreSQL  Redis  Payment Provider
           |       |         |
         metrics metrics   metrics
                   |
                   v
             Celery Worker
                   |
          task logs / metrics
                   |
                   v
              Outbox/etc.
```

## Interview answer

> I would instrument the critical parking workflows with structured logs, metrics, and distributed traces. Each request would have a correlation ID propagated into background tasks, while logs would also contain safe business identifiers such as ticket/payment IDs. I would monitor entry/exit latency and error rates, payment-provider success and latency, PostgreSQL locks/query latency, Redis hit ratio, Celery queue depth and oldest-task age, and outbox lag. Alerts should be based on actionable user-impact symptoms such as rising exit failures, payment timeouts, or a stuck outbox rather than every internal fluctuation. Logs and traces are operational data, not the durable business source of truth.

## Phase 28 takeaway

For every important workflow ask:

```text
Can I tell it is failing?
Can I tell how often?
Can I tell how slow?
Can I identify the affected request/business entity?
Can I tell which dependency caused the problem?
Can I alert before users complain?
Can I debug async work after the HTTP request ended?
```

If not, the system is not observable enough.
