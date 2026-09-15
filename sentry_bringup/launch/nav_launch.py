import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    bringup_dir = get_package_share_directory("sentry_bringup")
    sentry_description_dir = get_package_share_directory("sentry_description")
    small_point_lio_dir = get_package_share_directory("small_point_lio")
    mid360_driver_dir = get_package_share_directory("mid360_driver")

    # ===== 参数声明 =====
    map_yaml = LaunchConfiguration("map")
    use_rviz = LaunchConfiguration("use_rviz")
    autostart = LaunchConfiguration("autostart")

    declare_map = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(bringup_dir, "map", "my_map.yaml"),
        description="Full path to map yaml file"
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz", default_value="True"
    )
    declare_autostart = DeclareLaunchArgument(
        "autostart", default_value="True",
        description="Auto-activate nav2 lifecycle nodes"
    )

    # ===== 加载地图的 map_server =====
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml"),
                    {"yaml_filename": map_yaml}],
    )

    # ===== AMCL 定位 =====
    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )

    # ===== nav2 导航节点 =====
    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    smoother_server = Node(
        package="nav2_smoother",
        executable="smoother_server",
        name="smoother_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
    )
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml"),
                    {"autostart": autostart},
                    {"node_names": [
                        "controller_server", "planner_server", "smoother_server",
                        "behavior_server", "bt_navigator", "waypoint_follower",
                        "velocity_smoother", "map_server", "amcl"
                    ]}],
    )

    # ===== 底层：robot_state_publisher + driver + LIO + pointcloud_to_laserscan =====
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sentry_description_dir, "launch", "view_model.launch.py")
        ),
    )
    mid360_driver = Node(
        package="mid360_driver",
        executable="mid360_driver_node",
        name="mid360_driver",
        output="screen",
        parameters=[os.path.join(mid360_driver_dir, "config", "params.yaml")],
    )
    small_point_lio = Node(
        package="small_point_lio",
        executable="small_point_lio_node",
        name="small_point_lio",
        output="screen",
        parameters=[os.path.join(small_point_lio_dir, "config", "mid360.yaml")],
    )
    pointcloud_to_laserscan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        output="screen",
        parameters=[os.path.join(
            bringup_dir, "config", "slam_toolbox_mapping.yaml"
        )],
        remappings=[("cloud_in", "/cloud_registered"), ("scan", "/scan")],
    )

    # ===== RViz =====
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        condition=IfCondition(use_rviz),
    )

    ld = LaunchDescription()
    ld.add_action(declare_map)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_autostart)

    # 底层
    ld.add_action(robot_state_publisher)
    ld.add_action(mid360_driver)
    ld.add_action(small_point_lio)
    ld.add_action(pointcloud_to_laserscan)

    # 导航
    ld.add_action(map_server)
    ld.add_action(amcl)
    ld.add_action(planner_server)
    ld.add_action(controller_server)
    ld.add_action(smoother_server)
    ld.add_action(behavior_server)
    ld.add_action(bt_navigator)
    ld.add_action(waypoint_follower)
    ld.add_action(velocity_smoother)
    ld.add_action(lifecycle_manager)

    ld.add_action(rviz)
    return ld