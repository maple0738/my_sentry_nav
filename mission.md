<!--
 * @Author: maple0738 1573764313@qq.com
 * @Date: 2026-08-28 15:30:32
 * @LastEditors: maple0738 1573764313@qq.com
 * @LastEditTime: 2026-09-01 21:53:37
 * @FilePath: /my_sentry_nav/mission.md
-->

# ⚠️ 最高优先级规则

**只给建议和分析，不要改动任何代码/文件，除非我明确要求你改。**

# 任务：从零搭建哨兵导航系统

## 项目位置
- 项目目录：`/home/gyx/my_sentry_nav`
- 宿主机目录：`~/my_sentry_nav`
- 容器内工作空间：`/home/my_sentry_ws`
- 容器名：`my_sentry`
- 进入容器：`sudo docker exec -it my_sentry bash --login`

## 整体目标

### 第一阶段：跑通基础链路（当前）
用 `mas_nav_2027` 的现有代码，快速搭建并测试完整导航链路：
雷达驱动 → 里程计 → 建图 → 导航

目标：**先跑通，理解每个模块的输入输出和数据流，积累实操经验。**

### 第二阶段：替换自研模块（后续）
在理解基础链路后，逐个模块替换为自研代码：
- 用自研算法替换 small_point_lio
- 用自研规划器替换 nav2
- 自研决策层等

目标：**从"会用"到"会写"，掌握核心算法。**

## 开发笔记
- 详细记录在 `note.md`（包含所有操作步骤、命令、踩坑记录）
- 附录 1：开发机 ↔ Mini PC 文件传输
- 附录 2：Mini PC 连接雷达全流程

## 已完成进度

### ✅ 第 0 步：项目初始化 + Docker 环境
- Dockerfile + docker-compose.yml 已配置
- Dockerfile 已添加依赖：`ros-humble-asio-cmake-module`、`ros-humble-ament-cmake-auto`、`libomp-dev` 等
- 容器内编译环境就绪

### ✅ 第 1 步：my_interfaces 消息包
- 包含 `ChassisCmd.msg`
- 已编译通过

### ✅ 第 2 步：sentry_description 模型包
- URDF 文件：`mas2027_sentry.urdf`
- TF 树：`base_link → {base_footprint, lidar_link, lakibeam_frame, chassis_link}`
- launch 文件：`view_model.launch.py`（启动 robot_state_publisher）
- 已编译通过，RViz 可视化正常

### ✅ 第 3 步：mid360_driver 雷达驱动
- 已从 `mas_nav_2027` 复制到 `sentry_hardware/mid360_driver/`
- 架构：`mid360_driver.cpp`（底层 UDP 协议解析）+ `mid360_driver_node.cpp`（ROS2 节点层）
- 依赖 ASIO 网络库 + C++20 协程
- 话题：`/mid360_driver/lidar`（PointCloud2）、`/mid360_driver/imu`（Imu）
- 已编译通过，Mini PC 实测点云数据正常接收 ✅

### ✅ 第 4 步：small_point_lio 点云里程计
- 已从 `mas_nav_2027` 复制到 `sentry_hardware/Odometry/small_point_lio/`
- 算法：ESKF（误差状态卡尔曼）+ small_ivox（体素地图）
- 已编译通过 ✅

### ✅ 第 5 步：small_point_lio 配置适配
- `config/mid360.yaml`：话题名 `lidar_topic→/mid360_driver/lidar`，`lidar_type→custom_mid360_driver`，`lidar_frame→lidar_link`
- `launch/small_point_lio.launch.py`：删除冗余 `static_base_link_to_livox_frame` 节点
- 实测：`odom→base_link` TF 正常，`/cloud_registered` 点云拼接正常 ✅

### ✅ 第 6 步：sentry_bringup 启动编排包
- 创建 `sentry_bringup/` 包（CMakeLists.txt + package.xml）
- 配置 `config/slam_toolbox_mapping.yaml`：pointcloud_to_laserscan + slam_toolbox 参数
- 编写 `launch/mapping_launch.py`：一键启动 robot_state_publisher + mid360_driver + small_point_lio + pointcloud_to_laserscan + slam_toolbox + rviz2
- 无雷达情况下节点均正常启动（除 mid360_driver 因没接雷达报 bind 错误，预期行为）✅
- 需要安装：`sudo apt install ros-humble-pointcloud-to-laserscan`（宿主机）/ Docker 内已自带

## 参考项目
- 项目A（完整版）：`/home/gyx/mas_nav_2027`
- 项目B（早期版）：`/home/gyx/ph_sentry_nav_ws/src/mas_nav`

## 下一步任务

### 第 7 步：实测建图（最优先）
- 连接 Mini PC 雷达
- `ros2 launch sentry_bringup mapping_launch.py` 一键启动
- 手持雷达走一圈场地
- RViz 观察 `/map` 栅格地图 + `map→odom` TF
- 保存地图：`ros2 run nav2_map_server map_saver_cli -f ~/my_map`
- 输出 `my_map.pgm` + `my_map.yaml`

### 第 8 步：底盘通讯（需要写代码）
- 订阅 `/cmd_vel` → 转发给电机底层控制器
- 需要配合已有的底层电机控制逻辑

### 第 9 步：nav2 导航
- 创建 `sentry_bringup/config/nav2_params.yaml`
- 创建 `sentry_bringup/launch/nav_launch.py`
- 组件：map_server + amcl + planner_server + controller_server + bt_navigator + behavior_server
- 先用 nav2 默认算法跑通链路，后续替换自研插件

## 编译命令
```bash
# 容器内
cd /home/my_sentry_ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
# 或指定包
colcon build --packages-select small_point_lio --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

## 运行验证
- 容器内：`ros2 topic list` 查看话题
- 启动 robot_state_publisher：`ros2 launch sentry_description view_model.launch.py`
- 启动雷达：`ros2 launch mid360_driver mid360_driver.launch.py`
- 宿主机 X11：`xhost +si:localuser:root` 后容器内可开 RViz
- 每次新终端要 source：`source /home/my_sentry_ws/install/setup.bash`