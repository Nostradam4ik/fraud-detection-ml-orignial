"""Payment processing service with Stripe and PayPal"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StripePaymentService:
    """
    Stripe payment processing

    Features:
    - Subscription management
    - One-time payments
    - Customer management
    - Webhooks
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Stripe client"""
        try:
            import stripe
            stripe.api_key = self.api_key or "sk_test_..."  # Use env variable
            self.client = stripe
            logger.info("Stripe client initialized")
        except ImportError:
            logger.warning("Stripe package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a Stripe customer"""
        if not self.client:
            return None

        try:
            customer = self.client.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            return {
                'id': customer.id,
                'email': customer.email,
                'created': customer.created
            }

        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return None

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0
    ) -> Optional[Dict]:
        """Create a subscription"""
        if not self.client:
            return None

        try:
            subscription = self.client.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=trial_days if trial_days > 0 else None
            )

            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end
            }

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        if not self.client:
            return False

        try:
            self.client.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def create_payment_intent(
        self,
        amount: int,  # in cents
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a one-time payment intent"""
        if not self.client:
            return None

        try:
            intent = self.client.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {}
            )

            return {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
                'amount': intent.amount
            }

        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None

    def construct_webhook_event(self, payload: bytes, signature: str, secret: str):
        """Verify and construct webhook event"""
        if not self.client:
            return None

        try:
            event = self.client.Webhook.construct_event(
                payload, signature, secret
            )
            return event
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return None


class PayPalPaymentService:
    """
    PayPal payment processing

    Features:
    - Order creation
    - Payment capture
    - Subscription management
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.sandbox = True  # Use sandbox for testing

    def _get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        try:
            import requests
            import base64

            url = "https://api.sandbox.paypal.com/v1/oauth2/token" if self.sandbox else \
                  "https://api.paypal.com/v1/oauth2/token"

            auth = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()

            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            data = {'grant_type': 'client_credentials'}

            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()

            self.access_token = response.json()['access_token']
            return self.access_token

        except Exception as e:
            logger.error(f"Failed to get PayPal access token: {e}")
            return None

    def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "Fraud Detection Service"
    ) -> Optional[Dict]:
        """Create a PayPal order"""
        if not self.access_token:
            self._get_access_token()

        if not self.access_token:
            return None

        try:
            import requests

            url = "https://api.sandbox.paypal.com/v2/checkout/orders" if self.sandbox else \
                  "https://api.paypal.com/v2/checkout/orders"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': currency,
                        'value': str(amount)
                    },
                    'description': description
                }]
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            order = response.json()

            return {
                'id': order['id'],
                'status': order['status'],
                'links': order['links']
            }

        except Exception as e:
            logger.error(f"Failed to create PayPal order: {e}")
            return None

    def capture_order(self, order_id: str) -> Optional[Dict]:
        """Capture a PayPal order"""
        if not self.access_token:
            self._get_access_token()

        if not self.access_token:
            return None

        try:
            import requests

            url = f"https://api.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture" \
                  if self.sandbox else \
                  f"https://api.paypal.com/v2/checkout/orders/{order_id}/capture"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers)
            response.raise_for_status()

            capture = response.json()

            return {
                'id': capture['id'],
                'status': capture['status'],
                'payer': capture.get('payer', {})
            }

        except Exception as e:
            logger.error(f"Failed to capture PayPal order: {e}")
            return None


# Global service instances
stripe_service = StripePaymentService()
paypal_service = PayPalPaymentService()
