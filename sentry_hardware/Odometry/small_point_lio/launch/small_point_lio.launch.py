'''
Author: maple0738 1573764313@qq.com
Date: 2026-09-01 21:39:59
LastEditors: maple0738 1573764313@qq.com
LastEditTime: 2026-09-02 19:24:19
FilePath: /my_sentry_nav/sentry_hardware/Odometry/small_point_lio/launch/small_point_lio.launch.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    small_point_lio_node = Node(
        package="small_point_lio",
        executable="small_point_lio_node",
        name="small_point_lio",
        output="screen",
        parameters=[
            PathJoinSubstitution(
                [
                    FindPackageShare("small_point_lio"),
                    "config",
                    "mid360.yaml",
                ]
            )
        ],
    )

    static_base_link_to_livox_frame = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0.0",
            "--y",
            "0.0",
            "--z",
            "0.0",
            "--roll",
            "0.0",
            "--pitch",
            "0.0",
            "--yaw",
            "0.0",
            "--frame-id",
            "base_link",
            "--child-frame-id",
            "livox_frame",
        ],
    )

    return LaunchDescription([small_point_lio_node])
