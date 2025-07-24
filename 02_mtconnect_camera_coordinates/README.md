# Robot-Captured Vision Dataset with MTConnect Sync

This repository captures RGB camera frames from an Intel RealSense while logging robotic joint angles, tool position, and orientation from an MTConnect agent. The system is useful for building datasets for 3D reconstruction, calibration, and robotic simulation.

## Components
- **robot_mtcpull.py**: Runs the capture loop and logs data.
- **igus_bridge.py**: Controls IGUS ReBeL robot to trigger movement or scanning routines.
- **plot_camera_capture.py**: Visualizes camera position in 3D over time from the log.

## Output Structure

```
robot_capture_sequence/
├── img_<timestamp>.png
└── capture_log.json
```

Each log entry includes:
- Joint angles (j1–j6)
- Position [X, Y, Z]
- Orientation [Roll, Pitch, Yaw]

## Visualization
Run:
```bash
python plot_camera_capture.py
```
To show the 3D path of the camera in the world frame.

## Requirements

Install with:
```bash
pip install -r requirements.txt
```

## Hardware Requirements

- IGUS ReBeL robot (connected to MTConnect agent)
- Intel RealSense camera (tested with D435i)
- Real-time control PC with network access to robot

## Notes

- `robot_mtcpull.py` runs the capture thread and robot motion in parallel
- Requires MTConnect stream served at: `http://localhost:5001/current`
- Robot movements are defined in XML programs (e.g., `camera_coordinate_test.xml`)

## Example
 <img width="1414" height="870" alt="robot_capture_path" src="https://github.com/user-attachments/assets/651648ab-3236-465c-97ed-a5a900d9c188" />

