import math
from dataclasses import dataclass

@dataclass
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    W: int
    H: int

def estimate_fx_from_sensor(f_mm: float, W_px: int, sensor_width_mm: float) -> float:
    return f_mm * W_px / sensor_width_mm

def scale_intrinsics(K: Intrinsics, W_new: int, H_new: int) -> Intrinsics:
    sx = W_new / K.W
    sy = H_new / K.H
    return Intrinsics(
        fx=K.fx * sx,
        fy=K.fy * sy,
        cx=K.cx * sx,
        cy=K.cy * sy,
        W=W_new,
        H=H_new
    )

def monocular_distance_and_xyz(
    K: Intrinsics,
    bbox_xyxy,          # (x1,y1,x2,y2) in pixels
    real_H_m: float,    # target real height (m), here 0.4
    use_bottom_point: bool = True
):
    x1, y1, x2, y2 = bbox_xyxy
    h = max(1.0, (y2 - y1))  # bbox height in pixels, avoid div0

    # Depth (meters)
    Z = K.fy * real_H_m / h

    # choose image point
    u = (x1 + x2) / 2.0
    v = (y2 if use_bottom_point else (y1 + y2) / 2.0)

    # Camera-frame coordinates (meters)
    X = (u - K.cx) * Z / K.fx
    Y = (v - K.cy) * Z / K.fy
    return X, Y, Z

if __name__ == "__main__":
    # --- given camera info ---
    f_mm = 2.8
    W0, H0 = 1920, 1080
    sensor_width_mm = 5.0  # 1/2.9" common approx

    fx0 = estimate_fx_from_sensor(f_mm, W0, sensor_width_mm)
    fy0 = fx0  # recommended
    K0 = Intrinsics(fx=fx0, fy=fy0, cx=W0/2, cy=H0/2, W=W0, H=H0)

    print("K0:", K0)

    # --- if your YOLO runs on resized frames (example 640x480) ---
    # If you run YOLO on original 1920x1080, skip this and use K0 directly.
    W1, H1 = 640, 480
    K1 = scale_intrinsics(K0, W1, H1)

    # --- example bbox in the same resolution as K1 expects ---
    bbox = (220, 120, 360, 420)  # x1,y1,x2,y2 on 640x480 frame
    real_H_m = 0.4

    X, Y, Z = monocular_distance_and_xyz(K1, bbox, real_H_m, use_bottom_point=True)
    print(f"Estimated distance Z={Z:.2f} m, X={X:.2f} m, Y={Y:.2f} m")
