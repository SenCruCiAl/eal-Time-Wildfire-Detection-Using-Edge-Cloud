"""Secure cloud event sender for wildfire detections.

Supports Azure IoT Hub telemetry publishing and a generic HTTPS webhook fallback.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import requests
from azure.iot.device import IoTHubDeviceClient, Message

logger = logging.getLogger(__name__)


class CloudEventSender:
    """Send wildfire detection events from edge to cloud securely."""

    def __init__(self) -> None:
        self.transport = os.getenv("EDGE_CLOUD_TRANSPORT", "iot").lower()
        self.iot_client: IoTHubDeviceClient | None = None
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")

        if self.transport == "iot":
            connection_string = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING", "")
            if not connection_string:
                raise ValueError("IOTHUB_DEVICE_CONNECTION_STRING is required for IoT Hub transport")

            # Azure SDK uses TLS by default for secure communication.
            self.iot_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
            self.iot_client.connect()
            logger.info("Connected to Azure IoT Hub successfully.")

        elif self.transport == "http":
            if not self.webhook_url:
                raise ValueError("ALERT_WEBHOOK_URL is required for HTTP transport")
            logger.info("Configured HTTP cloud transport.")

        else:
            raise ValueError("EDGE_CLOUD_TRANSPORT must be 'iot' or 'http'")

    def send_event(self, event_data: Dict[str, Any]) -> None:
        """Send wildfire detection event payload to cloud destination."""
        payload = json.dumps(event_data)

        if self.transport == "iot" and self.iot_client:
            message = Message(payload)
            message.content_type = "application/json"
            message.content_encoding = "utf-8"
            message.custom_properties["eventType"] = "wildfireDetection"
            self.iot_client.send_message(message)
            logger.info("Wildfire event sent to IoT Hub: %s", payload)
            return

        if self.transport == "http":
            response = requests.post(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            response.raise_for_status()
            logger.info("Wildfire event sent via HTTPS webhook: status=%s", response.status_code)

    def close(self) -> None:
        """Close active cloud client resources."""
        if self.iot_client:
            self.iot_client.shutdown()
            logger.info("IoT Hub client connection closed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    sender = CloudEventSender()
    sender.send_event(
        {
            "device_id": os.getenv("EDGE_DEVICE_ID", "edge-cam-001"),
            "timestamp": "2026-01-01T00:00:00Z",
            "confidence": 0.92,
            "bbox": [100, 120, 300, 400],
            "frame_id": 1,
        }
    )
    sender.close()
