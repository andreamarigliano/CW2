<<<<<<< HEAD
# Armando · Robotics Lab 2026 · Classwork 2

Armando is a four-joint robotic arm simulated in Gazebo with ROS 2 Humble. Classwork 2 connects the simulated camera to inverse kinematics. The detector recognizes the ArUco marker on the workbench, an adapter node computes a target above the marker, and the KDL solver moves the end effector to that position.

## Setup from a clean environment

Use Ubuntu with an X11 or XWayland desktop session, Git, and a running Docker daemon accessible to your user. The startup scripts use `xhost` and pass `/dev/dri` and `/dev/video0` through to the container. The CW2 camera itself is simulated.

### 1. Build the Docker image

Set `REPO_URL` to the HTTPS URL of your public submission repository, then run:

```bash
git clone "git clone https://github.com/andreamarigliano/CW2.git" Armando_Simulation
cd Armando_Simulation
bash docker_scripts/docker_build_image.sh
```

The Dockerfile installs ROS 2 Humble, the simulation dependencies, and `ros-humble-aruco-ros`, which brings in `aruco_msgs`. Rebuild the image whenever the Dockerfile changes. Wait for the script to print `Build completed` before starting the container.

### 2. Start Gazebo

In the first terminal, run this from the repository root on the host:

```bash
bash docker_scripts/docker_run_container.sh
```

The script mounts `src/` from the host, builds the workspace, and sources the ROS environment. Start Gazebo at the container prompt:

```bash
env -u LIBGL_ALWAYS_SOFTWARE ros2 launch armando_description armando_gazebo.launch.py
```

Gazebo should show the arm, the workbench, and the marker on the work surface. Keep this terminal open.

### 3. Start the ArUco and KDL pipeline

In a second terminal, run this from the repository root on the host:

```bash
bash docker_scripts/docker_connect.sh
```

Inside the container, source the workspace and check the controllers:

```bash
source /root/ros2_ws/install/setup.bash
ros2 control list_controllers
```

Wait for both `joint_state_broadcaster` and `joint_trajectory_controller` to report `active`, then start the pipeline:

```bash
ros2 launch armando_controller aruco_pipeline.launch.py \
  target_id:=201 offset_distance:=0.30
```

The pipeline starts the detector and the adapter and includes `armando_ik_kdl.launch.py`. The arm should move above the marker and hold its position. The controller log should report `Goal reached, success!`. The test uses an offset of **0.30 m**. The launch defaults to 0.34 m, so the command specifies the tested value explicitly.

## Marker and scene

| Item | Configuration |
|---|---|
| Dictionary | `DICT_5X5_250` |
| ID | `201` |
| Black square side length | `0.10 m` |
| White border | Approximately `0.12857 m` overall side length |
| Model | `src/armando_description/models/aruco_marker_201/model.sdf` |
| Texture | `materials/textures/aruco_201.png` inside the model directory |
| World pose | `0.20 0 0.406 0 0 0` in `armando_workbench.sdf` |

The original 756 × 756 PNG contains the black square and the marker pattern. The material on the 0.10 m plane loads the PNG through `albedo_map`. A separate white backing provides contrast around the border. The `marker_size` parameter is the side length of the black square and is set to `0.10`.

In `rqt_image_view`, select `/camera/image_raw` to check that the entire marker is in view. The launch uses `camera_optical_frame` as the camera frame and expresses the estimated marker pose in `base_link`.

## ROS data flow and target calculation

| Component | Input | Output |
|---|---|---|
| `aruco_ros/marker_publisher` detector | `/camera/image_raw` and `/camera/camera_info` | `aruco_msgs/msg/MarkerArray` on `/aruco_marker_publisher/markers` |
| `marker_to_target_node` adapter | Array of detections | `geometry_msgs/msg/PoseStamped` on `/target_pose` for the selected ID |
| `armando_ik_kdl_node` solver | `/target_pose`, `/joint_states`, and the URDF | Joint trajectory for `j0`–`j3` via `/joint_trajectory_controller/follow_joint_trajectory` |

The adapter preserves the measurement frame and timestamp. It rotates the vector `(0, 0, d)` by the marker orientation and adds it to the measured marker position. This places the target at distance `d` along the positive normal to the marker plane. The adapter also rotates the target orientation by 180° about the marker's local X axis, so the target's Z axis points toward the marker.

KDL builds the chain from `base_link` to `crawer_base` using the expanded Xacro and uses the current joint positions as its initial guess. It uses TF to transform the target into `base_link` when needed. The solver checks the URDF joint limits and constrains only the XYZ position of `crawer_base`. The target message also carries the orientation calculated by the adapter.

## Verification and target changes

Open another container shell by running `bash docker_scripts/docker_connect.sh` on the host, then source `/root/ros2_ws/install/setup.bash` in the container. Run these commands individually:

```bash
ros2 topic echo /aruco_marker_publisher/markers --once
ros2 topic echo /target_pose --once
ros2 run tf2_ros tf2_echo base_link crawer_base
```

The first command shows the detected ID and marker pose. The second shows the target published by the adapter. After the motion finishes, compare the TF `Translation` with the position on `/target_pose`. If the arm occludes the marker, you can still check the final end-effector position with TF. To inspect the target before the arm moves, start the pipeline with `start_ik:=false`.

To try a different offset, stop the pipeline and relaunch it with a different `offset_distance`. To move the marker, edit its `<pose>` in `src/armando_description/worlds/armando_workbench.sdf`, rebuild `armando_description`, and restart Gazebo:

```bash
cd /root/ros2_ws
colcon build --packages-select armando_description
source install/setup.bash
```

Place the marker where the camera can see it and the arm can reach the resulting target. A detectable marker can still produce a target outside the arm's workspace. Run `ros2 launch armando_controller aruco_pipeline.launch.py --show-args` to list the available arguments for marker ID, frames, topics, and simulation time.

## Manual IK test

With Gazebo running and the ArUco pipeline stopped, run `ros2 launch armando_controller armando_ik_kdl.launch.py`. Source the workspace in a second container terminal and publish a test pose:

```bash
ros2 topic pub --once /target_pose geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: base_link}, pose: {position: {x: 0.2, y: 0.0, z: 0.3}, orientation: {w: 1.0}}}"
```

## Troubleshooting

- **Black scene when using the texture.** In the tested setup, the PNG worked when Gazebo was started without forcing software rendering. Use the Gazebo launch command above.
- **`package 'aruco_ros' not found`.** Rebuild the image from the updated Dockerfile and start a new container. The startup script runs the container with `--rm`.
- **The arm stays still.** Check that the controllers are active, the detector recognizes the selected ID, and the adapter publishes on `/target_pose`. If a target is present, check the KDL and controller logs for a valid solution and an accepted trajectory.

This project is based on the [course starter repository](https://github.com/RoboticsLab2026/Armando_Simulation).
=======
# CW2
Armando_ARUCO
>>>>>>> 4b0acb0c749ac6941cff9e81300a3c9c4a5012ed
