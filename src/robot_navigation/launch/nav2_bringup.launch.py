import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    pkg_share = get_package_share_directory('robot_navigation')

    amcl_yaml = os.path.join(pkg_share, 'config', 'amcl.yaml')
    planner_yaml = os.path.join(pkg_share, 'config', 'planner_server.yaml')
    controller_yaml = os.path.join(pkg_share, 'config', 'controller_server.yaml')
    behavior_yaml = os.path.join(pkg_share, 'config', 'behavior_server.yaml')
    bt_navigator_yaml = os.path.join(pkg_share, 'config', 'bt_navigator.yaml')

    # The map we saved in the SLAM step
    map_file = os.path.join(pkg_share, 'map', 'turtlebot3_world_map.yaml')

    # RViz config saved inside the package: robot_navigation/rviz/navigation.rviz
    rviz_config = os.path.join(pkg_share, 'rviz', 'navigation.rviz')

    # Map Server - provides the static map
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_file}
        ]
    )

    # AMCL - Adaptive Monte Carlo Localization
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[amcl_yaml, {'use_sim_time': use_sim_time}]
    )

    # Planner Server - computes global paths
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[planner_yaml, {'use_sim_time': use_sim_time}]
    )

    # Controller Server - generates velocity commands on /cmd_vel
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[controller_yaml, {'use_sim_time': use_sim_time}]
    )

    # Behavior Server - runs recovery behaviors
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[behavior_yaml, {'use_sim_time': use_sim_time}]
    )

    # BT Navigator - manages the navigation flow using Behavior Trees
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[bt_navigator_yaml, {'use_sim_time': use_sim_time}]
    )

    # Lifecycle Manager - activates all navigation nodes in the right order
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': [
                'map_server',
                'amcl',
                'planner_server',
                'controller_server',
                'behavior_server',
                'bt_navigator'
            ]}
        ]
    )

    # RViz - opens with the saved navigation.rviz config
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        map_server,
        amcl,
        planner_server,
        controller_server,
        behavior_server,
        bt_navigator,
        lifecycle_manager,
        rviz
    ])