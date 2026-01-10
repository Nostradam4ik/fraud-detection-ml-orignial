"""
Email Service - Sending emails for alerts and notifications

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    def _create_smtp_connection():
        """Create SMTP connection"""
        if not settings.smtp_user or not settings.smtp_password:
            return None

        try:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            return None

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """Send an email"""
        if not settings.smtp_user:
            logger.warning("SMTP not configured, skipping email")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
            msg["To"] = to_email

            # Add plain text version
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))

            # Add HTML version
            msg.attach(MIMEText(body_html, "html"))

            server = EmailService._create_smtp_connection()
            if server:
                server.sendmail(settings.email_from, to_email, msg.as_string())
                server.quit()
                logger.info(f"Email sent to {to_email}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str, username: str) -> bool:
        """Send password reset email"""
        reset_link = f"http://localhost:5173/reset-password?token={reset_token}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>This link will expire in 15 minutes.</p>
                    <p>If you didn't request this, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Fraud Detection ML System</p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        Hello {username},

        We received a request to reset your password.

        Click here to reset your password: {reset_link}

        This link will expire in 15 minutes.

        If you didn't request this, you can safely ignore this email.

        Fraud Detection ML System
        """

        return EmailService.send_email(to_email, "Password Reset Request", html, text)

    @staticmethod
    def send_fraud_alert_email(
        to_email: str,
        transaction_amount: float,
        fraud_probability: float,
        risk_score: int
    ) -> bool:
        """Send fraud detection alert email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ef4444; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #fef2f2; }}
                .alert-box {{ background: white; padding: 15px; border-left: 4px solid #ef4444; margin: 15px 0; }}
                .stat {{ display: inline-block; margin: 10px 20px; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #ef4444; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Fraud Alert</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <p><strong>A potentially fraudulent transaction has been detected!</strong></p>
                    </div>
                    <div style="text-align: center;">
                        <div class="stat">
                            <div class="stat-value">${transaction_amount:.2f}</div>
                            <div>Amount</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{fraud_probability*100:.1f}%</div>
                            <div>Fraud Probability</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{risk_score}</div>
                            <div>Risk Score</div>
                        </div>
                    </div>
                    <p style="text-align: center; margin-top: 20px;">
                        Please review this transaction in the Fraud Detection Dashboard.
                    </p>
                </div>
                <div class="footer">
                    <p>Fraud Detection ML System - Automated Alert</p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        FRAUD ALERT

        A potentially fraudulent transaction has been detected!

        Amount: ${transaction_amount:.2f}
        Fraud Probability: {fraud_probability*100:.1f}%
        Risk Score: {risk_score}

        Please review this transaction in the Fraud Detection Dashboard.

        Fraud Detection ML System
        """

        return EmailService.send_email(to_email, "⚠️ Fraud Alert - Action Required", html, text)

    @staticmethod
    def send_2fa_enabled_email(to_email: str, username: str) -> bool:
        """Send email when 2FA is enabled"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #22c55e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f0fdf4; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Two-Factor Authentication Enabled</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>Two-factor authentication has been successfully enabled on your account.</p>
                    <p>From now on, you'll need to enter a code from your authenticator app when logging in.</p>
                    <p>If you didn't make this change, please contact support immediately.</p>
                </div>
                <div class="footer">
                    <p>Fraud Detection ML System</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(to_email, "Two-Factor Authentication Enabled", html)

    @staticmethod
    def send_test_alert_email(to_email: str, alert_type: str, username: str) -> bool:
        """Send a test email for an alert configuration"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f0f9ff; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Test Alert</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>This is a test email for your <strong>{alert_type}</strong> alert configuration.</p>
                    <p>If you received this email, your alert is working correctly!</p>
                </div>
                <div class="footer">
                    <p>Fraud Detection ML System</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(to_email, f"Test Alert: {alert_type}", html)

    @staticmethod
    def send_daily_report_email(to_email: str, username: str, stats: dict) -> bool:
        """Send daily summary report email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #6366f1; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f5f3ff; }}
                .stat-row {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 15px; background: white; border-radius: 8px; }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: #6366f1; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Report</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>Here's your daily fraud detection summary:</p>
                    <div class="stat-row">
                        <div class="stat">
                            <div class="stat-value">{stats.get('total', 0)}</div>
                            <div>Total Predictions</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{stats.get('fraud', 0)}</div>
                            <div>Fraud Detected</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{stats.get('fraud_rate', 0)*100:.1f}%</div>
                            <div>Fraud Rate</div>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <p>Fraud Detection ML System - Daily Report</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(to_email, "📊 Daily Fraud Detection Report", html)
