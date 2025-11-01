"""
Notification Service

Sends email notifications for important streak and gem balance events.
Supports SMTP-based email delivery (Gmail, SendGrid, etc.)
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Handles email notifications for streak automation events.

    Supports SMTP email delivery with customizable templates.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        recipient_email: str,
        enabled: bool = True
    ):
        """
        Initialize the notification service.

        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (usually 587 for TLS)
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            recipient_email: Email address to receive notifications
            enabled: Whether notifications are enabled
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.recipient_email = recipient_email
        self.enabled = enabled

        if not self.enabled:
            logger.info("Email notifications are disabled")

    def _send_email(self, subject: str, body_html: str, body_text: str):
        """
        Send an email via SMTP.

        Args:
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (fallback)
        """
        if not self.enabled:
            logger.debug(f"[Notifications Disabled] Would send: {subject}")
            return

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.smtp_username
            message["To"] = self.recipient_email
            message["Subject"] = subject

            # Attach both plain text and HTML versions
            part_text = MIMEText(body_text, "plain")
            part_html = MIMEText(body_html, "html")

            message.attach(part_text)
            message.attach(part_html)

            # Connect and send
            logger.info(f"Sending email notification: {subject}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info("✓ Email notification sent successfully")

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")

    def send_low_gems_warning(self, current_gems: int, threshold: int):
        """
        Send warning that gem balance is running low.

        Args:
            current_gems: Current gem count
            threshold: Low gems threshold
        """
        subject = "⚠️ Duolingo Gems Running Low"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #ff9600;">⚠️ Low Gems Warning</h2>
            <p>Your Duolingo gem balance is running low.</p>

            <div style="background-color: #fff3cd; border-left: 4px solid #ff9600; padding: 15px; margin: 20px 0;">
                <strong>Current Balance:</strong> {current_gems} 💎<br>
                <strong>Warning Threshold:</strong> {threshold} 💎
            </div>

            <p>You may not have enough gems to purchase streak freezes soon.
            Consider earning more gems through lessons to maintain your streak protection.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from your Duo Streak Keeper.
            </p>
        </body>
        </html>
        """

        body_text = f"""
⚠️ Low Gems Warning

Your Duolingo gem balance is running low.

Current Balance: {current_gems} gems
Warning Threshold: {threshold} gems

You may not have enough gems to purchase streak freezes soon.
Consider earning more gems through lessons to maintain your streak protection.

---
This is an automated notification from your Duo Streak Keeper.
        """

        self._send_email(subject, body_html, body_text)

    def send_out_of_gems_alert(self, current_gems: int, required_gems: int):
        """
        Send critical alert that user is out of gems.

        Args:
            current_gems: Current gem count
            required_gems: Gems needed for streak freeze
        """
        subject = "🚨 Out of Gems - Streak At Risk!"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #dc3545;">🚨 Critical: Out of Gems</h2>
            <p><strong>You do not have enough gems to purchase a streak freeze!</strong></p>

            <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                <strong>Current Balance:</strong> {current_gems} 💎<br>
                <strong>Required:</strong> {required_gems} 💎<br>
                <strong>Shortage:</strong> {required_gems - current_gems} 💎
            </div>

            <p><strong>Your streak is at risk!</strong> The automation service cannot purchase
            streak freezes without sufficient gems.</p>

            <h3>What to do:</h3>
            <ol>
                <li>Complete Duolingo lessons to earn gems</li>
                <li>Check your streak freeze inventory manually</li>
                <li>Consider Duolingo Super for automatic streak repair</li>
            </ol>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from your Duo Streak Keeper.<br>
                Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </body>
        </html>
        """

        body_text = f"""
🚨 Critical: Out of Gems

You do not have enough gems to purchase a streak freeze!

Current Balance: {current_gems} gems
Required: {required_gems} gems
Shortage: {required_gems - current_gems} gems

Your streak is at risk! The automation service cannot purchase
streak freezes without sufficient gems.

What to do:
1. Complete Duolingo lessons to earn gems
2. Check your streak freeze inventory manually
3. Consider Duolingo Super for automatic streak repair

---
This is an automated notification from your Duo Streak Keeper.
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        self._send_email(subject, body_html, body_text)

    def send_purchase_success(self, gems_remaining: int):
        """
        Send notification that streak freeze was successfully purchased.

        Args:
            gems_remaining: Gems remaining after purchase
        """
        subject = "✅ Streak Freeze Purchased Successfully"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #28a745;">✅ Success!</h2>
            <p>A streak freeze has been successfully purchased and equipped.</p>

            <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;">
                <strong>Cost:</strong> 200 💎<br>
                <strong>Remaining Balance:</strong> {gems_remaining} 💎
            </div>

            <p>Your Duolingo streak is now protected. If you miss a day,
            the streak freeze will automatically maintain your streak.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from your Duo Streak Keeper.<br>
                Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </body>
        </html>
        """

        body_text = f"""
✅ Success!

A streak freeze has been successfully purchased and equipped.

Cost: 200 gems
Remaining Balance: {gems_remaining} gems

Your Duolingo streak is now protected. If you miss a day,
the streak freeze will automatically maintain your streak.

---
This is an automated notification from your Duo Streak Keeper.
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        self._send_email(subject, body_html, body_text)

    def send_streak_broken_alert(self):
        """Send alert that the streak has been broken."""
        subject = "💔 Duolingo Streak Broken"

        body_html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #dc3545;">💔 Streak Broken</h2>
            <p>Unfortunately, your Duolingo streak has been broken.</p>

            <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                <strong>Status:</strong> Streak reset to 0 days
            </div>

            <p>This may have happened due to:</p>
            <ul>
                <li>Insufficient gems to purchase a streak freeze</li>
                <li>No streak freeze equipped when a day was missed</li>
                <li>API connectivity issues</li>
            </ul>

            <p>You can start building your streak again by completing a lesson today!</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from your Duo Streak Keeper.
            </p>
        </body>
        </html>
        """

        body_text = """
💔 Streak Broken

Unfortunately, your Duolingo streak has been broken.

Status: Streak reset to 0 days

This may have happened due to:
- Insufficient gems to purchase a streak freeze
- No streak freeze equipped when a day was missed
- API connectivity issues

You can start building your streak again by completing a lesson today!

---
This is an automated notification from your Duo Streak Keeper.
        """

        self._send_email(subject, body_html, body_text)

    def send_error_notification(self, error_message: str):
        """
        Send notification about a system error.

        Args:
            error_message: Description of the error
        """
        subject = "❌ Duo Streak Keeper Error"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #dc3545;">❌ System Error</h2>
            <p>An error occurred in your Duo Streak Keeper automation:</p>

            <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-family: monospace;">
                {error_message}
            </div>

            <p>The automation may not function correctly until this is resolved.
            Please check your configuration and credentials.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from your Duo Streak Keeper.<br>
                Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </body>
        </html>
        """

        body_text = f"""
❌ System Error

An error occurred in your Duo Streak Keeper automation:

{error_message}

The automation may not function correctly until this is resolved.
Please check your configuration and credentials.

---
This is an automated notification from your Duo Streak Keeper.
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        self._send_email(subject, body_html, body_text)
