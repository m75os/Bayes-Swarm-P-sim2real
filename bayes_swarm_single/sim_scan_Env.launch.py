#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable,GroupAction, DeclareLaunchArgument, TimerAction, LogInfo, RegisterEventHandler , ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node,PushRosNamespace
from launch.conditions import IfCondition
import xml.etree.ElementTree as ET
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration, PythonExpression



POSE_FILE = '/tmp/initial_poses.yaml'


def prefix_tf_references_only(root, prefix, robot_ns):
    for plugin in root.findall('.//plugin'):
        for elem in plugin.iter():
            if elem.tag in ['parent', 'child', 'frame'] and elem.text and not elem.text.startswith(prefix):
                elem.text = f'{prefix}{elem.text}'

        def update_or_create(tag_name, value):
            found = plugin.find(tag_name)
            if found is not None:
                found.text = value
            else:
                ET.SubElement(plugin, tag_name).text = value

        update_or_create('robotNamespace', robot_ns)
        update_or_create('odometryFrame', f'{prefix}odom')
        update_or_create('robotBaseFrame', f'{prefix}base_footprint')

    for elem in root.iter():
        if elem.tag in ['odometry_frame', 'robot_base_frame', 'frame_name'] and elem.text and not elem.text.startswith(prefix):
            elem.text = f'{prefix}{elem.text}'
    return root


def generate_launch_description():

    # Set default TURTLEBOT3_MODEL only if not already set
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'burger')

    total_robots = 1
    pose = [[1.0,3.0,0.01,3.14],[3.0,3.0,0.01,1.57],[3.0,2.0,0.01,-1.57],[2.5,2.5,0.01,0.0]]

    # Environment = 'Custom_world'
    # Environment = 'turtlebot3_house'
    Environment = 'empty_world'

    Environment_sdf_path = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'models', Environment,'model.sdf')

    model_folder = 'turtlebot3_' + TURTLEBOT3_MODEL

    urdf_path = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'models', model_folder, 'model.sdf')
    urdf_robot_file = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'urdf', f'turtlebot3_{TURTLEBOT3_MODEL}.urdf')
    save_path = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'models', model_folder, 'tmp')
    os.makedirs(save_path, exist_ok=True)

    launch_file_dir = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'launch')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    world = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'worlds', f'{Environment}.world')

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )

    headless_arg = DeclareLaunchArgument('headless', default_value='false', description='Run in headless mode (no GUI)')

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
        condition=IfCondition(PythonExpression(["'", LaunchConfiguration('headless'), "' == 'false'"]))
    )

    arena_lb = [0.0,0.0]
    arena_ub = [3.0,3.0]
    
    actions = []
    spawn_turtlebot_cmd_list = []
    static_tf_publishers = []
    rsp_nodes = []
    joint_state_publishers = []
    description_publishers = []    
    rssi_nodes = []
    scan_envs = []    
    logger_nodes = []


    for count in range(total_robots):
        robot_ns = f'TB3_{count+1}'
        prefix = f'{robot_ns}/'
        robot_id = count+1

        # Modify and save SDF with plugin injection and TF prefixing
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        root = prefix_tf_references_only(root, prefix, robot_ns)

        urdf_modified = ET.tostring(root, encoding='unicode')
        urdf_modified = '<?xml version="1.0" ?>\n' + urdf_modified
        sdf_output_path = os.path.join(save_path, f'{count+1}.sdf')
        with open(sdf_output_path, 'w') as file:
            file.write(urdf_modified)

        # Read URDF for robot_state_publisher
        with open(urdf_robot_file, 'r') as urdf_file:
            urdf_content = urdf_file.read()


        pose_topic_vicon = f"/{robot_ns}/odom"
        cmd_vel_topic = f"/{robot_ns}/cmd_vel"


        # Robot State Publisher Node with frame_prefix
        rsp_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name=f'robot_state_publisher_{robot_ns}',
            namespace=robot_ns,
            parameters=[{
                'use_sim_time': True,
                'frame_prefix': prefix,
                'robot_description': urdf_content
            }],
            # remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
            output='screen'
        )

        # Joint State Publisher Node
        joint_state_pub = Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name=f'joint_state_publisher_{robot_ns}',
            namespace=robot_ns,
            parameters=[{'use_sim_time': True}],
            output='screen'
        )

        # Explicitly publish the robot_description as a latched topic
        description_pub = Node(
            package='rclcpp_components',
            executable='component_container_mt',
            name=f'{robot_ns}_desc_pub',
            namespace=robot_ns,
            arguments=[],
            parameters=[{
                'use_sim_time': True,
                'robot_description': urdf_content
            }],
            remappings=[
                ('robot_description', f'{robot_ns}/robot_description')
            ],
            output='screen'
        )

        # Static transform to /map
        static_tf_node = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'static_tf_{robot_ns}',
            arguments=['0', '0', '0', '0', '0', '0', 'map', f'{robot_ns}/odom'],
            output='screen'
        )

        # Spawn Robot
        spawn_robot_cmd = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_file_dir, 'multi_spawn_turtlebot3.launch.py')
            ),
            launch_arguments={
                'x_pose': str(pose[count][0]),
                'y_pose': str(pose[count][1]),
                'z_pose': str(pose[count][2]),
                'yaw': str(pose[count][3]),
                'robot_name': f'{TURTLEBOT3_MODEL}_{count+1}',
                'namespace': robot_ns,
                'sdf_path': sdf_output_path
            }.items()
        )

        # --- LoRa RSSI publisher node ---
        rssi_node = Node(
            package='bayes_swarm_single',
            executable='simulated_source_node',     # use 'Lora_e22_2.py' 
            name=f'lora_rssi_publisher_{robot_ns}',
            parameters=[
                {
                    'position_topic': f'/{robot_ns}/odom',
                    'lora_rssi_topic': f'/{robot_ns}/Lora_signal_strength'
                }
            ],
            output='screen',
        )

        logger_node = Node(
            package='Signal_source',
            executable='logger.py',     # use 'logger.py' 
            name=f'Logger_{robot_ns}',
            output='screen',    
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
                "pose_topic_odom" : pose_topic_vicon,
                "obstacle_pose_topic_odom" : "", 
                "cmd_vel_topic": cmd_vel_topic,

            }],
        )
        

        spawn_turtlebot_cmd_list.append(spawn_robot_cmd)
        static_tf_publishers.append(static_tf_node)
        rsp_nodes.append(rsp_node)
        joint_state_publishers.append(joint_state_pub)
        description_publishers.append(description_pub)
        rssi_nodes.append(rssi_node)
        scan_envs.append(scan_env)    


    ld = LaunchDescription()

    ld.add_action(headless_arg)
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)

    for i in range(total_robots):
        ld.add_action(GroupAction([joint_state_publishers[i]]))
        ld.add_action(GroupAction([
            rsp_nodes[i],
            spawn_turtlebot_cmd_list[i],
            description_publishers[i]
        ]))
        ld.add_action(GroupAction([
            rssi_nodes[i],
            scan_envs[i],
        ]))
    ld.add_action(RegisterEventHandler(
        OnShutdown(on_shutdown=lambda event, context: [
            os.remove(os.path.join(save_path, f'{i+1}.sdf')) for i in range(total_robots)
        ])
    ))

    return ld


