
1. exprot model with torchscript format
```
yolo export model=runs/detect/train7/weights/best.pt format=torchscript imgsz=640
```

2. convert to pnnx format
```
pnnx best.torchscript
```

#扫描IP
```
sudo nmap -sn 192.168.0.0/24
```

#播放视频流
```
ffplay rtsp://admin:admin@192.168.0.15:554/live
```