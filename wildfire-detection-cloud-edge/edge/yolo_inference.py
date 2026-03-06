"""YOLOv8 wildfire detector for edge inference."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from ultralytics import YOLO

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """Inference configuration for wildfire detection."""

    model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    fire_conf_threshold: float = float(os.getenv("FIRE_CONFIDENCE_THRESHOLD", "0.6"))
    image_size: int = int(os.getenv("YOLO_IMAGE_SIZE", "640"))


class WildfireDetector:
    """Encapsulates YOLOv8 model loading and fire inference."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self.model = YOLO(self.config.model_path)
        logger.info("YOLO model loaded from %s", self.config.model_path)

    def infer(self, frame: Any) -> List[Dict[str, Any]]:
        """Run inference on a frame and return filtered fire detections."""
        results = self.model.predict(source=frame, imgsz=self.config.image_size, verbose=False)

        detections: List[Dict[str, Any]] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_idx = int(box.cls[0].item())
                class_name = names.get(class_idx, str(class_idx)).lower()
                confidence = float(box.conf[0].item())

                # Simple wildfire/fire class filtering to support custom models.
                if class_name in {"fire", "wildfire", "smoke"} and confidence >= self.config.fire_conf_threshold:
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    detections.append(
                        {
                            "label": class_name,
                            "confidence": confidence,
                            "bbox": [x1, y1, x2, y2],
                        }
                    )

        logger.debug("Detections found: %d", len(detections))
        return detections
