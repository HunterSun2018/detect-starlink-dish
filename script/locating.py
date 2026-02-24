import numpy as np

R_EARTH = 6378137.0  # meters

def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], dtype=float)

def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]], dtype=float)

def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]], dtype=float)

def cam_to_enu_rotation(yaw, pitch, roll):
    """
    ENU:
      yaw about U(z), pitch about E(x), roll about N(y)
    OpenCV cam:
      x right, y down, z forward
    Zero pose: cam forward->North, right->East, down->-Up
    """
    R0 = np.array([[1, 0, 0],
                   [0, 0, 1],
                   [0,-1, 0]], dtype=float)

    R = rot_z(yaw) @ rot_x(pitch) @ rot_y(roll) @ R0
    return R

def bbox_to_cam_point(K_fx, K_fy, K_cx, K_cy, bbox_xyxy, real_H=0.4, use_bottom=True):
    x1,y1,x2,y2 = bbox_xyxy
    h = max(1.0, (y2 - y1))
    Z = K_fy * real_H / h

    u = 0.5*(x1+x2)
    v = y2 if use_bottom else 0.5*(y1+y2)

    X = (u - K_cx) * Z / K_fx
    Y = (v - K_cy) * Z / K_fy
    return np.array([X,Y,Z], dtype=float), Z

def enu_to_gps(lat0_deg, lon0_deg, alt0_m, E, N, U):
    lat0 = np.deg2rad(lat0_deg)
    lon0 = np.deg2rad(lon0_deg)

    dlat = N / R_EARTH
    dlon = E / (R_EARTH * np.cos(lat0))

    lat = lat0 + dlat
    lon = lon0 + dlon
    alt = alt0_m + U
    return np.rad2deg(lat), np.rad2deg(lon), alt

def monocular_gps_from_bbox(
    lat0_deg, lon0_deg, alt0_m,
    yaw_rad, pitch_rad, roll_rad,
    fx, fy, cx, cy,
    bbox_xyxy,
    real_H=0.4
):
    Pc, Z = bbox_to_cam_point(fx, fy, cx, cy, bbox_xyxy, real_H=real_H, use_bottom=True)
    R = cam_to_enu_rotation(yaw_rad, pitch_rad, roll_rad)
    Penu = R @ Pc  # [E, N, U] offset from camera position

    tgt_lat, tgt_lon, tgt_alt = enu_to_gps(lat0_deg, lon0_deg, alt0_m, Penu[0], Penu[1], Penu[2])
    return {
        "Z_m": float(Z),
        "ENU_m": (float(Penu[0]), float(Penu[1]), float(Penu[2])),
        "gps": (float(tgt_lat), float(tgt_lon), float(tgt_alt)),
    }