#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Multi-robot Nav2 bringup using a SINGLE namespace-free params YAML.

IMPORTANT TRUTH:
- Node namespaces do NOT namespace TF frame IDs.
- Your TF frames are prefixed: TB3_1/base_footprint, TB3_1/odom, etc.
- Therefore we MUST rewrite frame IDs per robot namespace at launch time.

This launch:
- Runs Nav2 nodes per-robot namespace (TB3_1, TB3_2, ...)
- Uses ONE base params YAML (namespace-free)
- Uses RewrittenYaml root_key=<ns> AND rewrites frame IDs per robot
- Map server is global
- TF topics are global (/tf, /tf_static)
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def _to_bool(s: str) -> bool:
    return str(s).strip().lower() in ("true", "1", "yes", "on")


def _launch_setup(context, *args, **kwargs):
    num_robots = int(LaunchConfiguration("num_robots").perform(context))
    namespace_prefix = LaunchConfiguration("namespace_prefix").perform(context)
    config_pkg = LaunchConfiguration("config_pkg").perform(context)

    map_file_cli = LaunchConfiguration("map_file").perform(context)
    params_file_cli = LaunchConfiguration("params_file").perform(context)

    use_velocity_smoother = _to_bool(LaunchConfiguration("use_velocity_smoother").perform(context))

    # For RewrittenYaml we can pass string -> convert_types=True will convert,
    # for Node dict we must pass a real bool
    use_sim_time_str = LaunchConfiguration("use_sim_time").perform(context)   # "True"/"False"
    use_sim_time_bool = _to_bool(use_sim_time_str)

    pkg_share = get_package_share_directory(config_pkg)

    # Map
    default_map_path = os.path.join(pkg_share, "map", "map.yaml")
    map_file = map_file_cli if map_file_cli and map_file_cli.lower() != "default" else default_map_path

    # Params (namespace-free base file)
    # CHANGE THIS default to whatever you actually named the namespace-free YAML.
    default_params_path = os.path.join(pkg_share, "config", "nav2_params.yaml")
    params_file = params_file_cli if params_file_cli and params_file_cli.lower() != "default" else default_params_path

    if not os.path.isfile(map_file):
        raise FileNotFoundError(f"Map YAML not found: {map_file}")

    if not os.path.isfile(params_file):
        raise FileNotFoundError(
            f"Params YAML not found: {params_file}\n"
            f"Put it at: {default_params_path}\n"
            f"or pass params_file:=/abs/path/to/nav2_params_base_no_namespace.yaml"
        )

    rviz_config_dir = os.path.join(
        get_package_share_directory("turtlebot3_navigation2"),
        "rviz",
        "tb3_navigation2.rviz",
    )

    nodes = []

    # -------------------- Global map server --------------------
    nodes.append(
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            output="screen",
            parameters=[{
                "use_sim_time": use_sim_time_bool,
                "topic_name": "map",
                "frame_id": "map",
                "yaml_filename": map_file,
            }],
        )
    )

    lifecycle_nodes = ["map_server"]

    # Force namespaced Nav2 nodes to use global TF topics
    tf_remaps = [("tf", "/tf"), ("tf_static", "/tf_static")]

    # -------------------- Per-robot Nav2 nodes --------------------
    for i in range(1, num_robots + 1):
        ns = f"{namespace_prefix}_{i}"

        # Your TF frames are prefixed like:
        #   TB3_1/odom, TB3_1/base_footprint, TB3_1/base_scan
        odom_frame = f"{ns}/odom"
        base_frame = f"{ns}/base_footprint"

        # ✅ Robust param rewrites:
        # rewrite the ACTUAL parameter keys that appear in many Nav2 sections
        param_rewrites = {
            "use_sim_time": use_sim_time_str,

            # AMCL frame IDs
            "base_frame_id": base_frame,
            "odom_frame_id": odom_frame,
            "global_frame_id": "map",

            # Costmaps / behaviors / navigator commonly use these names:
            "robot_base_frame": base_frame,
            "odom_frame": odom_frame,
            "global_frame": "map",
        }

        configured_params = RewrittenYaml(
            source_file=params_file,
            root_key=ns,
            param_rewrites=param_rewrites,
            convert_types=True,
        )

        # AMCL
        nodes.append(
            Node(
                namespace=ns,
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                output="screen",
                parameters=[configured_params],
                remappings=tf_remaps,
            )
        )

        # Controller (cmd_vel -> cmd_vel_nav)
        nodes.append(
            Node(
                namespace=ns,
                package="nav2_controller",
                executable="controller_server",
                name="controller_server",
                output="screen",
                parameters=[configured_params],
                remappings=tf_remaps + [("cmd_vel", "cmd_vel_nav")],
            )
        )

        # Planner
        nodes.append(
            Node(
                namespace=ns,
                package="nav2_planner",
                executable="planner_server",
                name="planner_server",
                output="screen",
                parameters=[configured_params],
                remappings=tf_remaps,
            )
        )

        # Behaviors / recovery
        nodes.append(
            Node(
                namespace=ns,
                package="nav2_behaviors",
                executable="behavior_server",
                name="behavior_server",
                output="screen",
                parameters=[configured_params],
                remappings=tf_remaps,
            )
        )

        # BT Navigator
        nodes.append(
            Node(
                namespace=ns,
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator",
                output="screen",
                parameters=[configured_params],
                remappings=tf_remaps,
            )
        )

        # Optional: velocity smoother (cmd_vel_nav -> cmd_vel)
        if use_velocity_smoother:
            nodes.append(
                Node(
                    namespace=ns,
                    package="nav2_velocity_smoother",
                    executable="velocity_smoother",
                    name="velocity_smoother",
                    output="screen",
                    parameters=[configured_params],
                    remappings=tf_remaps + [
                        ("cmd_vel", "cmd_vel_nav"),
                        ("cmd_vel_smoothed", "cmd_vel"),
                    ],
                )
            )

        lifecycle_nodes.extend([
            f"{ns}/amcl",
            f"{ns}/planner_server",
            f"{ns}/controller_server",
            f"{ns}/behavior_server",
            f"{ns}/bt_navigator",
        ])
        if use_velocity_smoother:
            lifecycle_nodes.append(f"{ns}/velocity_smoother")

    # -------------------- Lifecycle manager + RViz (delayed) --------------------
    nodes.append(
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package="nav2_lifecycle_manager",
                    executable="lifecycle_manager",
                    name="lifecycle_manager_navigation",
                    output="screen",
                    parameters=[{
                        "use_sim_time": use_sim_time_bool,
                        "autostart": True,
                        "bond_timeout": 0.0,
                        "node_names": lifecycle_nodes,
                    }],
                ),
                Node(
                    package="rviz2",
                    executable="rviz2",
                    name="rviz2",
                    arguments=["-d", rviz_config_dir],
                    parameters=[{"use_sim_time": use_sim_time_bool}],
                    output="screen",
                ),
            ],
        )
    )

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("num_robots", default_value="1"),
        DeclareLaunchArgument("namespace_prefix", default_value="TB3"),
        DeclareLaunchArgument("config_pkg", default_value="bayes_swarm_single"),
        DeclareLaunchArgument("map_file", default_value="default"),
        DeclareLaunchArgument(
            "params_file",
            default_value="default",
            description='Absolute path to namespace-free params yaml. Use "default" for <config_pkg>/config/nav2_params_base_no_namespace.yaml',
        ),
        DeclareLaunchArgument("use_velocity_smoother", default_value="True"),
        DeclareLaunchArgument("use_sim_time", default_value="True"),
        OpaqueFunction(function=_launch_setup),
    ])



# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# Multi-robot Nav2 bringup using a SINGLE namespace-free params YAML.

# IMPORTANT TRUTH:
# - Node namespaces do NOT namespace TF frame IDs.
# - Your TF frames are prefixed: TB3_1/base_footprint, TB3_1/odom, etc.
# - Therefore we MUST rewrite frame IDs per robot namespace at launch time.

# This launch:
# - Runs Nav2 nodes per-robot namespace (TB3_1, TB3_2, ...)
# - Uses ONE base params YAML (namespace-free)
# - Uses RewrittenYaml root_key=<ns> AND rewrites frame IDs per robot
# - Map server is global
# - TF topics are global (/tf, /tf_static)
# """

# import os

# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
# from launch.substitutions import LaunchConfiguration
# from ament_index_python.packages import get_package_share_directory
# from launch_ros.actions import Node
# from nav2_common.launch import RewrittenYaml


# def _to_bool(s: str) -> bool:
#     return str(s).strip().lower() in ("true", "1", "yes", "on")


# def _launch_setup(context, *args, **kwargs):
#     num_robots = int(LaunchConfiguration("num_robots").perform(context))
#     namespace_prefix = LaunchConfiguration("namespace_prefix").perform(context)
#     config_pkg = LaunchConfiguration("config_pkg").perform(context)

#     map_file_cli = LaunchConfiguration("map_file").perform(context)
#     params_file_cli = LaunchConfiguration("params_file").perform(context)

#     use_velocity_smoother = _to_bool(LaunchConfiguration("use_velocity_smoother").perform(context))

#     # For RewrittenYaml we want string, for Node dict we want bool
#     use_sim_time_str = LaunchConfiguration("use_sim_time").perform(context)      # "True"/"False"
#     use_sim_time_bool = _to_bool(use_sim_time_str)

#     pkg_share = get_package_share_directory(config_pkg)

#     # Map
#     default_map_path = os.path.join(pkg_share, "map", "map.yaml")
#     map_file = map_file_cli if map_file_cli and map_file_cli.lower() != "default" else default_map_path

#     # Params (namespace-free base file)
#     default_params_path = os.path.join(pkg_share, "config", "myslam_param_TB3_1.yaml")
#     params_file = params_file_cli if params_file_cli and params_file_cli.lower() != "default" else default_params_path

#     if not os.path.isfile(map_file):
#         raise FileNotFoundError(f"Map YAML not found: {map_file}")

#     if not os.path.isfile(params_file):
#         raise FileNotFoundError(
#             f"Params YAML not found: {params_file}\n"
#             f"Put it at: {default_params_path}\n"
#             f"or pass params_file:=/abs/path/to/nav2_params_base_no_namespace.yaml"
#         )

#     rviz_config_dir = os.path.join(
#         get_package_share_directory("turtlebot3_navigation2"),
#         "rviz",
#         "tb3_navigation2.rviz",
#     )

#     nodes = []

#     # -------------------- Global map server --------------------
#     nodes.append(
#         Node(
#             package="nav2_map_server",
#             executable="map_server",
#             name="map_server",
#             output="screen",
#             parameters=[{
#                 "use_sim_time": use_sim_time_bool,     # MUST be bool here
#                 "topic_name": "map",
#                 "frame_id": "map",
#                 "yaml_filename": map_file,
#             }],
#         )
#     )

#     lifecycle_nodes = ["map_server"]

#     # Force namespaced Nav2 nodes to use global TF topics
#     tf_remaps = [("tf", "/tf"), ("tf_static", "/tf_static")]

#     # -------------------- Per-robot Nav2 nodes --------------------
#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"

#         # Your TF frames are prefixed like this:
#         #   TB3_1/odom, TB3_1/base_footprint, TB3_1/base_scan
#         odom_frame = f"{ns}/odom"
#         base_frame = f"{ns}/base_footprint"

#         # Rewrite params for this robot:
#         # - use_sim_time
#         # - AMCL frames
#         # - costmap frames
#         # Note: scan_topic should be "scan" in the base yaml (relative topic),
#         # so /TB3_1/scan is resolved by node namespace automatically.
#         param_rewrites = {
#             "use_sim_time": use_sim_time_str,

#             # AMCL
#             "amcl.ros__parameters.base_frame_id": base_frame,
#             "amcl.ros__parameters.odom_frame_id": odom_frame,
#             "amcl.ros__parameters.global_frame_id": "map",

#             # Local costmap
#             "local_costmap.local_costmap.ros__parameters.robot_base_frame": base_frame,
#             "local_costmap.local_costmap.ros__parameters.odom_frame": odom_frame,

#             # Global costmap
#             "global_costmap.global_costmap.ros__parameters.robot_base_frame": base_frame,
#             "global_costmap.global_costmap.ros__parameters.odom_frame": odom_frame,
#         }

#         configured_params = RewrittenYaml(
#             source_file=params_file,
#             root_key=ns,
#             param_rewrites=param_rewrites,
#             convert_types=True,
#         )

#         # AMCL
#         nodes.append(
#             Node(
#                 namespace=ns,
#                 package="nav2_amcl",
#                 executable="amcl",
#                 name="amcl",
#                 output="screen",
#                 parameters=[configured_params],
#                 remappings=tf_remaps,
#             )
#         )

#         # Controller (cmd_vel -> cmd_vel_nav)
#         nodes.append(
#             Node(
#                 namespace=ns,
#                 package="nav2_controller",
#                 executable="controller_server",
#                 name="controller_server",
#                 output="screen",
#                 parameters=[configured_params],
#                 remappings=tf_remaps + [("cmd_vel", "cmd_vel_nav")],
#             )
#         )

#         # Planner
#         nodes.append(
#             Node(
#                 namespace=ns,
#                 package="nav2_planner",
#                 executable="planner_server",
#                 name="planner_server",
#                 output="screen",
#                 parameters=[configured_params],
#                 remappings=tf_remaps,
#             )
#         )

#         # Behaviors / recovery
#         nodes.append(
#             Node(
#                 namespace=ns,
#                 package="nav2_behaviors",
#                 executable="behavior_server",
#                 name="behavior_server",
#                 output="screen",
#                 parameters=[configured_params],
#                 remappings=tf_remaps,
#             )
#         )

#         # BT Navigator
#         nodes.append(
#             Node(
#                 namespace=ns,
#                 package="nav2_bt_navigator",
#                 executable="bt_navigator",
#                 name="bt_navigator",
#                 output="screen",
#                 parameters=[configured_params],
#                 remappings=tf_remaps,
#             )
#         )

#         # Optional: velocity smoother (cmd_vel_nav -> cmd_vel)
#         if use_velocity_smoother:
#             nodes.append(
#                 Node(
#                     namespace=ns,
#                     package="nav2_velocity_smoother",
#                     executable="velocity_smoother",
#                     name="velocity_smoother",
#                     output="screen",
#                     parameters=[configured_params],
#                     remappings=tf_remaps + [
#                         ("cmd_vel", "cmd_vel_nav"),
#                         ("cmd_vel_smoothed", "cmd_vel"),
#                     ],
#                 )
#             )

#         lifecycle_nodes.extend([
#             f"{ns}/amcl",
#             f"{ns}/planner_server",
#             f"{ns}/controller_server",
#             f"{ns}/behavior_server",
#             f"{ns}/bt_navigator",
#         ])
#         if use_velocity_smoother:
#             lifecycle_nodes.append(f"{ns}/velocity_smoother")

#     # -------------------- Lifecycle manager + RViz (delayed) --------------------
#     nodes.append(
#         TimerAction(
#             period=7.0,
#             actions=[
#                 Node(
#                     package="nav2_lifecycle_manager",
#                     executable="lifecycle_manager",
#                     name="lifecycle_manager_navigation",
#                     output="screen",
#                     parameters=[{
#                         "use_sim_time": use_sim_time_bool,   # MUST be bool here
#                         "autostart": True,
#                         "bond_timeout": 0.0,
#                         "node_names": lifecycle_nodes,
#                     }],
#                 ),
#                 Node(
#                     package="rviz2",
#                     executable="rviz2",
#                     name="rviz2",
#                     arguments=["-d", rviz_config_dir],
#                     parameters=[{"use_sim_time": use_sim_time_bool}],  # MUST be bool here
#                     output="screen",
#                 ),
#             ],
#         )
#     )

#     return nodes


# def generate_launch_description():
#     return LaunchDescription([
#         DeclareLaunchArgument(
#             "num_robots",
#             default_value="2",
#             description="Number of robots to bring up Nav2 for",
#         ),
#         DeclareLaunchArgument(
#             "namespace_prefix",
#             default_value="TB3",
#             description="Namespace prefix: TB3 -> TB3_1, TB3_2, ...",
#         ),
#         DeclareLaunchArgument(
#             "config_pkg",
#             default_value="turtlebot3_gazebo",
#             description="Package containing config/ and map/ directories",
#         ),
#         DeclareLaunchArgument(
#             "map_file",
#             default_value="default",
#             description='Absolute path to map yaml. Use "default" for <config_pkg>/map/map.yaml',
#         ),
#         DeclareLaunchArgument(
#             "params_file",
#             default_value="default",
#             description='Absolute path to namespace-free params yaml. Use "default" for <config_pkg>/config/nav2_params_base_no_namespace.yaml',
#         ),
#         DeclareLaunchArgument(
#             "use_velocity_smoother",
#             default_value="True",
#             description="Launch velocity_smoother per robot and route cmd_vel_nav -> cmd_vel",
#         ),
#         DeclareLaunchArgument(
#             "use_sim_time",
#             default_value="True",
#             description="Use simulation time",
#         ),
#         OpaqueFunction(function=_launch_setup),
#     ])









# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# Argument-driven multi-robot Nav2 bringup.

# Args:
# - num_robots (int)           : number of robots (default: 3)
# - namespace_prefix (string)  : namespace prefix (default: TB3)
# - base_robot (string)        : base robot name whose YAML is the template (default: TB3_1)
# - config_pkg (string)        : package that holds the config/ and map/ dirs (default: turtlebot3_gazebo)
# - map_file (string)          : absolute path to map.yaml (default: <config_pkg>/map/map.yaml)

# Notes:
# - Generates per-robot param files: config/myslam_param_<NS>.yaml from config/myslam_param_<base_robot>.yaml
# - Does NOT touch TF.

# """

# import os
# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
# from launch.substitutions import LaunchConfiguration
# from ament_index_python.packages import get_package_share_directory
# from launch_ros.actions import Node


# def _generate_param_files(base_template_path: str, output_dir: str, base_name: str,
#                           namespace_prefix: str, num_robots: int, base_robot: str, log=print):
#     if not os.path.isfile(base_template_path):
#         raise FileNotFoundError(f"Base template not found: {base_template_path}")

#     with open(base_template_path, 'r') as f:
#         base_content = f.read()

#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"
#         updated = base_content.replace(base_robot, ns)
#         out_path = os.path.join(output_dir, f'{base_name}_{ns}.yaml')
#         with open(out_path, 'w') as f:
#             f.write(updated)
#         log(f'✅ Generated/updated param file: {out_path}')


# def _launch_setup(context, *args, **kwargs):
#     num_robots = int(LaunchConfiguration('num_robots').perform(context))
#     namespace_prefix = LaunchConfiguration('namespace_prefix').perform(context)
#     base_robot = LaunchConfiguration('base_robot').perform(context)
#     config_pkg = LaunchConfiguration('config_pkg').perform(context)
#     map_file_cli = LaunchConfiguration('map_file').perform(context)

#     use_sim_time = True  # must be True for Gazebo

#     pkg_share = get_package_share_directory(config_pkg)
#     config_dir = os.path.join(pkg_share, 'config')
#     base_file = os.path.join(config_dir, f'myslam_param_{base_robot}.yaml')
#     base_output_name = 'myslam_param'
#     default_map_path = os.path.join(pkg_share, 'map', 'map.yaml')
#     map_file = map_file_cli if map_file_cli and map_file_cli.lower() != 'default' else default_map_path
#     rviz_config_dir = os.path.join(get_package_share_directory('turtlebot3_navigation2'),'rviz','tb3_navigation2.rviz')

#     _generate_param_files(
#         base_template_path=base_file,
#         output_dir=config_dir,
#         base_name=base_output_name,
#         namespace_prefix=namespace_prefix,
#         num_robots=num_robots,
#         base_robot=base_robot,
#         log=lambda msg: print(msg, flush=True)
#     )

#     nodes = []

#     # Shared map server
#     nodes.append(
#         Node(
#             package='nav2_map_server',
#             executable='map_server',
#             name='map_server',
#             output='screen',
#             parameters=[{
#                 'use_sim_time': use_sim_time,
#                 'topic_name': 'map',
#                 'frame_id': 'map',
#                 'yaml_filename': map_file
#             }]
#         )
#     )

#     lifecycle_nodes = ['map_server']

#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"
#         config_file = os.path.join(config_dir, f'{base_output_name}_{ns}.yaml')

#         # # Add robot_state_publisher first (critical for TF availability)
#         # nodes.append(
#         #     Node(
#         #         package='robot_state_publisher',
#         #         executable='robot_state_publisher',
#         #         namespace=ns,
#         #         name='robot_state_publisher',
#         #         output='screen',
#         #         parameters=[{'use_sim_time': use_sim_time}]
#         #     )
#         # )

#         # Nav2 nodes
#         nodes += [
#             Node(
#                 namespace=ns,
#                 package='nav2_amcl',
#                 executable='amcl',
#                 name='amcl',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_controller',
#                 executable='controller_server',
#                 name='controller_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_planner',
#                 executable='planner_server',
#                 name='planner_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_behaviors',
#                 executable='behavior_server',
#                 name='behavior_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_bt_navigator',
#                 executable='bt_navigator',
#                 name='bt_navigator',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#         ]

#         lifecycle_nodes.extend([
#             f'{ns}/amcl',
#             f'{ns}/planner_server',
#             f'{ns}/controller_server',
#             f'{ns}/behavior_server',
#             f'{ns}/bt_navigator'
#         ])

#     # Lifecycle manager: delayed start to allow TFs to populate
#     nodes.append(
#         TimerAction(
#             period=3.0,
#             actions=[
#                 Node(
#                     package='nav2_lifecycle_manager',
#                     executable='lifecycle_manager',
#                     name='lifecycle_manager_navigation',
#                     output='screen',
#                     parameters=[{
#                         'use_sim_time': use_sim_time,
#                         'autostart': True,
#                         'bond_timeout': 0.0,
#                         'node_names': lifecycle_nodes
#                     }]
#                 ),
#             Node(
#                 package='rviz2',
#                 executable='rviz2',
#                 name='rviz2',
#                 arguments=['-d', rviz_config_dir],
#                 parameters=[{'use_sim_time': use_sim_time}],
#                 output='screen')
#             ]
#         )
#     )



#     return nodes


# def generate_launch_description():
#     return LaunchDescription([
#         DeclareLaunchArgument('num_robots', default_value='2',
#                               description='Number of robots to launch'),
#         DeclareLaunchArgument('namespace_prefix', default_value='TB3',
#                               description='Namespace prefix, e.g., TB3 -> TB3_1, TB3_2, ...'),
#         DeclareLaunchArgument('base_robot', default_value='TB3_1',
#                               description='Base robot name used inside the template YAML'),
#         DeclareLaunchArgument('config_pkg', default_value='turtlebot3_gazebo',
#                               description='Package containing config/ and map/ dirs'),
#         DeclareLaunchArgument('map_file', default_value='default',
#                               description='Absolute path to map YAML. Use "default" to take <config_pkg>/map/map.yaml'),
#         OpaqueFunction(function=_launch_setup),
#     ])



# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# Argument-driven multi-robot Nav2 bringup.

# Args:
# - num_robots (int)           : number of robots (default: 3)
# - namespace_prefix (string)  : namespace prefix (default: TB3)
# - base_robot (string)        : base robot name whose YAML is the template (default: TB3_1)
# - config_pkg (string)        : package that holds the config/ and map/ dirs (default: turtlebot3_gazebo)
# - map_file (string)          : absolute path to map.yaml (default: <config_pkg>/map/map.yaml)

# Notes:
# - Generates per-robot param files: config/myslam_param_<NS>.yaml from config/myslam_param_<base_robot>.yaml
# - Does NOT touch TF.

# ### References ###

# # https://github.com/Kazimbalti/Multi_TB3/blob/main/src/path_planner_server/launch/multi_pathplanner.launch.py
# # https://app.theconstruct.ai/open-classes/ca4e2636-c3e1-4b14-8149-da1a193fcb0e/
# # https://github.com/robo-friends/m-explore-ros2/tree/main

# """

# import os
# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument, OpaqueFunction
# from launch.substitutions import LaunchConfiguration
# from ament_index_python.packages import get_package_share_directory
# from launch_ros.actions import Node
# from launch_ros.substitutions import FindPackageShare
# from launch.substitutions import PathJoinSubstitution


# def _generate_param_files(base_template_path: str, output_dir: str, base_name: str,
#                           namespace_prefix: str, num_robots: int, base_robot: str, log=print):
#     """Create myslam_param_<NS>.yaml for robots 2..N by replacing base_robot tag in the template."""
#     if not os.path.isfile(base_template_path):
#         raise FileNotFoundError(f"Base template not found: {base_template_path}")

#     with open(base_template_path, 'r') as f:
#         base_content = f.read()

#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"
#         # Always generate (including TB3_1) so files are guaranteed to exist & up-to-date
#         updated = base_content.replace(base_robot, ns)
#         out_path = os.path.join(output_dir, f'{base_name}_{ns}.yaml')
#         with open(out_path, 'w') as f:
#             f.write(updated)
#         log(f'✅ Generated/updated param file: {out_path}')


# def _launch_setup(context, *args, **kwargs):
#     # Resolve args
#     num_robots        = int(LaunchConfiguration('num_robots').perform(context))
#     namespace_prefix  = LaunchConfiguration('namespace_prefix').perform(context)
#     base_robot        = LaunchConfiguration('base_robot').perform(context)
#     config_pkg        = LaunchConfiguration('config_pkg').perform(context)
#     map_file_cli      = LaunchConfiguration('map_file').perform(context)
#     use_sim_time = True
#     # Paths
#     pkg_share  = get_package_share_directory(config_pkg)
#     config_dir = os.path.join(pkg_share, 'config')
#     base_file  = os.path.join(config_dir, f'myslam_param_{base_robot}.yaml')
#     base_output_name = 'myslam_param'

#     # Map file: if user didn’t pass, default to <pkg>/map/map.yaml
#     default_map_path = os.path.join(pkg_share, 'map', 'map.yaml')
#     # default_map_path = "/home/urvish/ros2_ws/map_vicon_space/map_vicon_space.yaml"
#     print("-------------------------------------------------------")
#     print(default_map_path)
#     print("-------------------------------------------------------")
#     map_file = map_file_cli if map_file_cli and map_file_cli.lower() != 'default' else default_map_path

#     # Generate per-robot param files
#     def _log(msg):  # use launch logging format
#         print(msg, flush=True)
#     _generate_param_files(
#         base_template_path=base_file,
#         output_dir=config_dir,
#         base_name=base_output_name,
#         namespace_prefix=namespace_prefix,
#         num_robots=num_robots,
#         base_robot=base_robot,
#         log=_log
#     )

#     nodes = []

#     # Shared map server
#     nodes.append(
#         Node(
#             package='nav2_map_server',
#             executable='map_server',
#             name='map_server',
#             output='screen',
#             parameters=[{
#                 'use_sim_time': use_sim_time,
#                 'topic_name': 'map',
#                 'frame_id': 'map',
#                 'yaml_filename': map_file
#             }]
#         )
#     )

#     lifecycle_nodes = ['map_server']

#     # Per-robot Nav2 stack
#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"
#         config_file = os.path.join(config_dir, f'{base_output_name}_{ns}.yaml')

#         nodes += [
#             Node(
#                 namespace=ns,
#                 package='nav2_amcl',
#                 executable='amcl',
#                 name='amcl',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_controller',
#                 executable='controller_server',
#                 name='controller_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_planner',
#                 executable='planner_server',
#                 name='planner_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_behaviors',
#                 executable='behavior_server',
#                 name='behavior_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_bt_navigator',
#                 executable='bt_navigator',
#                 name='bt_navigator',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#         ]

#         lifecycle_nodes.extend([
#             f'{ns}/amcl',
#             f'{ns}/planner_server',
#             f'{ns}/controller_server',
#             f'{ns}/behavior_server',
#             f'{ns}/bt_navigator'
#         ])

#     # Lifecycle manager for navigation stack
#     nodes.append(
#         Node(
#             package='nav2_lifecycle_manager',
#             executable='lifecycle_manager',
#             name='lifecycle_manager_navigation',
#             output='screen',
#             parameters=[{
#                 'use_sim_time': use_sim_time,
#                 'autostart': True,
#                 'bond_timeout': 0.0,
#                 'node_names': lifecycle_nodes
#             }]
#         )
#     )

#     return nodes


# def generate_launch_description():
#     # Declare args
#     return LaunchDescription([
#         DeclareLaunchArgument('num_robots',        default_value='1',
#                               description='Number of robots to launch'),
#         DeclareLaunchArgument('namespace_prefix',  default_value='TB3',
#                               description='Namespace prefix, e.g., TB3 -> TB3_1, TB3_2, ...'),
#         DeclareLaunchArgument('base_robot',        default_value='TB3_1',
#                               description='Base robot name used inside the template YAML'),
#         DeclareLaunchArgument('config_pkg',        default_value='turtlebot3_gazebo',
#                               description='Package containing config/ and map/ dirs'),
#         DeclareLaunchArgument('map_file',          default_value='default',
#                               description='Absolute path to map YAML. Use "default" to take <config_pkg>/map/map.yaml'),
#         OpaqueFunction(function=_launch_setup),
#     ])





# '''
# ### References ###

# # https://github.com/Kazimbalti/Multi_TB3/blob/main/src/path_planner_server/launch/multi_pathplanner.launch.py
# # https://app.theconstruct.ai/open-classes/ca4e2636-c3e1-4b14-8149-da1a193fcb0e/
# # https://github.com/robo-friends/m-explore-ros2/tree/main

# '''
# import os
# from ament_index_python.packages import get_package_share_directory
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_param_files(template_path, output_dir, base_name, num_robots):
#     """
#     Generate myslam_param_TB3_X.yaml files from a template.
#     Only generates TB3_2 and beyond; TB3_1 should already exist.
#     """
#     with open(template_path, 'r') as f:
#         base_content = f.read()

#     for i in range(2, num_robots + 1):
#         robot_ns = f'TB3_{i}'
#         updated_content = base_content.replace('TB3_1', robot_ns)
#         output_path = os.path.join(output_dir, f'{base_name}_{robot_ns}.yaml')
#         with open(output_path, 'w') as f:
#             f.write(updated_content)
#         print(f'✅ Generated param file: {output_path}')

# def generate_launch_description():
#     num_robots = 1
#     namespace_prefix = 'TB3'
#     base_robot = 'TB3_1'
#     config_pkg = 'turtlebot3_gazebo'

#     config_dir = os.path.join(get_package_share_directory(config_pkg), 'config')
#     base_file = os.path.join(config_dir, f'myslam_param_{base_robot}.yaml')
#     base_output_name = 'myslam_param'

#     # 🔧 Generate param files if needed
#     generate_param_files(base_file, config_dir, base_output_name, num_robots)

#     launch_nodes = []

#     # Shared map server
#     map_file  = '/home/urvish/ros2_ws/src/turtlebot3_gazebo/map/map.yaml'
#     # map_file = os.path.join(get_package_share_directory(config_pkg), 'map', 'map.yaml')
#     launch_nodes.append(
#         Node(
#             package='nav2_map_server',
#             executable='map_server',
#             name='map_server',
#             output='screen',
#             parameters=[{
#                 'use_sim_time': True,
#                 'topic_name': 'map',
#                 'frame_id': 'map',
#                 'yaml_filename': map_file
#             }]
#         )
#     )

#     lifecycle_nodes = ['map_server']

#     for i in range(1, num_robots + 1):
#         ns = f"{namespace_prefix}_{i}"
#         config_file = os.path.join(config_dir, f'myslam_param_{ns}.yaml')

#         launch_nodes += [
#             Node(
#                 namespace=ns,
#                 package='nav2_amcl',
#                 executable='amcl',
#                 name='amcl',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_controller',
#                 executable='controller_server',
#                 name='controller_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_planner',
#                 executable='planner_server',
#                 name='planner_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_behaviors',
#                 executable='behavior_server',
#                 name='behavior_server',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#             Node(
#                 namespace=ns,
#                 package='nav2_bt_navigator',
#                 executable='bt_navigator',
#                 name='bt_navigator',
#                 output='screen',
#                 parameters=[config_file]
#             ),
#         ]

#         lifecycle_nodes.extend([
#             f'{ns}/amcl',
#             f'{ns}/controller_server',
#             f'{ns}/planner_server',
#             f'{ns}/behavior_server',
#             f'{ns}/bt_navigator'
#         ])

#     # Lifecycle manager
#     launch_nodes.append(
#         Node(
#             package='nav2_lifecycle_manager',
#             executable='lifecycle_manager',
#             name='lifecycle_manager_navigation',
#             output='screen',
#             parameters=[{
#                 'use_sim_time': True,
#                 'autostart': True,
#                 'bond_timeout': 0.0,
#                 'node_names': lifecycle_nodes
#             }]
#         )
#     )

#     return LaunchDescription(launch_nodes)
