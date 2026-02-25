import numpy as np

R_EARTH = 6378137.0

def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], float)

def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]], float)

def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]], float)

def cam_to_enu_rotation(yaw, pitch, roll):
    # R = R_yaw(U/z) * R_pitch(E/x) * R_roll(N/y) * R0
    R0 = np.array([[1, 0, 0],
                   [0, 0, 1],
                   [0,-1, 0]], float)
    return rot_z(yaw) @ rot_x(pitch) @ rot_y(roll) @ R0

def bbox_to_cam_point(fx, fy, cx, cy, bbox_xyxy, real_H=0.4, use_bottom=True):
    x1,y1,x2,y2 = bbox_xyxy
    h = max(1.0, (y2-y1))
    Z = fy * real_H / h
    u = 0.5*(x1+x2)
    v = y2 if use_bottom else 0.5*(y1+y2)
    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy
    return np.array([X,Y,Z], float), Z

def enu_to_gps(lat0_deg, lon0_deg, alt0_m, E, N, U):
    lat0 = np.deg2rad(lat0_deg)
    dlat = N / R_EARTH
    dlon = E / (R_EARTH * np.cos(lat0))
    return lat0_deg + np.rad2deg(dlat), lon0_deg + np.rad2deg(dlon), alt0_m + U

def monocular_gps_from_bbox(lat0, lon0, alt0, yaw, pitch, roll, fx, fy, cx, cy, bbox, H=0.4):
    Pc, Z = bbox_to_cam_point(fx, fy, cx, cy, bbox, real_H=H, use_bottom=True)
    R = cam_to_enu_rotation(yaw, pitch, roll)
    Penu = R @ Pc
    gps = enu_to_gps(lat0, lon0, alt0, *Penu)
    return Z, Penu, gps

def assert_close(a, b, tol=1e-6, msg=""):
    if abs(a-b) > tol:
        raise AssertionError(f"{msg} | {a} vs {b} (tol={tol})")

def main():
    # ---- Camera intrinsics (example) ----
    W, Himg = 1920, 1080
    fx, fy = 1500.0, 1500.0   # 你可替换成你的估算/标定值
    cx, cy = W/2, Himg/2

    # ---- Fake camera GPS ----
    lat0, lon0, alt0 = 37.0, -122.0, 10.0

    # ---- Build a bbox whose bottom-center is at (cx,cy) and height gives a known Z ----
    real_obj_H = 0.4
    target_Z = 20.0
    hpx = fy * real_obj_H / target_Z
    # bottom v = cy, so y2=cy, y1=cy-hpx
    bbox_center = (cx, cy - hpx, cx, cy)  # x1=x2=cx makes width=0 but ok for center test

    # Test 1: zero pose -> forward maps to North
    yaw=pitch=roll=0.0
    Z, Penu, gps = monocular_gps_from_bbox(lat0, lon0, alt0, yaw, pitch, roll, fx, fy, cx, cy, bbox_center, H=real_obj_H)
    print("Test1 Z, ENU:", Z, Penu)
    assert_close(Penu[0], 0.0, 1e-6, "E should be ~0 at image center")
    assert_close(Penu[2], 0.0, 1e-6, "U should be ~0 at image center (v=cy)")
    if not (Penu[1] > 0):
        raise AssertionError("N should be >0 at image center (forward)")

    # Test 2: yaw +90 deg -> forward should go East OR West (depending on sign convention)
    yaw=np.deg2rad(90.0); pitch=0.0; roll=0.0
    Z, Penu, gps = monocular_gps_from_bbox(lat0, lon0, alt0, yaw, pitch, roll, fx, fy, cx, cy, bbox_center, H=real_obj_H)
    print("Test2 ENU:", Penu)
    if abs(Penu[1]) > 1e-6:
        raise AssertionError("N should be ~0 after 90deg yaw for center ray")
    # Only check magnitude; sign tells you yaw convention
    if not (abs(Penu[0]) > 0.1):
        raise AssertionError("E should be significantly non-zero after 90deg yaw")

    # Test 3: left-right symmetry for E
    dx = 200
    # make two bboxes with same height and bottom v=cy, but u shifts
    bbox_r = (cx+dx, cy-hpx, cx+dx, cy)
    bbox_l = (cx-dx, cy-hpx, cx-dx, cy)
    yaw=pitch=roll=0.0
    _, Penu_r, _ = monocular_gps_from_bbox(lat0, lon0, alt0, yaw, pitch, roll, fx, fy, cx, cy, bbox_r, H=real_obj_H)
    _, Penu_l, _ = monocular_gps_from_bbox(lat0, lon0, alt0, yaw, pitch, roll, fx, fy, cx, cy, bbox_l, H=real_obj_H)
    print("Test3 ENU right/left:", Penu_r, Penu_l)
    assert_close(Penu_r[1], Penu_l[1], 1e-6, "N should match for symmetric points")
    assert_close(Penu_r[2], Penu_l[2], 1e-6, "U should match for symmetric points")
    assert_close(Penu_r[0], -Penu_l[0], 1e-6, "E should be opposite for symmetric points")

    print("\nAll basic tests passed.")
    print("Yaw sign check: in Test2, if E>0 then +yaw rotates North->East; if E<0 then your yaw sign is opposite.")

if __name__ == "__main__":
    main()