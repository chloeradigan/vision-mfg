import threading
import time
import json
import os
import requests
import xml.etree.ElementTree as ET
import pyrealsense2 as rs
import numpy as np
import cv2

from igus_bridge import IgusBridge

# --- CONFIG ---
MTCONNECT_URL = "http://localhost:5001/current"
SAVE_DIR = "robot_capture_sequence"
JSON_LOG = os.path.join(SAVE_DIR, "capture_log.json")
os.makedirs(SAVE_DIR, exist_ok=True)

# --- RealSense Setup ---
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)
for _ in range(10):  # warm up
    pipeline.wait_for_frames()

# --- MTConnect Poller ---
def get_mtconnect_state():
    try:
        response = requests.get(MTCONNECT_URL, timeout=2)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns_uri = root.tag.split("}")[0][1:] if "}" in root.tag else ""
        ns = {'m': ns_uri} if ns_uri else {}

        joint_angles = {}
        for i in range(1, 7):
            tag = f'j{i}'
            el = root.find(f".//m:Angle[@name='{tag}']", ns)
            joint_angles[tag] = float(el.text.strip()) if el is not None else None

        pos_el = root.find(".//m:PathPosition", ns)
        position = list(map(float, pos_el.text.strip().split())) if pos_el is not None else [None, None, None]

        orient_el = root.find(".//m:Orientation", ns)
        orientation = list(map(float, orient_el.text.strip().split())) if orient_el is not None else [None, None, None]

        return {
            "joint_angles": joint_angles,
            "position": position,
            "orientation": orientation
        }
    except Exception as e:
        print(f"[MTConnect] Error: {e}")
        return None

# --- Capture Loop ---
def capture_loop(interval=5.0, duration=300.0):
    log = []
    start_time = time.time()

    while time.time() - start_time < duration:
        loop_start = time.time()
        timestamp = int(loop_start)
        img_name = f"img_{timestamp}.png"
        img_path = os.path.join(SAVE_DIR, img_name)

        try:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                print("Warning: No color frame received.")
                continue

            image = np.asanyarray(color_frame.get_data())
            cv2.imwrite(img_path, image)

            state = get_mtconnect_state()
            if state:
                log.append({
                    "timestamp": timestamp,
                    "image": img_name,
                    "joint_angles": state["joint_angles"],
                    "position": state["position"],
                    "orientation": state["orientation"]
                })
                print(f"Captured {img_name} at {state['position']}")
            else:
                print("Warning: MTConnect data unavailable. Skipping log entry.")

        except Exception as e:
            print(f"[Capture Error] {e}")

        elapsed = time.time() - loop_start
        remaining = interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    # Save log
    with open(JSON_LOG, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\n[INFO] Log saved to {JSON_LOG}")

# --- Robot Thread ---
def run_robot_program():
    robot = IgusBridge(sim=False)
    robot.enable_controller()
    robot.camera_capture_coord("r", "pnc")  # runs long, expected

# --- MAIN ---
if __name__ == "__main__":
    robot_thread = threading.Thread(target=run_robot_program)
    robot_thread.start()

    capture_loop(interval=5, duration=180)  # now runs 3 minutes reliably

    pipeline.stop()
