# Phase 2 — Concept 5: JSON Request Bodies

## Goal
Understand JSON payloads used in webhook requests, nested data, raw-byte decoding, and validation in Django/DRF.

## 1. What is JSON?
JSON (JavaScript Object Notation) is a text format for exchanging structured data.

Example payment event:
```json
{
  "event": "payment.succeeded",
  "payment_id": "pay_123",
  "amount": 10000,
  "currency": "INR"
}
```
Here the amount is in paise: 10000 paise = ₹100.

## 2. JSON lives in the HTTP request body

```http
POST /api/webhooks/payments/ HTTP/1.1
Host: parking.example.com
Content-Type: application/json

{"event":"payment.succeeded","payment_id":"pay_123"}
```

`Content-Type` describes the format; the actual JSON is in the **body**.

## 3. JSON types and Python equivalents

| JSON type | Example | Python |
|---|---|---|
| String | `"paid"` | `str` |
| Number | `100`, `10.5` | `int`, `float` |
| Boolean | `true` | `True` |
| Null | `null` | `None` |
| Object | `{"id":123}` | `dict` |
| Array | `[1,2]` | `list` |

JSON is text, not a Python dictionary, though a JSON object can be decoded into one.

## 4. Nested webhook payload

```json
{
  "id": "evt_001",
  "type": "payment.succeeded",
  "data": {
    "payment": {
      "id": "pay_123",
      "amount": 10000,
      "currency": "INR"
    },
    "parking": {
      "ticket_id": "ticket_456",
      "floor": 2,
      "spot": "A12"
    }
  }
}
```

After parsing into a Python dictionary:
```python
event_type = payload["type"]
payment_id = payload["data"]["payment"]["id"]
amount = payload["data"]["payment"]["amount"]
ticket_id = payload["data"]["parking"]["ticket_id"]
```
This is an *illustrative schema*. Each actual payment provider defines its own payload shape.

## 5. Raw bytes and Python parsing

```python
raw_body = request.body
# b'{"event":"payment.succeeded","amount":10000}'

import json
payload = json.loads(raw_body)
# {"event": "payment.succeeded", "amount": 10000}
```

The HTTP body arrives as bytes. `json.loads()` decodes and parses JSON into Python objects.

```text
HTTP JSON body (bytes)
         |
         v
json.loads(request.body)
         |
         v
Python dict / list / scalar
```

## 6. JSON syntax vs business validation
These are different questions:

- Is this valid JSON syntax?
- Does this JSON satisfy our payment-event rules?

Example valid JSON with invalid business fields:
```json
{"payment_id": null, "amount": "banana"}
```

Some rules might require a nonempty payment ID, a positive integer amount, a supported currency and a recognized event type.

A valid JSON document can also be an array, number, or string. Check that its root has the type your API expects.

## 7. Django hands-on

`urls.py`:
```python
from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("api/webhooks/payments/", payment_webhook)
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

    if request.content_type != "application/json":
        return JsonResponse({"error": "Expected application/json"}, status=415)

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Expected a JSON object"}, status=400)

    payment_id = payload.get("payment_id")
    amount = payload.get("amount")

    if not isinstance(payment_id, str) or not payment_id:
        return JsonResponse({"error": "Invalid payment_id"}, status=400)

    if type(amount) is not int or amount <= 0:
        return JsonResponse({"error": "Invalid amount"}, status=400)

    return JsonResponse(
        {"message": "Valid JSON received", "payment_id": payment_id},
        status=200
    )
```

`type(amount) is int` avoids inadvertently accepting a Python `bool` as an integer, because `isinstance(True, int)` is `True`.

**Important:** This receiver is for *local learning only*. CSRF exemption is not proof of sender identity; production webhook endpoints need sender-signature verification, durable acceptance, and idempotency before updating payments.

## 8. DRF parsing

```python
from rest_framework.views import APIView
from rest_framework.response import Response

class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data
        return Response({"event": payload.get("event")})
```

DRF's `request.data` parses JSON when its JSON parser is configured. This demo assumes an object-shaped payload and does not authenticate the sender. For HMAC signatures, preserve the *original raw bytes* instead of reconstructing JSON.

## 9. Practice with curl

```bash
python manage.py runserver
```

```bash
curl -i -X POST http://127.0.0.1:8000/api/webhooks/payments/ \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"pay_123","amount":10000}'
```

Try three changes:
1. Remove a comma to create malformed JSON (expect 400).
2. Make `amount` a string (expect 400).
3. Send `[]` instead of an object (expect 400).

## 10. Interview questions

**Is JSON a Python dictionary?** No; JSON is a text format. JSON objects decode into dictionaries.

**Does Django parse JSON into request.POST?** No. Use `json.loads(request.body)` or DRF's `request.data`.

**What happens when JSON is malformed?** Parsing fails, so respond with a suitable client error.

**Can JSON be nested?** Yes, with objects and arrays.

**Why validate after parsing?** Syntax-valid JSON can still be business-invalid.

## Phase 2 tracker

- Completed: **5/16**
- Remaining: **11**
- Next: **Concept 6 — Content Types**
