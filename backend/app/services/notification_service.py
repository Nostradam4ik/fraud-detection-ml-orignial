"""
Notification Service - Slack and Discord integrations

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    FRAUD_DETECTED = "fraud_detected"
    HIGH_RISK_ALERT = "high_risk_alert"
    BATCH_COMPLETE = "batch_complete"
    DAILY_SUMMARY = "daily_summary"
    SYSTEM_ALERT = "system_alert"


class NotificationService:
    """Service for sending notifications to Slack and Discord"""

    @staticmethod
    async def send_slack_notification(
        webhook_url: str,
        message: str,
        notification_type: NotificationType,
        data: Optional[Dict[str, Any]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send a notification to Slack via webhook.

        Args:
            webhook_url: Slack webhook URL
            message: Main message text
            notification_type: Type of notification for formatting
            data: Additional data to include
            channel: Optional channel override

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build Slack message with blocks for rich formatting
            blocks = []

            # Header
            emoji = {
                NotificationType.FRAUD_DETECTED: ":rotating_light:",
                NotificationType.HIGH_RISK_ALERT: ":warning:",
                NotificationType.BATCH_COMPLETE: ":white_check_mark:",
                NotificationType.DAILY_SUMMARY: ":bar_chart:",
                NotificationType.SYSTEM_ALERT: ":bell:",
            }.get(notification_type, ":bell:")

            color = {
                NotificationType.FRAUD_DETECTED: "#dc2626",
                NotificationType.HIGH_RISK_ALERT: "#f59e0b",
                NotificationType.BATCH_COMPLETE: "#10b981",
                NotificationType.DAILY_SUMMARY: "#3b82f6",
                NotificationType.SYSTEM_ALERT: "#8b5cf6",
            }.get(notification_type, "#6b7280")

            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {notification_type.value.replace('_', ' ').title()}",
                    "emoji": True
                }
            })

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            })

            # Add data fields if provided
            if data:
                fields = []
                for key, value in data.items():
                    if len(fields) < 10:  # Slack limit
                        fields.append({
                            "type": "mrkdwn",
                            "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
                        })

                if fields:
                    blocks.append({
                        "type": "section",
                        "fields": fields
                    })

            # Footer with timestamp
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Fraud Detection System • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                    }
                ]
            })

            payload = {
                "blocks": blocks,
                "attachments": [{
                    "color": color,
                    "fallback": message
                }]
            }

            if channel:
                payload["channel"] = channel

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    @staticmethod
    async def send_discord_notification(
        webhook_url: str,
        message: str,
        notification_type: NotificationType,
        data: Optional[Dict[str, Any]] = None,
        username: str = "Fraud Detection Bot"
    ) -> bool:
        """
        Send a notification to Discord via webhook.

        Args:
            webhook_url: Discord webhook URL
            message: Main message text
            notification_type: Type of notification for formatting
            data: Additional data to include
            username: Bot username to display

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build Discord embed
            color = {
                NotificationType.FRAUD_DETECTED: 0xdc2626,
                NotificationType.HIGH_RISK_ALERT: 0xf59e0b,
                NotificationType.BATCH_COMPLETE: 0x10b981,
                NotificationType.DAILY_SUMMARY: 0x3b82f6,
                NotificationType.SYSTEM_ALERT: 0x8b5cf6,
            }.get(notification_type, 0x6b7280)

            emoji = {
                NotificationType.FRAUD_DETECTED: "🚨",
                NotificationType.HIGH_RISK_ALERT: "⚠️",
                NotificationType.BATCH_COMPLETE: "✅",
                NotificationType.DAILY_SUMMARY: "📊",
                NotificationType.SYSTEM_ALERT: "🔔",
            }.get(notification_type, "🔔")

            embed = {
                "title": f"{emoji} {notification_type.value.replace('_', ' ').title()}",
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Fraud Detection System"
                }
            }

            # Add fields if data provided
            if data:
                fields = []
                for key, value in data.items():
                    if len(fields) < 25:  # Discord limit
                        fields.append({
                            "name": key.replace('_', ' ').title(),
                            "value": str(value),
                            "inline": True
                        })
                embed["fields"] = fields

            payload = {
                "username": username,
                "embeds": [embed]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return False

    @staticmethod
    async def notify_fraud_detected(
        webhook_url: str,
        platform: str,  # "slack" or "discord"
        transaction_id: int,
        amount: float,
        fraud_probability: float,
        risk_score: int
    ) -> bool:
        """Send fraud detection alert"""
        message = f"A fraudulent transaction has been detected!\n\nTransaction ID: `{transaction_id}`"

        data = {
            "amount": f"${amount:,.2f}",
            "fraud_probability": f"{fraud_probability * 100:.1f}%",
            "risk_score": f"{risk_score}/100",
            "severity": "CRITICAL" if risk_score >= 75 else "HIGH"
        }

        if platform.lower() == "slack":
            return await NotificationService.send_slack_notification(
                webhook_url, message, NotificationType.FRAUD_DETECTED, data
            )
        else:
            return await NotificationService.send_discord_notification(
                webhook_url, message, NotificationType.FRAUD_DETECTED, data
            )

    @staticmethod
    async def notify_batch_complete(
        webhook_url: str,
        platform: str,
        batch_id: str,
        total_transactions: int,
        fraud_count: int,
        processing_time_ms: float
    ) -> bool:
        """Send batch processing complete notification"""
        fraud_rate = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0
        message = f"Batch prediction completed successfully!\n\nBatch ID: `{batch_id[:8]}...`"

        data = {
            "total_transactions": total_transactions,
            "fraud_detected": fraud_count,
            "legitimate": total_transactions - fraud_count,
            "fraud_rate": f"{fraud_rate:.2f}%",
            "processing_time": f"{processing_time_ms:.0f}ms"
        }

        if platform.lower() == "slack":
            return await NotificationService.send_slack_notification(
                webhook_url, message, NotificationType.BATCH_COMPLETE, data
            )
        else:
            return await NotificationService.send_discord_notification(
                webhook_url, message, NotificationType.BATCH_COMPLETE, data
            )

    @staticmethod
    async def notify_daily_summary(
        webhook_url: str,
        platform: str,
        date: str,
        total_predictions: int,
        fraud_count: int,
        total_amount: float,
        avg_risk_score: float
    ) -> bool:
        """Send daily summary notification"""
        fraud_rate = (fraud_count / total_predictions * 100) if total_predictions > 0 else 0
        message = f"Daily fraud detection summary for {date}"

        data = {
            "total_predictions": total_predictions,
            "fraud_detected": fraud_count,
            "fraud_rate": f"{fraud_rate:.2f}%",
            "total_volume": f"${total_amount:,.2f}",
            "avg_risk_score": f"{avg_risk_score:.1f}"
        }

        if platform.lower() == "slack":
            return await NotificationService.send_slack_notification(
                webhook_url, message, NotificationType.DAILY_SUMMARY, data
            )
        else:
            return await NotificationService.send_discord_notification(
                webhook_url, message, NotificationType.DAILY_SUMMARY, data
            )

    @staticmethod
    async def notify_high_risk_alert(
        webhook_url: str,
        platform: str,
        message: str,
        details: Dict[str, Any]
    ) -> bool:
        """Send high risk alert notification"""
        if platform.lower() == "slack":
            return await NotificationService.send_slack_notification(
                webhook_url, message, NotificationType.HIGH_RISK_ALERT, details
            )
        else:
            return await NotificationService.send_discord_notification(
                webhook_url, message, NotificationType.HIGH_RISK_ALERT, details
            )

    @staticmethod
    async def test_webhook(
        webhook_url: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test a webhook connection"""
        message = "This is a test notification from the Fraud Detection System. Your webhook is configured correctly!"

        data = {
            "status": "Test Successful",
            "platform": platform.capitalize(),
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        try:
            if platform.lower() == "slack":
                success = await NotificationService.send_slack_notification(
                    webhook_url, message, NotificationType.SYSTEM_ALERT, data
                )
            else:
                success = await NotificationService.send_discord_notification(
                    webhook_url, message, NotificationType.SYSTEM_ALERT, data
                )

            return {
                "success": success,
                "message": "Webhook test successful!" if success else "Failed to send test message"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error testing webhook: {str(e)}"
            }
