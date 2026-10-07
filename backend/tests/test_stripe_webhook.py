"""Stripe webhook imza doğrulama testleri."""
import hashlib
import hmac
import json
import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_stripe_webhook_missing_signature():
    """İmza başlığı olmadan 400 dönmeli."""
    response = client.post("/api/v1/stripe/webhook", content=b'{"type": "test"}')
    assert response.status_code == 400


def test_stripe_webhook_invalid_signature():
    """Geçersiz imzayla 400 dönmeli."""
    payload = json.dumps({"type": "checkout.session.completed"}).encode()
    response = client.post("/api/v1/stripe/webhook", content=payload,
                           headers={"stripe-signature": "t=1234,v1=invalidsignature"})
    assert response.status_code == 400


def test_stripe_webhook_valid_event():
    """Geçerli (mock) imzayla 200 dönmeli."""
    test_secret = "whsec_test_secret_for_testing"
    payload = json.dumps({"type": "payment_intent.created", "data": {"object": {}}}).encode()
    ts = int(time.time())
    sig = hmac.new(test_secret.encode(), f"{ts}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = {"type": "payment_intent.created", "data": {"object": {}}}
        response = client.post("/api/v1/stripe/webhook", content=payload,
                               headers={"stripe-signature": f"t={ts},v1={sig}"})
    assert response.status_code == 200
