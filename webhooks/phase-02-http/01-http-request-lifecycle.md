# Phase 2 — HTTP Knowledge Required for Webhooks

## Goal
Understand how an HTTP request travels from a webhook sender to a Django receiver, what data it carries, and how responses work.

## Learning roadmap (16 concepts)
1. HTTP request lifecycle
2. URL, domain, path, and query parameters
3. POST requests and why providers commonly use them
4. Request headers
5. JSON request bodies
6. Content types
7. Raw request body versus parsed JSON
8. HTTP response bodies
9. Success codes: 200, 202, 204
10. Client errors (4xx) and server errors (5xx)
11. Provider-specific interpretation of response codes
12. Connection and response timeouts
13. HTTPS and TLS
14. DNS resolution and connection failures
15. Redirects
16. Request size limits

---

# Concept 1 — HTTP Request Lifecycle

## What is HTTP?
HTTP means **Hypertext Transfer Protocol**. It defines how a client requests something from a server and how that server responds.

For webhooks, both ends are normally servers:
- **Sender (HTTP client):** payment provider
- **Receiver (HTTP server):** our Django parking-lot backend

## Real-life scenario
A driver pays a parking fee of ₹100. The payment provider sends a `payment.succeeded` event to our Django application.

```text
Customer pays ₹100
       |
       v
Payment provider (webhook sender)
       |
       | HTTPS POST /api/webhooks/payments/
       | JSON: payment succeeded
       v
Django app (webhook receiver)
       |
       | validate and accept event
       v
Return HTTP 200 OK
       |
       v
Process payment event / update database safely
```

In production, processing can happen after the acknowledgment in a background worker, but only after the event has been durably accepted.

## Parts of an HTTP request

```http
POST /api/webhooks/payments/ HTTP/1.1
Host: parking.example.com
Content-Type: application/json

{
  "event": "payment.succeeded",
  "payment_id": "pay_123",
  "amount": 10000,
  "currency": "INR"
}
```

The `POST /api/webhooks/payments/ HTTP/1.1` line specifies the HTTP **method**, **path**, and **protocol version**.

`Host` and `Content-Type` are **headers**: metadata that describes the request.

The JSON between braces is the **body**: the event's actual data. Here `10000` paise means ₹100.00.

## HTTP request lifecycle, step by step

1. **Event happens:** payment provider records a successful payment.
2. **Prepare request:** provider creates JSON event data, headers, and target URL.
3. **Resolve DNS:** domain name is resolved to an address.
4. **Connect securely:** the sender establishes a network connection and, for HTTPS, negotiates TLS.
5. **Send request:** the sender transmits an HTTP POST request.
6. **Route:** web server and Django URL routing select the webhook view.
7. **Handle:** receiver inspects, authenticates, validates, and durably accepts the event.
8. **Respond:** Django returns an HTTP response such as `200 OK` to acknowledge delivery.
9. **Process:** payment record is safely updated; this may be asynchronous.

**Key distinction:** a successful HTTP response is an acknowledgment according to the provider's contract; it does not inherently prove business processing is complete.

## Django hands-on demo

Create a URL route in `urls.py`:

```python
from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("api/webhooks/payments/", payment_webhook),
]
```

Create a view in `views.py`:

```python
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def payment_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    print("Method:", request.method)
    print("Headers:", dict(request.headers))
    print("Body:", payload)

    return JsonResponse({"message": "Webhook received"}, status=200)
```

**Security warning:** `csrf_exempt` does not authenticate the webhook sender. The demo accepts unverified requests, and must **not** be used to mark real payments successful or issue parking tickets. We will introduce raw-body HMAC signature verification, persistence, and idempotency in later phases.

Run:

```bash
python manage.py runserver
```

In another terminal:

```bash
curl -i -X POST http://127.0.0.1:8000/api/webhooks/payments/ \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.succeeded","payment_id":"pay_123"}'
```

Expected response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"message": "Webhook received"}
```

Look at the Django terminal to see the request method, headers, and parsed body.

## Quick check
**Question:** What does a webhook POST body contain?

**Answer:** Typically an event payload (often JSON): event type, payment ID, amount, timestamps, etc.

## Tracker
- Phase 2: **1 / 16 concepts explained**
- Remaining in Phase 2: **15**
- **Next:** Concept 2 — URLs, domains, paths, and query parameters
