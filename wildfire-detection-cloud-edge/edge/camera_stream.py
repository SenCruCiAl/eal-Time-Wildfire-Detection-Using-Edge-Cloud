"""Real-time camera stream processing loop for wildfire detection at the edge."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import cv2

from send_event_to_cloud import CloudEventSender
from yolo_inference import WildfireDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("edge.camera_stream")


def build_event(device_id: str, frame_id: int, detection: Dict[str, Any]) -> Dict[str, Any]:
    """Construct cloud event payload for a single wildfire detection."""
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frame_id": frame_id,
        "confidence": detection["confidence"],
        "label": detection["label"],
        "bbox": detection["bbox"],
    }


def main() -> None:
    device_id = os.getenv("EDGE_DEVICE_ID", "edge-cam-001")
    camera_index = int(os.getenv("CAMERA_INDEX", "0"))
    display_window = os.getenv("DISPLAY_WINDOW", "false").lower() == "true"

    detector = WildfireDetector()
    sender = CloudEventSender()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open camera index {camera_index}")

    logger.info("Starting realtime wildfire detection loop on device=%s", device_id)

    frame_id = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("No frame read from camera; retrying...")
                time.sleep(0.2)
                continue

            detections = detector.infer(frame)
            for detection in detections:
                event = build_event(device_id, frame_id, detection)
                sender.send_event(event)
                logger.info(
                    "Wildfire event emitted | frame=%s confidence=%.3f bbox=%s",
                    frame_id,
                    detection["confidence"],
                    detection["bbox"],
                )

                x1, y1, x2, y2 = detection["bbox"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    f"{detection['label']} {detection['confidence']:.2f}",
                    (x1, max(y1 - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )

            if display_window:
                cv2.imshow("Wildfire Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            frame_id += 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down edge pipeline.")
    finally:
        cap.release()
        sender.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
