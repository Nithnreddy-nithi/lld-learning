# Phase 2 — Concept 3: POST Requests and Why Webhooks Use Them

## Goal
Understand HTTP POST, why webhook providers use it, how Django receives it, and why repeated POST requests require care.

## 1. What is POST?
HTTP methods describe the type of operation being requested:

| Method | Common use | Parking example |
|---|---|---|
| GET | Retrieve information | Read a parking ticket |
| POST | Submit information for processing | Deliver a payment webhook |
| PUT | Replace a resource | Replace ticket details |
| PATCH | Partially update a resource | Change ticket status |
| DELETE | Delete a resource | Delete a draft |

**POST submits data to a server for processing.**

## 2. Payment webhook example

```http
POST /api/webhooks/payments/ HTTP/1.1
Host: parking.example.com
Content-Type: application/json

{
  "event": "payment.succeeded",
  "payment_id": "pay_123",
  "ticket_id": "ticket_456",
  "amount": 10000,
  "currency": "INR"
}
```

Here 10000 paise = ₹100.00.

```text
Customer pays
      |
      v
Payment provider creates event
      |
      | HTTP POST + JSON body
      v
Django webhook endpoint
      |
      | Validate/authenticate/accept safely
      v
HTTP acknowledgment
```

## 3. Why POST?
1. POST can carry a structured JSON request body.
2. POST represents submitting information to an endpoint to be processed.
3. Unlike PUT, POST is **not idempotent by HTTP semantics**: repeating it can cause repeated effects if the application is poorly designed.

This does **not** mean POST requests cannot be implemented idempotently. Real webhook receivers should implement deduplication and business idempotency.

## 4. Query parameters vs POST body

Query:
```http
POST /api/webhooks/payments/?payment_id=pay_123 HTTP/1.1
```

Body:
```http
POST /api/webhooks/payments/ HTTP/1.1
Content-Type: application/json

{"payment_id": "pay_123", "status": "succeeded"}
```

Both can appear in the same POST request. Webhook event data normally goes in the body.

## 5. Django example (learning only)

`urls.py`:
```python
from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("api/webhooks/payments/", payment_webhook),
]
```

`views.py`:
```python
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def payment_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event = data.get("event")
    payment_id = data.get("payment_id")

    print("Event:", event)
    print("Payment ID:", payment_id)
    return JsonResponse({"message": "Event received"}, status=200)
```

Sequence:
1. Django receives POST.
2. `request.method` is `POST`.
3. `request.body` gives the raw bytes.
4. `json.loads` parses the JSON.
5. The view extracts fields.
6. Django responds.

**Security:** This learning example is not production-ready. `csrf_exempt` does not authenticate a sender. Production payment receivers must verify provider signatures, validate payloads, durably accept events, and handle duplicates before changing business state.

## 6. request.body vs request.POST vs DRF request.data

| Property | Contains |
|---|---|
| `request.body` | Raw request bytes |
| `request.POST` | Parsed HTML form data; usually empty for JSON |
| DRF `request.data` | Parsed request data including JSON, with an appropriate parser |

Example:
```json
{"event":"payment.succeeded","payment_id":"pay_123"}
```

Django's `request.body` is bytes, e.g. `b'{"event":"payment.succeeded","payment_id":"pay_123"}'`. DRF `request.data` can contain the corresponding Python dictionary.

For HMAC verification, use the exact **original raw bytes**, not reconstructed JSON.

## 7. What if POST arrives twice?

```text
Provider -> Django: POST event evt_001
Django  -> Provider: response lost in network
Provider -> Django: retry POST event evt_001
```

If each delivery triggers a new parking ticket, the customer may receive duplicates.

**Idempotency** means repeated delivery must not create repeated unintended business effects. In Phase 7, we'll implement this with unique constraints, database transactions, and event IDs.

## 8. Practice with curl

Start Django:
```bash
python manage.py runserver
```

Send event:
```bash
curl -i -X POST http://127.0.0.1:8000/api/webhooks/payments/ \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.succeeded","payment_id":"pay_123"}'
```

Run it twice and observe two deliveries.

Send GET:
```bash
curl -i http://127.0.0.1:8000/api/webhooks/payments/
```

The example returns `405 Method Not Allowed`.

## 9. Interview questions

**Why do providers use POST instead of GET?** To submit event data for processing, commonly in a JSON body. GET is intended for retrieval and should not trigger state-changing actions.

**Does POST always create a new object?** No. POST semantics allow submitting information for server-side processing, which could update state or trigger a workflow.

**Is POST automatically idempotent?** No. The receiver must implement the relevant safety rules.

**Can POST have both body and query parameters?** Yes.

**Do JSON POST values appear in Django request.POST?** Usually no; parse raw JSON or use DRF request.data.

## Tracker
- Phase 2: **3 of 16 concepts explained**
- Remaining: **13**
- Next: **Concept 4 — Request Headers**
