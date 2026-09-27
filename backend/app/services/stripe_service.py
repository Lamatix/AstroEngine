"""
Stripe integration for credit top-ups (Checkout Sessions + webhook verification).
"""
import logging
from typing import Dict, Any
import stripe

from app.config.settings import get_settings

logger = logging.getLogger("stripe_service")
settings = get_settings()

stripe.api_key = settings.STRIPE_SECRET_KEY

CREDIT_PACKAGES: Dict[str, Dict[str, Any]] = {
    "starter_100": {"credits": 100, "price_usd": 4.99},
    "growth_500": {"credits": 500, "price_usd": 19.99},
    "pro_1500": {"credits": 1500, "price_usd": 49.99},
}


def get_package(package_id: str) -> Dict[str, Any]:
    package = CREDIT_PACKAGES.get(package_id)
    if package is None:
        raise ValueError(f"Unknown credit package: {package_id}")
    return package


def create_checkout_session(
    user_id: str,
    package_id: str,
    success_url: str,
    cancel_url: str
) -> stripe.checkout.Session:
    package = get_package(package_id)
    return stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"{package['credits']} Credits Top-up"},
                    "unit_amount": int(package["price_usd"] * 100),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "user_id": user_id,
            "package_id": package_id,
            "credits": str(package["credits"]),
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )


def verify_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )