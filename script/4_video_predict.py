import cv2
import time
from collections import deque
from ultralytics import YOLO
import Intrinsics as intr
import locating

 # --- given camera info ---
f_mm = 2.8
W0, H0 = 1920, 1080
sensor_width_mm = 5.0  # 1/2.9" common approx

fx0 = intr.estimate_fx_from_sensor(f_mm, W0, sensor_width_mm)
fy0 = fx0  # recommended
K0 = intr.Intrinsics(fx=fx0, fy=fy0, cx=W0/2, cy=H0/2, W=W0, H=H0)

print("K0:", K0)
# If you run YOLO on original 1920x1080, skip this and use K0 directly.
W1, H1 = 640, 480
K1 = intr.scale_intrinsics(K0, W1, H1)

# Starlink size
real_H_m = 0.4


model = YOLO("runs/detect/train7/weights/best.pt")  # 你的 best.pt
cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live?rtsp_transport=tcp",  cv2.CAP_FFMPEG)  # 或 0 / "video.mp4"
# cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live"+ "?fflags=discardcorrupt", cv2.CAP_FFMPEG)  # 丢弃损坏帧，降低延迟
# 降低延迟：尽量让缓冲变小（不同后端支持不同）
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
# cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP) 
# cap.set(cv2.CAP_PROP_TIMEOUT, 3000) 

# ===== FPS 统计 =====
fps_window = deque(maxlen=30)   # 30 帧滑动窗口
last_time = time.time()

while True:
    ok, frame = cap.read()
    if not ok:
        continue
    

    # 推理    
    results = model.predict(frame, imgsz=(640,480), conf=0.25, iou=0.7, verbose=False)

    # 画框（ultralytics 自带 plot）
    annotated = results[0].plot()
    
    # X, Y, Z = intr.monocular_distance_and_xyz(K1, results[0], real_H_m, use_bottom_point=True)
    boxes = results[0].boxes
    if boxes is not None and len(boxes) > 0:
        import cv2
        xyxy = boxes.xyxy.cpu().numpy()  # (N,4)

        for bbox in xyxy:
            x1, y1, x2, y2 = bbox

            # # 调用单框函数
            # X, Y, Z = intr.monocular_distance_and_xyz(
            #     K0,
            #     (x1, y1, x2, y2),
            #     real_H_m,
            #     use_bottom_point=True
            # )
            
            # 你可以替换成实际的姿态数据NEU，这里假设相机水平放置，没有旋转
            yaw_rad=pitch_rad=roll_rad=0.0            
            
            # # ---- Fake camera GPS ----
            lat0, lon0, alt0 = 37.0, -122.0, 10.0
                
            result = locating.monocular_gps_from_bbox(
                lat0, lon0, alt0,
                yaw_rad, pitch_rad, roll_rad,
                K0.fx, K0.fy, K0.cx, K0.cy,                
                bbox,   # (x1, y1, x2, y2),
                real_H=real_H_m
            )
            
            # 构造显示文本
            #text = f"X={X:.2f}m Y={Y:.2f}m Z={Z:.2f}m"            
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
            cv2.putText(
                annotated,
                text,
                (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )

    # ===== FPS 计算 =====
    now = time.time()
    fps_window.append(now - last_time)
    last_time = now

    if len(fps_window) > 0:
        fps = len(fps_window) / sum(fps_window)
    else:
        fps = 0.0

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
    
    # x = results[0].x
    # y = results[0].y - 10

    cv2.imshow("YOLO Stream", annotated)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

