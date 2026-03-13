import json
import hmac
import hashlib
import urllib.request
import urllib.error
import ssl
from django.conf import settings

def _make_request(url, data=None, headers=None):
    ctx = ssl.create_default_context()

    # Merge in a User-Agent so Cloudflare doesn't block the request
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; HubApp/1.0)',
        **(headers or {}),
    }

    req = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise Exception(f"HTTP {e.code} from {url}: {body}") from e
    except urllib.error.URLError as e:
        raise Exception(f"Network error reaching {url}: {e.reason}") from e

# ── Paystack ───────────────────────────────────────────────────────────────

def paystack_initialize(email, amount_ngn, reference, callback_url):
    payload = json.dumps({
        'email': email,
        'amount': int(amount_ngn * 100),
        'reference': str(reference),
        'callback_url': callback_url,
    }).encode()

    data = _make_request(
        'https://api.paystack.co/transaction/initialize',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
    )
    return data['data']['authorization_url']


def paystack_verify(reference):
    data = _make_request(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers={'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    )
    return data['data']['status'] == 'success'


def paystack_verify_webhook(payload_bytes, signature):
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Flutterwave ────────────────────────────────────────────────────────────

def flutterwave_initialize(email, amount_ngn, reference, callback_url, course_title):
    payload = json.dumps({
        'tx_ref': str(reference),
        'amount': str(amount_ngn),
        'currency': 'NGN',
        'redirect_url': callback_url,
        'customer': {'email': email},
        'customizations': {'title': course_title},
    }).encode()

    data = _make_request(
        'https://api.flutterwave.com/v3/payments',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
    )
    return data['data']['link']


def flutterwave_verify(transaction_id):
    data = _make_request(
        f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify',
        headers={'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'}
    )
    return data['data']['status'] == 'successful'


def flutterwave_verify_webhook(payload_bytes, signature):
    expected = hmac.new(
        settings.FLUTTERWAVE_SECRET_KEY.encode(),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)