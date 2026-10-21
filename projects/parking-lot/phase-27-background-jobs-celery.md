# Phase 27 — Background Jobs & Celery

## Why background jobs exist

A web request should finish quickly. Some work is useful but does not need to block the user:

- generate/send receipt
- send email/SMS
- publish outbox events
- reconcile uncertain payments
- build daily reports
- cleanup expired temporary data
- refresh expensive read models

If all of this runs inside the HTTP request:

```text
Client
  -> API
  -> DB work
  -> payment API
  -> PDF generation
  -> email API
  -> analytics
  -> response
```

the request becomes slow and fragile.

A background worker lets us return after the critical business transaction is complete and run secondary work separately.

## Core architecture

```text
                HTTP request
                     |
                     v
                  Django
                     |
          enqueue background task
                     |
                     v
                  Broker
               (Redis/RabbitMQ)
                     |
                     v
               Celery Worker
                     |
               execute task
```

Django does not directly execute the asynchronous work.

It sends a task message to the broker. A Celery worker reads that message and executes the task.

## Main Celery components

### Producer

Usually Django.

It creates/enqueues a task:

```python
send_receipt.delay(ticket_id)
```

### Broker

Temporary message transport between producer and workers.

Common choices:

- Redis
- RabbitMQ

For our project:

```text
Django -> Redis -> Celery Worker
```

### Worker

A separate process that consumes and executes tasks.

```bash
celery -A config worker -l INFO
```

### Result backend

Optional storage for task result/state.

Can store:

```text
PENDING
STARTED
SUCCESS
FAILURE
RETRY
```

For fire-and-forget tasks such as sending an email, application code often should not depend heavily on Celery result backend.

### Celery Beat

Scheduler for periodic tasks.

```text
Celery Beat
    |
    v
  Broker
    |
    v
 Worker
```

Examples:

- every 5 minutes: payment reconciliation
- every day: parking report
- every minute: publish pending outbox events

## Django + Celery setup

Typical project structure:

```text
project/
├── config/
│   ├── __init__.py
│   ├── celery.py
│   └── settings.py
├── parking/
│   ├── tasks.py
│   ├── services.py
│   └── models.py
└── manage.py
```

### config/celery.py

```python
import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

app = Celery("config")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.autodiscover_tasks()
```

### config/__init__.py

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

### settings.py

```python
CELERY_BROKER_URL = "redis://redis:6379/0"

CELERY_RESULT_BACKEND = "redis://redis:6379/1"

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
```

JSON is preferable to arbitrary Python object serialization for safer, clearer message contracts.

## First useful task — send receipt

Do not block the exit API while generating/sending a receipt if the receipt is secondary to the actual parking exit.

```python
from celery import shared_task

@shared_task
def send_parking_receipt(ticket_id):
    ticket = ParkingTicket.objects.get(
        id=ticket_id
    )

    receipt = build_receipt(ticket)

    send_email(
        to=ticket.customer_email,
        attachment=receipt,
    )
```

Call:

```python
send_parking_receipt.delay(
    ticket.id
)
```

`.delay()` is shorthand for enqueueing the Celery task.

## Important: do not pass ORM objects

Bad:

```python
send_parking_receipt.delay(ticket)
```

Why?

- ORM object may not serialize cleanly
- object may be stale by execution time
- message becomes tightly coupled to Python/Django representation

Prefer stable identifiers:

```python
send_parking_receipt.delay(
    ticket_id=ticket.id
)
```

Worker loads current state itself.

## Never enqueue before DB commit if task depends on committed state

Bad:

```python
with transaction.atomic():
    ticket = create_ticket()

    send_receipt.delay(ticket.id)

    # transaction has not committed yet
```

Worker could execute immediately and fail to find the ticket.

Better:

```python
with transaction.atomic():
    ticket = create_ticket()

    transaction.on_commit(
        lambda: send_receipt.delay(
            ticket.id
        )
    )
```

Now task is enqueued only after the transaction commits.

However, remember the reliability gap:

```text
DB commits
process crashes before on_commit callback publishes task
```

For tasks that must never be lost, use the Transactional Outbox rather than relying only on on_commit.

## Best architecture for reliable secondary work

For critical integration events:

```text
Business transaction
    |
    +-> update Ticket/Spot
    +-> insert OutboxEvent
    |
   COMMIT
     |
     v
Outbox Publisher Task
     |
     v
Broker / external system
```

This is stronger than directly enqueueing everything from the request.

## Celery for outbox publishing

A periodic task can publish ready events:

```python
@shared_task
def publish_outbox_batch():
    events = claim_pending_outbox_events(
        limit=100
    )

    for event in events:
        try:
            publish_event(event)
            mark_published(event)
        except Exception as exc:
            mark_failed_attempt(
                event,
                error=str(exc),
            )
```

The task itself must handle duplicate execution safely.

## Idempotent tasks

Celery is normally at-least-once in practical failure scenarios.

A worker can crash after performing side effect but before acknowledging the message.

Task may run again.

Therefore:

```text
background task
!= exactly once
```

Task should be idempotent whenever possible.

### Bad receipt task

```python
def task(ticket_id):
    charge_customer()
    send_receipt()
```

Retry may charge twice.

### Better design

Critical charge happens in an idempotent payment workflow.

Receipt task can check:

```text
receipt already sent?
~~~

or use a durable unique record.

## Retry

Transient failures should often retry.

Celery example:

```python
from celery import shared_task

@shared_task(
    bind=True,
    autoretry_for=(TemporaryEmailError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_parking_receipt(
    self,
    ticket_id,
):
    ...
```

### Backoff

Instead of retrying immediately:

```text
1 sec
2 sec
4 sec
8 sec
...
```

This reduces pressure on a failing dependency.

### Jitter

Adds randomness so thousands of failed tasks do not retry simultaneously.

## Do not retry every error

Classify errors.

### Retryable

- network timeout
- HTTP 503
- temporary provider outage
- DB transient failure

### Usually not retryable

- invalid email address
- missing required business record
- invalid credentials/configuration
- business rejection

Blind retry can make failures worse.

## Payment reconciliation task

Recall uncertain payment states:

```text
PROCESSING
UNKNOWN
```

Periodic reconciliation is a perfect background job.

```python
@shared_task
def reconcile_uncertain_payments():

    payments = (
        PaymentAttempt.objects
        .filter(
            status__in=[
                "processing",
                "unknown",
            ]
        )
        .filter(
            updated_at__lt=threshold()
        )
    )

    for payment in payments:
        reconcile_payment(payment.id)
```

The reconciliation service asks provider for status and applies an idempotent local transition.

## Scheduled reports

Celery Beat can schedule:

```text
daily occupancy report
daily revenue summary
stale-payment reconciliation
cleanup jobs
outbox drain
~~~

Example conceptual schedule:

```python
CELERY_BEAT_SCHEDULE = {
    "reconcile-payments": {
        "task": (
            "parking.tasks."
            "reconcile_uncertain_payments"
        ),
        "schedule": 300.0,
    },
}
```

This means enqueue every 300 seconds.

Beat schedules tasks; workers execute them.

Do not confuse Beat with Worker.

## Web process vs worker

### Web process

Handles:

- HTTP
- validation
- synchronous critical workflow
- immediate response

### Worker

Handles:

- asynchronous jobs
- retries
- slow secondary work
- scheduled processing

If the worker dies, API may still run. If the API dies, workers may continue processing queued tasks.

They are separate processes.

## Docker Compose example

```yaml
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    depends_on:
      - db
      - redis

  celery_worker:
    build: .
    command: celery -A config worker -l INFO
    depends_on:
      - db
      - redis

  celery_beat:
    build: .
    command: celery -A config beat -l INFO
    depends_on:
      - redis

  redis:
    image: redis:7

  db:
    image: postgres:16
```

The web and workers normally use the same application image/code but run different processes.

## Task lifecycle

Conceptually:

```text
created
  ↓
queued in broker
  ↓
reserved by worker
  ↓
running
  ↓
SUCCESS
or
FAILURE
or
RETRY
```

A message can be re-delivered under certain failures, so side effects must remain safe.

## Acknowledgement

Workers acknowledge messages so the broker knows they were processed.

There are tradeoffs around when acknowledgement happens.

If task is acknowledged before execution and worker crashes, work can be lost.

With late acknowledgement, task can be redelivered after worker crash, which improves delivery but increases duplicate-execution possibility.

Therefore:

```text
late acknowledgement
+
idempotent task
~~~

is a common reliability combination for suitable tasks.

## acks_late

Example:

```python
@shared_task(
    acks_late=True,
)
def generate_report(report_id):
    ...
```

Use carefully. It does not magically make side effects exactly-once.

## Time limits

A task should not hang forever.

Celery supports soft/hard time limits.

Conceptually:

```text
soft limit
→ task can catch/cleanup

hard limit
→ worker forcibly terminates execution
```

For external HTTP calls, also configure explicit connect/read timeouts. Celery time limits are not a replacement for network-client timeouts.

## Task granularity

Too large:

```text
generate all reports for all lots for entire year
~~~

One failure repeats huge work.

Too tiny:

```text
one Celery task per trivial DB field update
~~~

creates queue overhead.

Choose meaningful independently retryable units.

## Fan-out

For 100 parking lots:

```text
parent job
  -> report lot 1
  -> report lot 2
  -> ...
~~~

Celery supports groups/chains/chords, but do not use workflow primitives unless the dependency structure requires them.

## Task chaining

Example conceptual workflow:

```text
generate PDF
    ↓
upload PDF
    ↓
send email
```

This can be modeled as chained tasks if each step deserves separate retry/error handling.

For a small system, one task may be simpler.

## Queues and routing

Different workloads may need separate queues:

```text
payments
emails
reports
outbox
~~~

Why?

A huge report workload should not prevent payment reconciliation tasks from running.

Architecture:

```text
               Broker
            /    |     \
           v     v      v
      email-q payment-q report-q
         |       |        |
       workers workers   workers
```

Initially one queue is fine. Split when workload characteristics differ.

## Worker concurrency

Workers can execute multiple tasks concurrently.

Higher concurrency improves throughput for I/O-heavy work but can overwhelm:

- DB connections
- Redis
- provider APIs
- CPU
- memory

Do not increase worker concurrency blindly.

## Prefetch

Workers may reserve multiple messages ahead of execution.

Large prefetch can hurt fairness when tasks have very different durations.

Example:

~~~text
worker A reserves several 10-minute tasks
worker B becomes idle
~~~

Task workload characteristics should influence worker/prefetch configuration.

## Rate limiting external providers

Suppose email provider allows 100 requests/sec.

Do not let 50 workers hammer it without control.

Possible mechanisms:

- Celery task rate limits
- queue-specific worker count
- application/provider-side throttling

## Task result backend

Ask whether result storage is actually needed.

For:

~~~text
send receipt
publish outbox
cleanup
~~~

the business database often contains the authoritative status already.

Do not make Redis result backend the business source of truth.

For long-running user-visible jobs, store a business Job record:

~~~text
job_id
status
progress
result_location
error
~~~

then the API can expose:

~~~text
GET /jobs/{job_id}
~~~

This is more durable/application-specific than relying only on Celery internal state.

## Error handling

A failed task should be observable.

Record/log:

- task name
- task id
- business entity id
- exception
- retry count
- elapsed time
- provider response/status where safe

Do not swallow:

~~~python
try:
    ...
except Exception:
    pass
~~~

## Dead-letter / permanently failed work

After maximum retries, work may need:

- FAILED status
- alert
- manual intervention
- dead-letter queue/table
- reconciliation

Do not retry forever.

## Celery vs synchronous code

Keep synchronous when:

- caller needs result immediately
- work is fast
- operation is core to request correctness

Move asynchronous when:

- work is slow
- user does not need immediate completion
- it can retry independently
- eventual consistency is acceptable

## Parking Lot endpoint examples

### POST /parking/entry

Keep synchronous:

~~~text
validate
find/lock spot
assign
create ticket
commit
return ticket
~~~

Possible async after commit:

- analytics
- notification
- display refresh if eventual is acceptable

### POST /parking/exit

Keep synchronous:

- validate ticket
- pricing needed for user
- payment initiation/result if user must know outcome
- final ticket/spot state

Async:

- receipt generation
- email/SMS
- analytics
- audit export
- downstream integrations

### GET /availability

Normally synchronous/cache read. Do not create a Celery task for every GET.

### Payment reconciliation

Background periodic task.

### Outbox publishing

Background task/worker.

## Critical rule: task is not your domain database

Bad:

~~~text
"Task is queued, therefore payment exists."
~~~

Broker messages can expire, duplicate, or fail.

Persist important business state first, then enqueue work.

## Failure scenario walkthrough

Receipt task:

~~~text
1. Exit transaction commits.
2. Receipt task queued.
3. Worker starts.
4. Email provider times out.
5. Celery retries with backoff.
6. Provider later succeeds.
7. Task marks ReceiptSent record / exits.
~~~

Payment reconciliation:

~~~text
1. Payment is UNKNOWN.
2. Beat enqueues reconciliation.
3. Worker asks provider.
4. Provider says SUCCESS.
5. Service performs idempotent DB transition.
6. If worker crashes, next run sees already-successful state and does nothing harmful.
~~~

## Celery + Outbox distinction

Celery solves:

~~~text
run work asynchronously
~~~

Transactional Outbox solves:

~~~text
reliably record the need to publish/integrate in the same transaction as business state
~~~

They complement each other.

Possible design:

~~~text
DB transaction
  -> OutboxEvent
commit
  -> Celery outbox publisher
  -> external broker/API
~~~

## Common mistakes

1. Passing ORM objects to tasks.
2. Enqueueing before DB commit.
3. Assuming tasks execute exactly once.
4. Retrying non-retryable business errors.
5. Performing non-idempotent payment side effects in blindly retried tasks.
6. Using result backend as business source of truth.
7. Making tasks enormous.
8. No timeouts on network calls.
9. Infinite retries.
10. No monitoring of queue depth/failed tasks.
11. One overloaded queue for every workload at scale.
12. Running critical ticket/spot state only inside asynchronous tasks.

## Interview answer

A strong answer:

> I would keep spot allocation and ticket/payment state transitions in the synchronous transactional request path because the caller needs a definitive result and those operations require strong consistency. I would use Celery for secondary or independently recoverable work such as receipt/email delivery, outbox publishing, payment reconciliation and scheduled reports. Redis or RabbitMQ can act as the broker. Since Celery tasks may be retried or redelivered, task handlers must be idempotent, should receive stable IDs rather than ORM objects, and tasks depending on committed DB state should only be enqueued after commit or through a transactional outbox.

## Mental model

```text
HTTP request
= do the minimum correctness-critical work needed now

Celery
= do slow/retryable/eventually-consistent work later

PostgreSQL
= durable business truth

Redis/RabbitMQ
= task transport

Worker
= background executor

Beat
= scheduler
```

## Phase 27 takeaway

Celery is not merely “run Python later”.

A production background-job design must answer:

- What can be asynchronous?
- What must remain synchronous?
- What is the durable source of truth?
- What happens if task runs twice?
- What happens if worker crashes?
- Which failures should retry?
- How long should retry continue?
- When is the task enqueued relative to DB commit?
- How is permanently failed work recovered?
- How is the queue monitored?
