"""Dataset helper utilities for wildfire YOLO training."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("ml.dataset_loader")


def build_dataset_yaml(dataset_root: Path, output_path: Path, class_map: Dict[int, str]) -> Path:
    """Create a YOLOv8 dataset yaml from a standard folder layout."""
    data = {
        "path": str(dataset_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": class_map,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)

    logger.info("Dataset YAML created at %s", output_path)
    return output_path


def parse_class_map(raw_value: str) -> Dict[int, str]:
    """Parse class map from format: '0:fire,1:smoke'."""
    items = [item.strip() for item in raw_value.split(",") if item.strip()]
    class_map: Dict[int, str] = {}
    for item in items:
        key, value = item.split(":", maxsplit=1)
        class_map[int(key)] = value.strip()
    return class_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate YOLO dataset config for wildfire datasets")
    parser.add_argument("--dataset-root", required=True, help="Dataset root containing images/ and labels/ folders")
    parser.add_argument("--output", default="data/wildfire.yaml", help="Output path for generated yaml")
    parser.add_argument("--classes", default="0:fire,1:smoke", help="Class map like '0:fire,1:smoke'")

    args = parser.parse_args()
    dataset_root = Path(args.dataset_root)
    output_file = Path(args.output)

    class_map = parse_class_map(args.classes)
    build_dataset_yaml(dataset_root, output_file, class_map)


if __name__ == "__main__":
    main()
