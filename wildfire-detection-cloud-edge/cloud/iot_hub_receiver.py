"""Utility receiver to read IoT Hub telemetry from Event Hub-compatible endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
import os

from azure.eventhub.aio import EventHubConsumerClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("cloud.iot_hub_receiver")


def on_event(partition_context, event) -> None:
    """Process received events for monitoring/debugging in cloud layer."""
    try:
        payload = json.loads(event.body_as_str(encoding="UTF-8"))
    except json.JSONDecodeError:
        payload = {"raw": event.body_as_str(encoding="UTF-8")}

    logger.info(
        "Received telemetry | partition=%s sequence=%s payload=%s",
        partition_context.partition_id,
        event.sequence_number,
        payload,
    )

    partition_context.update_checkpoint(event)


async def main() -> None:
    """Listen continuously for telemetry sent by edge devices."""
    connection_str = os.getenv("IOTHUB_EVENTHUB_CONNECTION_STRING", "")
    consumer_group = os.getenv("EVENTHUB_CONSUMER_GROUP", "$Default")

    if not connection_str:
        raise ValueError("IOTHUB_EVENTHUB_CONNECTION_STRING is required")

    client = EventHubConsumerClient.from_connection_string(
        conn_str=connection_str,
        consumer_group=consumer_group,
    )

    async with client:
        logger.info("Listening for IoT Hub events with consumer group=%s", consumer_group)
        await client.receive(on_event=on_event, starting_position="-1")


if __name__ == "__main__":
    asyncio.run(main())
