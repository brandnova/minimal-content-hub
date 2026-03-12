import json
import hmac
import hashlib
import urllib.request
import urllib.parse
from django.conf import settings


# ── Paystack ───────────────────────────────────────────────────────────────

def paystack_initialize(email, amount_ngn, reference, callback_url):
    """Initialize a Paystack transaction. Returns the authorization_url."""
    payload = json.dumps({
        'email': email,
        'amount': int(amount_ngn * 100),    # Paystack expects kobo
        'reference': str(reference),
        'callback_url': callback_url,
    }).encode()

    req = urllib.request.Request(
        'https://api.paystack.co/transaction/initialize',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
    return data['data']['authorization_url']


def paystack_verify(reference):
    """Verify a Paystack transaction. Returns True if paid."""
    req = urllib.request.Request(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers={'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
    return data['data']['status'] == 'success'


def paystack_verify_webhook(payload_bytes, signature):
    """Validate Paystack webhook signature."""
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Flutterwave ────────────────────────────────────────────────────────────

def flutterwave_initialize(email, amount_ngn, reference, callback_url, course_title):
    """Initialize a Flutterwave payment. Returns the payment link."""
    payload = json.dumps({
        'tx_ref': str(reference),
        'amount': str(amount_ngn),
        'currency': 'NGN',
        'redirect_url': callback_url,
        'customer': {'email': email},
        'customizations': {'title': course_title},
    }).encode()

    req = urllib.request.Request(
        'https://api.flutterwave.com/v3/payments',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
    return data['data']['link']


def flutterwave_verify(transaction_id):
    """Verify a Flutterwave transaction by ID. Returns True if successful."""
    req = urllib.request.Request(
        f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify',
        headers={'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'}
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
    return data['data']['status'] == 'successful'


def flutterwave_verify_webhook(payload_bytes, signature):
    """Validate Flutterwave webhook signature."""
    expected = hmac.new(
        settings.FLUTTERWAVE_SECRET_KEY.encode(),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)