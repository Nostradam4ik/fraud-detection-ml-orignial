"""SMS alerting service using Twilio"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS notification service

    Supports multiple providers:
    - Twilio (primary)
    - AWS SNS (fallback)
    - Custom webhook
    """

    def __init__(self, provider: str = "twilio"):
        self.provider = provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize SMS provider client"""
        try:
            if self.provider == "twilio":
                # Twilio client (requires twilio package)
                try:
                    from twilio.rest import Client
                    # These should come from environment variables
                    account_sid = "YOUR_ACCOUNT_SID"
                    auth_token = "YOUR_AUTH_TOKEN"
                    self.client = Client(account_sid, auth_token)
                    self.from_number = "YOUR_TWILIO_NUMBER"
                    logger.info("Twilio SMS client initialized")
                except ImportError:
                    logger.warning("Twilio package not installed")
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio: {e}")

            elif self.provider == "aws_sns":
                # AWS SNS client (requires boto3)
                try:
                    import boto3
                    self.client = boto3.client('sns')
                    logger.info("AWS SNS client initialized")
                except ImportError:
                    logger.warning("boto3 package not installed")
                except Exception as e:
                    logger.error(f"Failed to initialize AWS SNS: {e}")

        except Exception as e:
            logger.error(f"SMS service initialization failed: {e}")

    def send_sms(
        self,
        to_number: str,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        Send SMS message

        Args:
            to_number: Phone number (E.164 format: +1234567890)
            message: SMS message content
            priority: "low", "normal", "high"

        Returns:
            True if sent successfully
        """
        if not self.client:
            logger.warning("SMS client not configured, message not sent")
            return False

        try:
            if self.provider == "twilio":
                result = self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
                logger.info(f"SMS sent via Twilio: {result.sid}")
                return True

            elif self.provider == "aws_sns":
                result = self.client.publish(
                    PhoneNumber=to_number,
                    Message=message
                )
                logger.info(f"SMS sent via AWS SNS: {result['MessageId']}")
                return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_fraud_alert(
        self,
        to_number: str,
        transaction_id: int,
        amount: float,
        risk_score: float
    ) -> bool:
        """Send fraud alert SMS"""
        message = (
            f"🚨 FRAUD ALERT\n"
            f"Transaction #{transaction_id}\n"
            f"Amount: ${amount:.2f}\n"
            f"Risk Score: {risk_score:.1f}%\n"
            f"Please review immediately."
        )

        return self.send_sms(to_number, message, priority="high")

    def send_verification_code(
        self,
        to_number: str,
        code: str
    ) -> bool:
        """Send verification code SMS"""
        message = (
            f"Your verification code is: {code}\n"
            f"This code expires in 10 minutes.\n"
            f"Do not share this code with anyone."
        )

        return self.send_sms(to_number, message, priority="high")

    def send_weekly_summary(
        self,
        to_number: str,
        stats: Dict[str, Any]
    ) -> bool:
        """Send weekly summary SMS"""
        message = (
            f"📊 Weekly Fraud Summary\n"
            f"Total Transactions: {stats.get('total', 0)}\n"
            f"Fraud Detected: {stats.get('fraud', 0)}\n"
            f"Fraud Rate: {stats.get('rate', 0):.1%}\n"
            f"Login to see full report."
        )

        return self.send_sms(to_number, message, priority="low")


# Global SMS service instance
sms_service = SMSService(provider="twilio")
