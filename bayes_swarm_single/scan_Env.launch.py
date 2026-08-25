#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    robot_id = 1
    arena_lb = [0.0,0.0]
    arena_ub = [3.0,3.0]
    actions = []
    pose_topic_vicon = f"/vicon/SS_TB3_{robot_id}/SS_TB3_{robot_id}"
    obstacle_pose_topic_vicon = f"/vicon/Signal_source/Signal_source"
    cmd_vel_topic = f"TB3_{robot_id}/cmd_vel"

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
        launch_arguments={'namespace': f"TB3_{robot_id}"}.items(),
    )

    scan_env = Node(
        package="Signal_source",
        executable="Pattern_scan_env.py",
        name="patterm_scan",
        output="screen",
        parameters=[{
            "robot_id": robot_id,
            "arena_lb": arena_lb,
            "arena_ub": arena_ub,
            "number_of_points": 200,
            # topics/frames
            "pose_topic_vicon" : pose_topic_vicon,
            "obstacle_pose_topic_vicon" : obstacle_pose_topic_vicon, 
            "cmd_vel_topic": cmd_vel_topic,

        }],
    )
    rssi_node = Node(
        package='Signal_source',
        executable='Lora_e22_2.py',     # use 'Lora_e22_2.py' 
        name='lora_rssi_publisher',
        namespace = 'TB3_1',
        output='screen',
    )
    
    logger_node = Node(
        package='Signal_source',
        executable='logger.py',     # use 'logger.py' 
        name='Logger',
        output='screen',
    )


    ld = LaunchDescription(actions)
    ld.add_action(tb_bringup)
    ld.add_action(rssi_node)
    ld.add_action(scan_env)
    # ld.add_action(logger_node)
    return ld


