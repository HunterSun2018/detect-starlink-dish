from ultralytics import YOLO

# Load a pretrained YOLO26n model
model = YOLO("runs/detect/train4/weights/best.pt")

# Single stream with batch-size 1 inference
source = "rtsp://admin:admin@192.168.0.15:554/live"  # RTSP, RTMP, TCP, or IP streaming address

# Run inference on the source
results = model(source, stream=True)  # generator of Results objects
