import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, AppendEnvironmentVariable,
                            IncludeLaunchDescription, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    gz_extra = LaunchConfiguration('gz_extra')

    warehouse_dir = get_package_share_directory('warehouse_world')
    tb3_dir = get_package_share_directory('turtlebot3_gazebo')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')

    world = os.path.join(warehouse_dir, 'worlds', 'warehouse_storage.sdf')

    model_sdf = os.path.join(tb3_dir, 'models', 'turtlebot3_burger', 'model.sdf')
    urdf_file = os.path.join(tb3_dir, 'urdf', 'turtlebot3_burger.urdf')
    bridge_yaml = os.path.join(tb3_dir, 'params', 'turtlebot3_burger_bridge.yaml')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    # 1) Environment
    gz_env = [
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH',
                                  os.path.join(warehouse_dir, 'worlds')),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH',
                                  os.path.join(warehouse_dir, 'models')),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH',
                                  os.path.join(tb3_dir, 'models')),
    ]

    # 2) Gazebo server + world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', gz_extra, ' ', world],
            'on_exit_shutdown': 'true',
        }.items())

    # 3) robot_state_publisher (no frame_prefix)
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc,
        }])

    # 4) Spawn
    spawn_tb3 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'turtlebot3_burger',
                   '-file', model_sdf,
                   '-x', x_pose, '-y', y_pose, '-z', '0.01'],
        output='screen')

    # 5) Robot bridge (clock, tf, odom, scan, imu, joint_states, cmd_vel)
    robot_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='turtlebot3_bridge',
        parameters=[{'config_file': bridge_yaml,
                     'use_sim_time': use_sim_time}],
        output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x_pose', default_value='-3.0'),
        DeclareLaunchArgument('y_pose', default_value='0.0'),
        DeclareLaunchArgument('gz_extra', default_value=''),

        *gz_env,
        gz_sim,
        rsp,
        robot_bridge,
        TimerAction(period=5.0, actions=[spawn_tb3]),
    ])