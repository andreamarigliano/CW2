from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    arguments = {
        "target_id": "201",
        "offset_distance": "0.34",
        "marker_size": "0.10",
        "image_topic": "/camera/image_raw",
        "camera_info_topic": "/camera/camera_info",
        "camera_frame": "camera_optical_frame",
        "reference_frame": "base_link",
        "markers_topic": "/aruco_marker_publisher/markers",
        "target_pose_topic": "/target_pose",
        "use_sim_time": "true",
        "start_ik": "true",
    }

    detector = Node(
        package="aruco_ros",
        executable="marker_publisher",
        name="aruco_marker_publisher",
        parameters=[{
            "marker_size": ParameterValue(
                LaunchConfiguration("marker_size"), value_type=float),
            "reference_frame": LaunchConfiguration("reference_frame"),
            "camera_frame": LaunchConfiguration("camera_frame"),
            "image_is_rectified": True,
            "use_sim_time": ParameterValue(
                LaunchConfiguration("use_sim_time"), value_type=bool),
        }],
        remappings=[
            ("/image", LaunchConfiguration("image_topic")),
            ("/camera_info", LaunchConfiguration("camera_info_topic")),
            ("/aruco_marker_publisher/markers", LaunchConfiguration("markers_topic")),
        ],
        output="screen",
    )

    adapter = Node(
        package="armando_controller",
        executable="marker_to_target_node",
        name="marker_to_target",
        parameters=[{
            "target_id": ParameterValue(
                LaunchConfiguration("target_id"), value_type=int),
            "offset_distance": ParameterValue(
                LaunchConfiguration("offset_distance"), value_type=float),
            "markers_topic": LaunchConfiguration("markers_topic"),
            "target_pose_topic": LaunchConfiguration("target_pose_topic"),
            "use_sim_time": ParameterValue(
                LaunchConfiguration("use_sim_time"), value_type=bool),
        }],
        output="screen",
    )

    ik = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("armando_controller"),
            "launch",
            "armando_ik_kdl.launch.py",
        ])),
        launch_arguments={
            "target_pose_topic": LaunchConfiguration("target_pose_topic"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
        condition=IfCondition(LaunchConfiguration("start_ik")),
    )

    return LaunchDescription([
        *[
            DeclareLaunchArgument(name, default_value=value)
            for name, value in arguments.items()
        ],
        detector,
        adapter,
        ik,
    ])