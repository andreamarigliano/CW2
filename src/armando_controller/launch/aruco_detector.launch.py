from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    aruco_marker_publisher = Node(
        package='aruco_ros',
        executable='marker_publisher',
        name='aruco_marker_publisher',

        parameters=[{
            'marker_size': 0.10,
            'reference_frame': 'base_link',
            'camera_frame': 'camera_optical_frame',
            'image_is_rectified': True,
            'use_sim_time': True,
        }],

        remappings=[
            ('/camera_info', '/camera/camera_info'),
            ('/image', '/camera/image_raw'),
        ],

        output='screen'
    )

    return LaunchDescription([
        aruco_marker_publisher
    ])