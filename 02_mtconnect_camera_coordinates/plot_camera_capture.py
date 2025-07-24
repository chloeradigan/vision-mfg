import json
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIG ---
LOG_PATH = "robot_capture_sequence/capture_log.json"

# --- Camera Offset in End-Effector Frame ---
cam_offset_vec = np.array([63.5, -37.1, 0, 1])  # X, Y, Z, Homogeneous

# --- Euler to Rotation Matrix ---
def euler_to_matrix(rx, ry, rz):
    rx, ry, rz = np.radians([rx, ry, rz])
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rx), -np.sin(rx)],
                   [0, np.sin(rx),  np.cos(rx)]])
    Ry = np.array([[ np.cos(ry), 0, np.sin(ry)],
                   [0, 1, 0],
                   [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                   [np.sin(rz),  np.cos(rz), 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx  # ZYX order

# --- Apply Offset ---
def compute_camera_world_position(position, orientation):
    T = np.eye(4)
    T[:3, :3] = euler_to_matrix(*orientation)
    T[:3, 3] = position
    cam_world = T @ cam_offset_vec
    return cam_world[:3]

# --- Load Data & Compute Points ---
with open(LOG_PATH, "r") as f:
    data = json.load(f)

points = []
labels = []

for entry in data:
    pos = entry.get("position")
    ori = entry.get("orientation")
    if pos and ori and None not in pos and None not in ori:
        cam_world = compute_camera_world_position(pos, ori)
        points.append(cam_world)
        labels.append(entry["image"])

points = np.array(points)

# --- Plotting ---
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

import matplotlib.cm as cm

# Create color values from 0 to 1 based on capture order
norm_indices = np.linspace(1.0, 0.2, len(points))  # light → dark
colors = cm.plasma(norm_indices)

# Plot with color mapped to capture order
sc = ax.scatter(points[:, 0], points[:, 1], points[:, 2], c=colors, marker='o')


#for i, label in enumerate(labels):
    #ax.text(points[i, 0], points[i, 1], points[i, 2], label, fontsize=8)
import matplotlib.colors as mcolors

sm = plt.cm.ScalarMappable(cmap='plasma', norm=mcolors.Normalize(vmin=1, vmax=len(points)))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, label='Capture Order (earliest = lighter)')


ax.set_title("Camera Capture Positions (World Frame)")
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")
ax.set_box_aspect([1, 1, 1])
ax.view_init(elev=30, azim=45)
plt.tight_layout()
plt.show()
