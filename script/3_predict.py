# scripts/3_predict.py
from __future__ import annotations
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BEST_PT = PROJECT_ROOT / "runs" / "detect" / "train4" / "weights" / "best.pt"

def main():
    model = YOLO(str(BEST_PT))

    # 你可以换成任意图片路径/目录
    sample = PROJECT_ROOT / "data" / "camera002.jpg"
    results = model.predict(
        source=str(sample),
        imgsz=640,
        conf=0.25,
        iou=0.7,
        device='cpu',
        save=True
    )
    print(f"Pred done, got {len(results)} results.")

if __name__ == "__main__":
    main()

