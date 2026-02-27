import cv2
import time
import queue
import threading
from collections import deque
from ultralytics import YOLO

import Intrinsics as intr
import locating
import server


# 线程安全的队列，用于视频帧传递
q=queue.Queue()

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

# the  real size of Starlink dish 
real_H_m = 0.4

#  ---- Fake camera GPS and attitude (replace with real data from UDP) ----
lat0, lon0, alt0 = 37.0, -122.0, 10.0
# 替换成实际的姿态数据，这里假设相机水平放置，没有旋转
yaw_rad=pitch_rad=roll_rad=0.0

#  线程间的锁，保护共享的 GPS 和姿态数据
lock = threading.Lock()

#  加载 YOLO 模型
model = YOLO("runs/detect/train7/weights/best.pt")  # best.pt

# 线程间的终止信号
terminated = False

#
#   接收线程：负责从 RTSP 流读取视频帧，并放入队列
#    
def Receive():
    print("start Reveive")
    
    cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live?rtsp_transport=tcp",  cv2.CAP_FFMPEG)
    # cap = cv2.VideoCapture("rtsp://admin:admin@192.168.0.15:554/live"+ "?fflags=discardcorrupt", cv2.CAP_FFMPEG)  # 丢弃损坏帧，降低延迟
    # 降低延迟：尽量让缓冲变小（不同后端支持不同）
    # cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    ret = True
    while ret:
        if terminated:  
            break
        
        ret, frame = cap.read()
        q.put(frame)
             
    cap.release()
    
#
#   显示线程：负责从队列获取视频帧，进行 YOLO 推理和定位计算，并显示结果
#
def Display():
    print("Start Displaying")
    
    # ===== FPS 统计 =====
    fps_window = deque(maxlen=30)   # 30 帧滑动窗口
    last_time = time.time()
    
    while True:
        
        global terminated        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            terminated = True
            break   
        
        if not q.empty():            
        
            frame=q.get()

            # 推理    
            results = model.predict(frame, imgsz=(640,480), conf=0.25, iou=0.7, verbose=False)

            # 画框（ultralytics 自带 plot）
            annotated = results[0].plot()
                        
            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                
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
                    with lock:
                        lat0_copy, lon0_copy, alt0_copy = lat0, lon0, alt0
                        yaw_rad_copy, pitch_rad_copy, roll_rad_copy = yaw_rad, pitch_rad, roll_rad
                        
                    result = locating.monocular_gps_from_bbox(
                        lat0_copy, lon0_copy, alt0_copy,
                        yaw_rad_copy, pitch_rad_copy, roll_rad_copy,
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

            cv2.imshow("YOLO Stream", annotated)
            
    
    print("Release cv2 resources")
    
    cv2.destroyAllWindows()    

#
#   UDP 服务器回调接口：负责接收 GPS 和姿态数据更新
#
def onUpdatePose(msg):
    global lat0, lon0, alt0, yaw_rad, pitch_rad, roll_rad
    
    with lock:
        lat0 = msg['lat0']
        lon0 = msg['lon0']
        alt0 = msg['alt0']
        yaw_rad = msg['yaw_rad']
        pitch_rad = msg['pitch_rad']
        roll_rad = msg['roll_rad']

    print(f"Received position update: lat={lat0:.2f}, lon={lon0:.2f}, alt={alt0:.2f}, yaw={yaw_rad:.2f}, pitch={pitch_rad:.2f}, roll={roll_rad:.2f}")
        
#
#   主线程：启动接收和显示线程，并等待它们结束
#            
if __name__=='__main__':
        
    p1 = threading.Thread(target=Receive)
    p2 = threading.Thread(target=Display)
    p3 = threading.Thread(target=server.run_udp_server, kwargs={"bind_ip": "0.0.0.0", "port": 9000, "onUpdatePos": onUpdatePose})
    
    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
    
    print("Program terminated gracefully.")
    