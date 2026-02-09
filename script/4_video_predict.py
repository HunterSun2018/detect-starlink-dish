import cv2
from ultralytics import YOLO

model = YOLO("runs/detect/train7/weights/best.pt")  # 你的 best.pt
cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live")  # 或 0 / "video.mp4"

# 降低延迟：尽量让缓冲变小（不同后端支持不同）
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    

    # 推理
    #frame_480x640 = cv2.resize(frame, (640, 480))  # (width, height)
    #results = model.predict(frame_480x640, conf=0.25, iou=0.7, verbose=False)
    
    results = model.predict(frame, imgsz=(640,480), conf=0.25, iou=0.7, verbose=False)

    # 画框（ultralytics 自带 plot）
    annotated = results[0].plot()

    cv2.imshow("YOLO Stream", annotated)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

