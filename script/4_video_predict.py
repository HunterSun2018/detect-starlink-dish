import cv2
import time
from collections import deque
from ultralytics import YOLO

model = YOLO("runs/detect/train7/weights/best.pt")  # 你的 best.pt
# cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live?rtsp_transport=tcp",  cv2.CAP_FFMPEG)  # 或 0 / "video.mp4"
cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live")
# 降低延迟：尽量让缓冲变小（不同后端支持不同）
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# ===== FPS 统计 =====
fps_window = deque(maxlen=30)   # 30 帧滑动窗口
last_time = time.time()

while True:
    ok, frame = cap.read()
    if not ok:
        continue
    

    # 推理
    #frame_480x640 = cv2.resize(frame, (640, 480))  # (width, height)
    #results = model.predict(frame_480x640, conf=0.25, iou=0.7, verbose=False)
    
    results = model.predict(frame, imgsz=(640,480), conf=0.25, iou=0.7, verbose=False)

    # 画框（ultralytics 自带 plot）
    annotated = results[0].plot()
    
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
    
    cv2.imshow("YOLO Stream", annotated)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

