"""Azure Function handler that processes wildfire telemetry and dispatches alerts."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import azure.functions as func
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient

logger = logging.getLogger("azure_function_alert")


def send_email_alert(subject: str, body: str) -> None:
    """Send email alert via SendGrid."""
    api_key = os.getenv("SENDGRID_API_KEY", "")
    sender = os.getenv("ALERT_EMAIL_FROM", "")
    recipient = os.getenv("ALERT_EMAIL_TO", "")

    if not (api_key and sender and recipient):
        logger.warning("Email configuration missing; skipping email alert.")
        return

    message = Mail(from_email=sender, to_emails=recipient, subject=subject, plain_text_content=body)
    response = SendGridAPIClient(api_key).send(message)
    logger.info("Email alert sent. status=%s", response.status_code)


def send_sms_alert(body: str) -> None:
    """Send optional SMS alert via Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    to_number = os.getenv("TWILIO_TO_NUMBER", "")

    if not (account_sid and auth_token and from_number and to_number):
        logger.info("SMS configuration missing; skipping SMS alert.")
        return

    client = TwilioClient(account_sid, auth_token)
    sms = client.messages.create(body=body, from_=from_number, to=to_number)
    logger.info("SMS alert sent. sid=%s", sms.sid)


def parse_event(event: func.EventHubEvent) -> Dict[str, Any]:
    """Parse EventHub payload from IoT Hub routed message."""
    payload_bytes = event.get_body()
    payload_str = payload_bytes.decode("utf-8") if isinstance(payload_bytes, bytes) else str(payload_bytes)
    return json.loads(payload_str)


def main(event: func.EventHubEvent) -> None:
    """Azure Function entry point for wildfire event processing."""
    data = parse_event(event)
    timestamp = data.get("timestamp", "unknown-time")
    confidence = data.get("confidence", 0)

    message = f"Wildfire detected at {timestamp}. Confidence: {confidence}"
    logger.warning(message)

    send_email_alert("Wildfire Detection Alert", message)
    send_sms_alert(message)
