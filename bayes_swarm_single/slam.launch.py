#!/usr/bin/env python3
# colcon build --symlink-install

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    total_robots = 4
    robot_id = 1 # Change this for each robot: 1, 2, 3, 4 
    robot_ns = f'TB3_{robot_id}'
    actions = []
    # Set default TURTLEBOT3_MODEL only if not already set
    if not os.environ.get('TURTLEBOT3_MODEL'):
        actions.append(SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'))

    # --- Bring up TB3_4 base ---
    tb_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_bringup'),
                'launch', 'robot.launch.py'
            )
        ),
        launch_arguments={'namespace': robot_ns}.items(),
    )

    # SLAM Gmapping node for this robot with remapped topics
    gmapping_node = Node(
        package='slam_gmapping',
        executable='slam_gmapping',
        namespace=robot_ns,
        output='screen',
        parameters=[{
            'base_frame': f'{robot_ns}/base_footprint',
            'odom_frame': f'{robot_ns}/odom',
            'map_frame': f'{robot_ns}/map',
        }],
        remappings=[
            ('scan', f'/{robot_ns}/scan'),
            ('map', f'/{robot_ns}/map'),
            ('tf', f'/{robot_ns}/tf'),
            ('tf_static', f'/{robot_ns}/tf_static'),
        ]
    )


    ld = LaunchDescription(actions)
    ld.add_action(tb_bringup)
    ld.add_action(gmapping_node)
    return ld

