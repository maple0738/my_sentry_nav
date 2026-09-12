'''
Author: maple0738 1573764313@qq.com
Date: 2026-08-28 17:02:49
LastEditors: maple0738 1573764313@qq.com
LastEditTime: 2026-08-28 18:16:25
FilePath: /my_sentry_nav/sentry_description/launch/view_model.launch.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_name = 'sentry_description'
    urdf_name = "mas2027_sentry.urdf"

    # 获取包的路径
    pkg_share = get_package_share_directory(package_name)
    urdf_model_path = os.path.join(pkg_share, 'urdf', urdf_name)

    with open(urdf_model_path, 'r') as f:
        robot_desc = f.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}]
    )

    return LaunchDescription([
        robot_state_publisher_node
    ])