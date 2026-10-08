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
        default_value=os.path.join(bringup_dir, "maps", "lab3.yaml"),
        description="Full path to map yaml file"
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz", default_value="False"
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

    # ===== map->odom 静态 TF（关闭 AMCL，先让 map 与 odom 完全一致） =====
    static_map_odom_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_odom_static_tf",
        output="screen",
        arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
    )

    # ===== nav2 导航节点 =====
    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
        remappings=[("cmd_vel", "/cmd_vel_nav")],   # ← 加这一行
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
        # 恢复行为的速度也必须走 /cmd_vel_nav，否则会绕过 fake_vel_transform
        # 直接发到 /cmd_vel —— 既不叠 /cmd_spin，坐标系也是错的。
        remappings=[("cmd_vel", "/cmd_vel_nav")],
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
    # 速度平滑器：controller/behavior 的 /cmd_vel_nav -> /cmd_vel_nav_smoothed，
    # 20Hz 持续发布（空闲时发 0），保证 fake_vel_transform 下游永不静默。
    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml")],
        remappings=[("cmd_vel", "/cmd_vel_nav"),
                    ("cmd_vel_smoothed", "/cmd_vel_nav_smoothed")],
    )
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager",
        output="screen",
        parameters=[os.path.join(bringup_dir, "config", "nav2_params.yaml"),
                    {"autostart": autostart},
        {"node_names": [
            "map_server",
            "controller_server", "planner_server", "smoother_server",
            "behavior_server", "bt_navigator", "waypoint_follower",
            "velocity_smoother"
        ]}]
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

    # ===== ros2_comm 底盘通讯 =====
    ros2_comm_node = Node(
        package="ros2_comm",
        executable="ros2_comm_node",
        name="ros2_comm_node",
        output="screen",
        emulate_tty=True,
    )

    fake_vel_transform_node = Node(
    package="fake_vel_transform",
    executable="fake_vel_transform_node",
    name="fake_vel_transform",
    output="screen",
    parameters=[os.path.join(bringup_dir, "config", "fake_vel_transform.yaml")],
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
    ld.add_action(static_map_odom_tf)
    ld.add_action(planner_server)
    ld.add_action(controller_server)
    ld.add_action(smoother_server)
    ld.add_action(behavior_server)
    ld.add_action(bt_navigator)
    ld.add_action(waypoint_follower)
    ld.add_action(velocity_smoother)
    ld.add_action(lifecycle_manager)
    ld.add_action(fake_vel_transform_node)
    ld.add_action(ros2_comm_node)

    ld.add_action(rviz)
    return ld