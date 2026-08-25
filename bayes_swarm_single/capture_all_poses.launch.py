from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([
        Node(
            package='your_package_name',
            executable='vicon_pose_collector',
            name='vicon_pose_collector',
            parameters=[
                {
                    'robot_namespaces': ['robot1', 'robot2', 'robot3'],
                    'vicon_base_topic': '/vicon',
                    'source_name': 'source',
                    'output_file': '/tmp/initial_poses.yaml'
                }
            ],
            output='screen'
        )
    ])
