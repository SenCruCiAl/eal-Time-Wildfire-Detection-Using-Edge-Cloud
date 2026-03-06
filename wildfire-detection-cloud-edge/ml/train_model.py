"""Training pipeline script for YOLOv8 wildfire detection.

Can run locally or inside Azure ML jobs.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("ml.train_model")


def train(
    data_config: str,
    model_name: str,
    epochs: int,
    imgsz: int,
    batch: int,
    project_dir: str,
    run_name: str,
) -> Path:
    """Train a YOLOv8 model on wildfire dataset and return best weights path."""
    model = YOLO(model_name)
    logger.info("Starting training model=%s data=%s epochs=%s", model_name, data_config, epochs)

    results = model.train(
        data=data_config,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project_dir,
        name=run_name,
        pretrained=True,
        device="cpu",  # For portability; override via ULTRALYTICS_DEVICE if needed.
    )

    best_model = Path(results.save_dir) / "weights" / "best.pt"
    logger.info("Training complete. Best model path: %s", best_model)
    return best_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8 wildfire detector")
    parser.add_argument("--data", required=True, help="Path to YOLO dataset yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base YOLO model checkpoint")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default="runs/train")
    parser.add_argument("--name", default="wildfire-yolov8")

    args = parser.parse_args()
    train(args.data, args.model, args.epochs, args.imgsz, args.batch, args.project, args.name)


if __name__ == "__main__":
    main()
