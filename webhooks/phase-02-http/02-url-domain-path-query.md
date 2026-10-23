# Phase 2 — Concept 2: URL, Domain, Path, and Query Parameters

## Goal
Understand how a webhook sender finds our Django backend, which endpoint receives the request, and what each URL component means.

## 1. What is a URL?
A **Uniform Resource Locator (URL)** gives a network destination and a resource path.

Parking payment webhook example:

```text
https://parking.example.com/api/webhooks/payments/
```

A payment provider sends an HTTP POST request to this address when a payment event occurs.

## 2. Anatomy of a URL

```text
https://parking.example.com:443/api/webhooks/payments/?source=gateway&env=test
|---|  |-----------------| |-| |--------------------| |---------------------|
scheme         hostname     port          path                query string
```

| Part | Example | Purpose |
|---|---|---|
| Scheme | `https` | Protocol and secure transport |
| Domain/hostname | `parking.example.com` | Identifies the destination host |
| Port | `443` | Identifies network service (usually omitted for HTTPS) |
| Path | `/api/webhooks/payments/` | Identifies endpoint |
| Query string | `source=gateway&env=test` | Additional URL parameters |

## 3. Scheme: HTTP and HTTPS
`http://` uses HTTP without TLS by default. `https://` uses TLS to protect the communication and authenticate the destination server.

Real-world webhook endpoints should use HTTPS.

## 4. Domain
In `parking.example.com`, `parking` is a subdomain and `example.com` is the parent domain. DNS resolves the hostname to an IP address so the payment provider can establish a connection.

**DNS does not choose the Django view**; it helps find the host.

## 5. Path
All of these paths may share the same domain:

```text
/api/parking/tickets/
/api/parking/spots/
/api/webhooks/payments/
/api/webhooks/shipping/
```

In Django:

```python
from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("api/webhooks/payments/", payment_webhook),
]
```

Django uses URL routing to find the matching view.

## 6. Query parameters
A query string comes after `?`. Multiple key/value pairs are separated by `&`:

```text
https://parking.example.com/api/webhooks/payments/?source=gateway&env=test
```

In Django:

```python
def payment_webhook(request):
    source = request.GET.get("source")  # gateway
    env = request.GET.get("env")        # test
```

In DRF:

```python
source = request.query_params.get("source")
```

This works even when the HTTP method is POST: query parameters and request body are different things.

**Do not use query parameters as proof of sender identity.** Anyone constructing a request can change them. Verify provider-supported webhook signatures instead.

## 7. Ports and localhost
Typical ports:

- HTTP: 80
- HTTPS: 443
- Django `runserver`: 8000 by default

Example:

```text
http://127.0.0.1:8000/api/webhooks/payments/
```

`127.0.0.1` refers to the machine making the request. A remote payment provider cannot call a URL on **your** computer using its own `127.0.0.1`. For local integration testing, use a development tunnel or a publicly reachable test environment.

## 8. How routing works

```text
Payment provider
     |
     | POST https://parking.example.com/api/webhooks/payments/
     v
DNS resolves parking.example.com
     |
     v
HTTPS connection to backend
     |
     v
Reverse proxy/web server
     |
     v
Django URL resolver
     |
     v
payment_webhook(request)
```

## 9. Common questions

**Can endpoints share a domain?** Yes, paths can differ.

**Can POST include a query string?** Yes, query strings and body can both be present.

**Does DNS know the Django path?** No, Django routes the path after the request reaches the server.

**Why not put webhook secrets in URLs?** URLs can be logged or exposed. Use provider-recommended signature validation.

## Try it yourself

Start Django:

```bash
python manage.py runserver
```

Send a request with query parameters:

```bash
curl -i -X POST 'http://127.0.0.1:8000/api/webhooks/payments/?source=gateway&env=test' \
  -H 'Content-Type: application/json' \
  -d '{"event":"payment.succeeded","payment_id":"pay_123"}'
```

Inspect `request.GET` (or DRF `request.query_params`) in your handler.

## Learning tracker
- Phase 2: **2 / 16 concepts explained**
- Remaining: **14**
- Next: **Concept 3 — POST requests and why webhook providers use them**
