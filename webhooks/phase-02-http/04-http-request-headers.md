# Phase 2 — Concept 4: HTTP Request Headers

## Goal
Understand HTTP header names and values, how headers differ from bodies, and how Django/DRF reads them.

## 1. What are HTTP headers?
Headers are name-value pairs that contain metadata about an HTTP message.

Example payment webhook:

```http
POST /api/webhooks/payments/ HTTP/1.1
Host: parking.example.com
Content-Type: application/json
User-Agent: PaymentGateway/1.0
X-Webhook-Event: payment.succeeded
X-Webhook-Signature: abc123

{
  "payment_id": "pay_123",
  "amount": 10000,
  "currency": "INR"
}
```

The request line specifies the method and path. The headers describe the message or carry metadata. The body contains payment event data. Here 10000 paise means ₹100.

## 2. Why headers exist
Think of a delivery package: its label tells the recipient how to understand or handle the package, while the package contains the actual item. HTTP headers are like the label and HTTP body is like the contents.

## 3. Useful headers

| Header | Meaning |
|---|---|
| Content-Type | Body media type, e.g. application/json |
| Accept | Response media types preferred by client |
| Authorization | Credentials for supported authentication scheme |
| User-Agent | Software identifying itself as sender |
| Host | Destination host in HTTP/1.1 |
| Content-Length | Body length in bytes when sent |
| X-Webhook-Signature | Example custom webhook signature header |
| X-Webhook-Event | Example custom event-type header |
| X-Request-ID | Example request correlation identifier |

**Custom webhook header names are provider-specific.** Don't assume all providers send the example names shown here.

## 4. Content-Type

```http
Content-Type: application/json
```

This declares that the body should be JSON. Other common values:
- `application/x-www-form-urlencoded` — forms
- `multipart/form-data` — form data including file uploads
- `text/plain` — text
- `application/octet-stream` — generic binary data

A declared content type does **not** ensure the body is valid; parse and validate it.

## 5. Authorization and webhook signatures
Normal API requests may use:

```http
Authorization: Bearer <token>
```

Some webhook providers instead send a cryptographic signature:

```http
X-Webhook-Signature: <signature>
```

The signature has to be verified using the provider's documented rules and the exact raw request bytes. **Just seeing a signature header does not prove authenticity.**

We'll implement HMAC signing and verification in Phase 5.

## 6. Read headers in Django

```python
content_type = request.headers.get("Content-Type")
user_agent = request.headers.get("User-Agent")
signature = request.headers.get("X-Webhook-Signature")
```

Header **names** are case-insensitive.

Django also supports:

```python
request.META.get("CONTENT_TYPE")
request.META.get("HTTP_USER_AGENT")
request.META.get("HTTP_X_WEBHOOK_SIGNATURE")
```

Most headers appear in META as uppercase underscore-separated keys prefixed by HTTP_. CONTENT_TYPE is a special case.

## 7. Read headers in Django REST Framework

```python
from rest_framework.views import APIView
from rest_framework.response import Response

class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        content_type = request.headers.get("Content-Type")
        signature = request.headers.get("X-Webhook-Signature")
        return Response({
            "content_type": content_type,
            "signature_received": signature is not None,
        })
```

This is a headers-inspection demo, **not a secure webhook endpoint**. An external webhook view with no DRF authentication/permissions needs provider-specific signature verification.

## 8. Complete local practice

`views.py`:

```python
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def payment_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        return JsonResponse({"error": "Unsupported content type"}, status=415)

    signature = request.headers.get("X-Webhook-Signature")

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    print("Content Type:", content_type)
    print("Signature provided:", signature is not None)
    print("Payment ID:", payload.get("payment_id"))

    return JsonResponse({"message": "Webhook received"}, status=200)
```

Add to `urls.py`:

```python
from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("api/webhooks/payments/", payment_webhook),
]
```

Run:

```bash
python manage.py runserver
```

Send:

```bash
curl -i -X POST http://127.0.0.1:8000/api/webhooks/payments/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: demo-signature" \
  -d '{"payment_id":"pay_123","amount":10000}'
```

Try changing `Content-Type` to `text/plain` and observe `415 Unsupported Media Type`.

**Production note:** This example only checks header presence, not its validity. It doesn't authenticate the sender or durably store the event, and should never update real payments.

## 9. Interview questions

**Does a signature header prove sender identity?** No. Verify it cryptographically.

**Are header names case-sensitive?** No, names are case-insensitive; values have their own syntax.

**Can webhooks have custom headers?** Yes, provider-specific custom headers are common.

**Should production logs print all headers?** No; credentials and other sensitive data can leak.

**Does Content-Type validate JSON?** No; separately parse and validate.

## Tracker
Phase 2: **4/16 concepts explained**, 12 remaining.

Next: **Concept 5 — JSON Request Bodies**.
