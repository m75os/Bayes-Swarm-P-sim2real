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

    # --- LoRa RSSI publisher node ---
    rssi_node = Node(
        package='Signal_source',
        executable='Lora_e22_2.py',     # use 'Lora_e22_2.py' 
        name='lora_rssi_publisher',
        namespace = robot_ns,
        output='screen',
    )

    logger_node = Node(
        package='Signal_source',
        executable='logger.py',     # use 'logger.py' 
        name='Logger',
        output='screen',    
    )

    # --- Bayes Swarm node ---
    bayes_swarm_node = Node(
            package="bayes_swarm_single",
            executable="bayes_swarm_node",
            name=f"bayes_swarm_{robot_ns}",
            output="screen",
            parameters=[{
                "robot_id": robot_id,
                "n_robots": total_robots,
                "active_set_size" : 1000,
                "Simulator" : False,
                "Vicon" : True,
                "Debug" : False,
                "data_folder_path" : f"/tmp/bayes_swarm_plots_{robot_ns}",
                "Log_data" : False,
                "decision_horizon_init": 2.5,
                "observation_frequency": 10.0,
                "measurement_noise_rate": 0.05,
                "velocity": 0.2,
                "time_max": 100.0,
                "decision_horizon": 7.0,
                "arena_lb": [0.0, 0.0],
                "arena_ub": [ 3.0,  3.0],
                "source_detection_range": 0.2,
                "penalty_M": 1.2,
                "penalty_L": 100.0,
                "Model" : "Random_Walk", ## Choose any onr from "GP" or "SGP" or "PSO" or "Random_Walk"
                # LoRa + motion topics
                "rssi_topic": f"/{robot_ns}/Lora_signal_strength",   # std_msgs/Float32
                "cmd_vel_topic": f"/{robot_ns}/cmd_vel",
                "pose_topic_odom": f"/{robot_ns}/odom",   # nav_msgs/Odometry
                "pose_topic_vicon":f"/vicon/SS_{robot_ns}/SS_{robot_ns}",
            }],
        )




    ld = LaunchDescription(actions)
    ld.add_action(tb_bringup)
    ld.add_action(rssi_node)
    ld.add_action(bayes_swarm_node)
    ld.add_action(logger_node)
    return ld

