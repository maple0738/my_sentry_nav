'''
Author: maple0738 1573764313@qq.com
Date: 2026-09-22 16:43:37
LastEditors: maple0738 1573764313@qq.com
LastEditTime: 2026-09-22 16:43:45
FilePath: /my_sentry_nav/sentry_bringup/launch/test_radar_launch.py
Description: 
'''
'''
Description: 雷达数据测试（sentry_description + mid360_driver + small_point_lio）
'''
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def generate_launch_description():
    sentry_description_dir = get_package_share_directory("sentry_description")
    small_point_lio_dir = get_package_share_directory("small_point_lio")
    mid360_driver_dir = get_package_share_directory("mid360_driver")

    # ===== 声明参数 =====
    use_rviz = LaunchConfiguration("use_rviz")
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz", default_value="True", description="Whether to start RViz"
    )

    # ===== 1. robot_state_publisher =====
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sentry_description_dir, "launch", "view_model.launch.py")
        ),
    )

    # ===== 2. mid360_driver =====
    mid360_driver = Node(
        package="mid360_driver",
        executable="mid360_driver_node",
        name="mid360_driver",
        output="screen",
        parameters=[os.path.join(
            mid360_driver_dir, "config", "params.yaml"
        )],
    )

    # ===== 3. small_point_lio =====
    small_point_lio = Node(
        package="small_point_lio",
        executable="small_point_lio_node",
        name="small_point_lio",
        output="screen",
        parameters=[os.path.join(
            small_point_lio_dir, "config", "mid360.yaml"
        )],
    )

    # ===== 4. rviz2 =====
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        condition=IfCondition(use_rviz),    
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_rviz)
    ld.add_action(robot_state_publisher)
    ld.add_action(mid360_driver)
    ld.add_action(small_point_lio)
    ld.add_action(rviz)
    return ld