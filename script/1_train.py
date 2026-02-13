# scripts/1_train.py
from __future__ import annotations
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = PROJECT_ROOT / "starlink.yaml"

def main():
    # 选择一个预训练权重开始 fine-tune：yolov8n.pt（最轻量）
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=16,          # 显存不足可调小：8/4
        device="cpu",          # 无GPU改为 "cpu"
        workers=8,
        pretrained=True,
        # 常用可调项：
        # lr0=0.01, lrf=0.01,
        # mosaic=1.0, mixup=0.0,
        # patience=30
    )
    print(results)

if __name__ == "__main__":
    main()

