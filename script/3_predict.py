# scripts/3_predict.py
from __future__ import annotations
from pathlib import Path
import sys
from ultralytics import YOLO
import cv2
import time
import Intrinsics as intr
import locating

 # --- given camera info ---
f_mm = 2.8
W0, H0 = 1920, 1080
sensor_width_mm = 5.0  # 1/2.9" common approx

fx0 = intr.estimate_fx_from_sensor(f_mm, W0, sensor_width_mm)
fy0 = fx0  # recommended
K0 = intr.Intrinsics(fx=fx0, fy=fy0, cx=W0/2, cy=H0/2, W=W0, H=H0)

real_H_m = 0.4
#  ---- Fake camera GPS and attitude (replace with real data from UDP) ----
lat0, lon0, alt0 = 41.17228, 114.87902, 1462.7
# 替换成实际的姿态数据，这里假设相机水平放置，没有旋转
yaw_rad=pitch_rad=roll_rad=0.0

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BEST_PT = PROJECT_ROOT / "runs" / "detect" / "train8" / "weights" / "best.pt"

def main():
    model = YOLO(str(BEST_PT))

    arguments = sys.argv[1:]
    if len(arguments) > 0:
        sample = arguments[0]
    else:
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
    
    # ===== FPS 统计 =====    
        
    # 创建一个可调整大小的窗口
    window_title = "YOLO Stream"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    # 设置窗口大小为 1024x768
    cv2.resizeWindow(window_title, 1270, 768)
    
    # 画框（ultralytics 自带 plot）
    annotated = results[0].plot()
    
    boxes = results[0].boxes
    
    if boxes is not None and len(boxes) > 0:
        
        xyxy = boxes.xyxy.cpu().numpy()  # (N,4)

        for bbox in xyxy:
            x1, y1, x2, y2 = bbox           
                
            result = locating.monocular_gps_from_bbox(
                lat0, lon0, alt0,
                yaw_rad, pitch_rad, roll_rad,
                K0.fx, K0.fy, K0.cx, K0.cy,                
                bbox,   # (x1, y1, x2, y2),
                real_H=real_H_m
            )
            
            # 更新全局 Starlink 位置
            global sld_gps
            sld_gps = result['gps']           
            
            # 构造显示文本
            text = f"lat={result['gps'][0]:.2f} lon={result['gps'][1]:.2f} alt={result['gps'][2]:.2f}m Z={result['Z_m']:.2f}m"
            

            # 文本位置（框左上角上方）
            tx = int(x1)
            ty = int(y1) - 50  # 往上挪一点，避免遮挡框

            # 防止文字超出图像
            if ty < 20:
                ty = int(y1) + 20

            # 画黑色背景增强可读性
            (tw, th), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 1
            )

            cv2.rectangle(
                annotated,
                (tx, ty - th - baseline),
                (tx + tw, ty + baseline),
                (0, 0, 0),
                -1
            )

            # 写文字
            cv2.putText(annotated, text,
                (tx, ty), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, (0, 255, 0), 1,
                cv2.LINE_AA)

    # ===== FPS 计算 =====        
    fps = 30.0

    # ===== 画 FPS =====
    cv2.putText(
        annotated,
        f"FPS: {fps:.2f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )            
    
    cv2.imshow(window_title, annotated)
    
    cv2.imwrite('output_image.jpg', annotated)
            
    # cv2.waitKey(1)  # 必须调用，才能刷新显示窗口
            
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

