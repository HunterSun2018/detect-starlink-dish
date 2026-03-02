#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import socket
import time
from typing import Any, Dict, Tuple
from functools import partial

REQUIRED_KEYS = ("lat0", "lon0", "alt0", "yaw_rad", "pitch_rad", "roll_rad")


def _as_float(v: Any, key: str) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            pass
    raise ValueError(f"field '{key}' must be a number (or numeric string), got: {type(v).__name__}")


def parse_payload(data: bytes) -> Dict[str, float]:
    # UDP 包通常很小，但仍建议做上限保护
    if len(data) > 65507:
        raise ValueError("UDP datagram too large")

    try:
        obj = json.loads(data.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"invalid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ValueError("JSON root must be an object/dict")

    for k in REQUIRED_KEYS:
        if k not in obj:
            raise ValueError(f"missing required field: '{k}'")

    parsed = {k: _as_float(obj[k], k) for k in REQUIRED_KEYS}

    # 可选：做一些范围校验（按需启用/修改）
    lat = parsed["lat0"]
    lon = parsed["lon0"]
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"lat0 out of range: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"lon0 out of range: {lon}")

    return parsed


def run_udp_server(bind_ip: str = "0.0.0.0", port: int = 9000, onUpdatePos=None) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 允许快速重启
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((bind_ip, port))
    print(f"[UDP] listening on {bind_ip}:{port}")

    while True:
        data, addr = sock.recvfrom(8192)  # 8KB 足够装下你的 JSON
        ts = time.time()

        try:
            msg = parse_payload(data)
            print(
                f"[{ts:.3f}] from {addr[0]}:{addr[1]} "
                f"lat0={msg['lat0']:.8f} lon0={msg['lon0']:.8f} alt0={msg['alt0']:.3f} "
                f"yaw={msg['yaw_rad']:.6f} pitch={msg['pitch_rad']:.6f} roll={msg['roll_rad']:.6f}"
            )
            if onUpdatePos is not None:
                gps = onUpdatePos(msg)
                
            # 回一个 ACK（可选）
            if gps is not None:
                ack = {"ok": True, "ts": ts, "lat": gps[0], "lon": gps[1], "alt": gps[2]}
            else:
                ack = {"ok": True, "ts": ts}
            
            sock.sendto(json.dumps(ack).encode("utf-8"), addr)

        except Exception as e:
            err = {"ok": False, "error": str(e), "ts": ts}
            # 尽量回错误信息，便于调试（可按需要关掉）
            try:
                sock.sendto(json.dumps(err).encode("utf-8"), addr)
            except Exception:
                pass
            print(f"[{ts:.3f}] from {addr[0]}:{addr[1]} ERROR: {e}")


if __name__ == "__main__":
    run_udp_server(bind_ip="0.0.0.0", port=9000)