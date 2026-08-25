#!/usr/bin/env python3
# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument
# from launch.substitutions import LaunchConfiguration
# from launch_ros.actions import Node

# def generate_launch_description():
#     ns       = LaunchConfiguration('ns')
#     robot_id = LaunchConfiguration('robot_id')

#     # shared params
#     n_robots              = LaunchConfiguration('n_robots')
#     decision_horizon_init = LaunchConfiguration('decision_horizon_init')
#     observation_frequency = LaunchConfiguration('observation_frequency')
#     measurement_noise_rate= LaunchConfiguration('measurement_noise_rate')
#     velocity              = LaunchConfiguration('velocity')
#     time_max              = LaunchConfiguration('time_max')
#     decision_horizon      = LaunchConfiguration('decision_horizon')
#     arena_lb              = LaunchConfiguration('arena_lb')
#     arena_ub              = LaunchConfiguration('arena_ub')
#     source_detection_range= LaunchConfiguration('source_detection_range')
#     penalty_M             = LaunchConfiguration('penalty_M')
#     penalty_L             = LaunchConfiguration('penalty_L')

#     # topics/frames (RELATIVE topics so NS applies)
#     rssi_topic     = LaunchConfiguration('rssi_topic')
#     pose_topic_odom= LaunchConfiguration('pose_topic_odom')
#     pose_topic_vicon= LaunchConfiguration('pose_topic_vicon')    
#     cmd_vel_topic  = LaunchConfiguration('cmd_vel_topic')
#     global_frame   = LaunchConfiguration('global_frame')

#     return LaunchDescription([
#         DeclareLaunchArgument('ns', default_value='', description='Namespace for this robot'),
#         DeclareLaunchArgument('robot_id', default_value='1', description='Unique Robot Id'),
#         DeclareLaunchArgument('n_robots', default_value='1', description='Number of robots'),

#         DeclareLaunchArgument('decision_horizon_init', default_value='2.5'),
#         DeclareLaunchArgument('observation_frequency', default_value='10.0'),
#         DeclareLaunchArgument('measurement_noise_rate', default_value='0.05'),
#         DeclareLaunchArgument('velocity', default_value='0.2'),
#         DeclareLaunchArgument('time_max', default_value='300.0'),
#         DeclareLaunchArgument('decision_horizon', default_value='5.0'),
#         DeclareLaunchArgument('arena_lb', default_value='[-0.95, -0.95]'),
#         DeclareLaunchArgument('arena_ub', default_value='[0.95, 0.95]'),
#         DeclareLaunchArgument('source_detection_range', default_value='0.2'),
#         DeclareLaunchArgument('penalty_M', default_value='1.2'),
#         DeclareLaunchArgument('penalty_L', default_value='100.0'),

#         # IMPORTANT: relative topics (no leading slash)
#         DeclareLaunchArgument('rssi_topic', default_value='lora_rssi_values',
#                               description='RSSI topic (relative; will resolve to /<ns>/lora_rssi_values)'),
#         DeclareLaunchArgument('pose_topic_odom', default_value='odom',
#                               description='Odom topic (relative; will resolve to /<ns>/odom)'),
#         DeclareLaunchArgument('pose_topic_vicon', default_value='vicon',
#                               description='vicon topic (relative; will resolve to /vicon/topicname/namsespace)'),
        
#         DeclareLaunchArgument('cmd_vel_topic', default_value='cmd_vel',
#                               description='cmd_vel topic (relative; will resolve to /<ns>/cmd_vel)'),

#         # Must match Nav2 behavior_server.global_frame: "map" (AMCL) or "odom"
#         DeclareLaunchArgument('global_frame', default_value='map'),

#         Node(
#             package="bayes_swarm_single",
#             executable="bayes_swarm_node",
#             name="bayes_swarm",
#             namespace=ns,
#             output="screen",
#             parameters=[{
#                 "robot_id": robot_id,
#                 "n_robots": n_robots,
#                 "decision_horizon_init": decision_horizon_init,
#                 "observation_frequency": observation_frequency,
#                 "measurement_noise_rate": measurement_noise_rate,
#                 "velocity": velocity,
#                 "time_max": time_max,
#                 "decision_horizon": decision_horizon,
#                 "arena_lb": arena_lb,
#                 "arena_ub": arena_ub,
#                 "source_detection_range": source_detection_range,
#                 "penalty_M": penalty_M,
#                 "penalty_L": penalty_L,

#                 # topics/frames
#                 "rssi_topic": rssi_topic,
#                 "pose_topic_odom": pose_topic_odom,
#                 "pose_topic_vicon" : pose_topic_vicon,
#                 "cmd_vel_topic": cmd_vel_topic,
#                 "global_frame": global_frame,

#             }],
#         )
#     ])






from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="bayes_swarm_single",
            executable="bayes_swarm_node",
            name="bayes_swarm",
            output="screen",
            parameters=[{
                "robot_id": 1,
                "n_robots": 1,
                "decision_horizon_init": 2.5,
                "observation_frequency": 10.0,
                "measurement_noise_rate": 0.05,
                "velocity": 0.2,
                "time_max": 300.0,
                "decision_horizon": 5.0,
                "arena_lb": [-0.95, -0.95],
                "arena_ub": [ 0.95,  0.95],
                "source_detection_range": 0.2,
                "penalty_M": 1.2,
                "penalty_L": 100.0,
                # LoRa + motion topics
                "rssi_topic": "/TB3_1/Lora_signal_strength",   # std_msgs/Float32
                "cmd_vel_topic": "/TB3_1/cmd_vel",
                # "pose_topic_odom": "/TB3_1/odom",   # nav_msgs/Odometry
                "pose_topic_vicon":"/vicon/Colo_trans_TB3_1/Colo_trans_TB3_1",
            }],
        )
    ])
