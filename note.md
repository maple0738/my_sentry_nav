<!--
 * @Author: maple0738 1573764313@qq.com
 * @Date: 2026-08-28 15:14:39
 * @LastEditors: maple0738 1573764313@qq.com
 * @LastEditTime: 2026-09-12 23:33:00
 * @FilePath: /my_sentry_nav/note.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# 开发笔记

## 附录 1：开发机 ↔ Mini PC 文件传输

### A.1 查看网口信息（ifconfig）
```bash
# 目标机器上执行
ifconfig        # 显示所有活动网络接口
ifconfig -a     # 显示所有接口（含不活动的 + IPv6）
```

网口命名规则：
| 前缀 | 含义 | 示例 |
|------|------|------|
| `enp` | 有线以太网口 | `enp2s0`、`eno1` |
| `wlp` | 无线 WiFi 网口 | `wlp3s0` |
| `lo` | 本地环回接口 | `127.0.0.1` |
| `docker0` | Docker 网桥 | `172.17.0.1` |

### A.2 测试网络连通性（ping）
```bash
# 开发机上执行，测试能否连到 Mini PC
ping 192.168.77.7
# 有数据返回 = 已连通
```

### A.3 传输文件（scp）
```bash
# 从开发机传给 Mini PC
scp -r /本地/文件/路径 用户名@Mini_PC_IP:/远程/目标/路径

# 示例：把 my_sentry_nav 整个项目传到 Mini PC
scp -r ~/my_sentry_nav mas@192.168.77.7:/home/mas/
```

参数说明：
| 参数 | 含义 |
|------|------|
| `scp` | Secure Copy，通过 SSH 安全复制 |
| `-r` | 递归复制整个目录 |
| `用户名@IP` | 目标机器登录用户和 IP |
| `:/路径` | 目标机器存放位置 |

> **注意**：如果用 `scp` 传整个项目，`build/`、`install/`、`log/` 是命名卷，不在宿主机目录里。Mini PC 上需要重新 `docker compose up -d --build` 并编译。

---

## 附录 2：Mini PC 连接雷达全流程

### 5.1 硬件准备
```bash
# 1. 查看有线网口名称
ip addr
# 输出示例：eno1 / enp2s0 / eth0

# 2. 配置网口 IP（必须和 params.yaml 的 host_ip 一致）
sudo ip addr add 192.168.1.50/24 dev eno1

# 3. 插雷达网线到该网口 + 插供电线
```

### 5.2 网络说明
```
host_ip: 192.168.1.50    ← 驱动监听这个地址
雷达出厂设定：往 192.168.1.50 发 UDP 数据
mini PC 网口：必须配成 192.168.1.50 才能收到
```

| 网口 | IP | 用途 |
|------|-----|------|
| WiFi（wlp3s0） | 192.168.77.7 | 远程 SSH 连接 |
| 有线（eno1） | 192.168.1.50 | 插雷达 |
| Docker（docker0） | 172.17.0.1 | 容器网桥，不用管 |

### 5.3 构建 + 编译
```bash
# 1. 构建 Docker 镜像（Dockerfile 已包含所有依赖）
cd ~/my_sentry_nav
sudo docker compose up -d --build

# 2. 进入容器，编译
sudo docker exec -it my_sentry bash --login
cd /home/my_sentry_ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

### 5.4 启动运行
```bash
# 终端 1：启动 robot_state_publisher（发布 TF 树）
source /home/my_sentry_ws/install/setup.bash
ros2 launch sentry_description view_model.launch.py

# 终端 2：启动雷达驱动
source /home/my_sentry_ws/install/setup.bash
ros2 launch mid360_driver mid360_driver.launch.py
```

### 5.5 验证 + 可视化
```bash
# 终端 3：验证数据
source /home/my_sentry_ws/install/setup.bash
ros2 topic echo /mid360_driver/lidar --no-arr

# RViz 可视化
# ⚠️ 必须先 source，否则 rviz2 找不到 meshes/ 等资源
source /home/my_sentry_ws/install/setup.bash
rviz2
# Fixed Frame: base_link
# Add → By topic → /mid360_driver/lidar → PointCloud2
```

### 5.6 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `Authorization required, no protocol specified` | 宿主机没授权 X11 | 宿主机执行 `xhost +si:localuser:root` |
| `Package [sentry_description] does not exist` | 没 source 工作空间 | 先 `source install/setup.bash` 再 `rviz2` |
| 每次新开终端都要 source | bashrc 没配 | 容器内执行 `echo 'source /home/my_sentry_ws/install/setup.bash' >> ~/.bashrc` |

### 5.7 一键流程总结
```
配IP → 插雷达 → 启容器 → 编译 → 启TF → 启驱动 → 看数据
```

---

## 第 0 步：项目初始化 + Docker 环境

### 0.1 创建项目目录
```bash
mkdir -p ~/my_sentry_nav
cd ~/my_sentry_nav
```

### 0.2 复制 Dockerfile
```bash
cp /home/gyx/mas_nav_2027/Dockerfile .
```

修改 `Dockerfile`：
- 将 `WORKDIR /home/ros2_ws` 改为 `WORKDIR /home/my_sentry_ws`
- 将 `RUN mkdir -p /home/ros2_ws/src ...` 改为 `RUN mkdir -p /home/my_sentry_ws/src ...`

### 0.3 创建 docker-compose.yml
```yaml
services:
  my_sentry_nav:
    build:
      context: .
      dockerfile: Dockerfile
      network: host
    image: my_sentry_image:latest
    container_name: my_sentry
    stdin_open: true
    tty: true
    network_mode: host
    ipc: host
    pid: host
    privileged: true
    environment:
      - DISPLAY=${DISPLAY}
      - QT_X11_NO_MITSHM=1
      - ROS_DOMAIN_ID=0
      - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ${HOME}/.Xauthority:/root/.Xauthority:rw
      - ./:/home/my_sentry_ws/src
      - my_sentry-build:/home/my_sentry_ws/build
      - my_sentry-install:/home/my_sentry_ws/install
      - my_sentry-log:/home/my_sentry_ws/log

volumes:
  my_sentry-build:
  my_sentry-install:
  my_sentry-log:
```

### 0.4 构建容器
```bash
sudo docker compose up -d --build
```

### 0.5 进入容器
```bash
sudo docker exec -it my_sentry bash --login
# 进去后确认环境
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO
# 应该输出: humble
```

### 0.6 X11 图形界面验证（宿主机执行）
```bash
xhost +si:localuser:root
```

### 完成状态
✅ Docker 容器构建成功  
✅ 容器内 ROS 2 环境正常  
✅ 工作空间目录结构：
```
/home/my_sentry_ws/
├── src/      (宿主机 ~/my_sentry_nav/ → 挂载到这里)
├── build/
├── install/
└── log/
```

---

## 第 1 步：创建 my_interfaces 消息包

### 1.1 创建包骨架
```bash
cd ~/my_sentry_nav
ros2 pkg create --build-type ament_cmake my_interfaces
```

### 1.2 目录结构
```
my_interfaces/
├── msg/
│   └── ChassisCmd.msg       ← 底盘控制命令
├── CMakeLists.txt
└── package.xml
```

### 1.3 CMakeLists.txt 要点
- 使用 `ament_cmake` + `rosidl_default_generators`（不能用 `ament_cmake_auto`，容器里没装）
- 手动 `find_package` 每个依赖
- `rosidl_generate_interfaces` 注册 msg 文件

### 1.4 package.xml 要点
- 加 `<build_depend>rosidl_default_generators</build_depend>`
- 加 `<exec_depend>rosidl_default_runtime</exec_depend>`
- 加 `<member_of_group>rosidl_interface_packages</member_of_group>`
- 加 `builtin_interfaces`、`geometry_msgs` 等依赖

### 1.5 ChassisCmd.msg 内容
```msg
float32 velocity
float32 omega
uint8 mode         # 0~11 导航模式，200~207 腿长模式
uint8 step_dist    # 台阶距离（仅台阶模式有效）
```

---

## 第 2 步：创建 sentry_description 机器人描述包

### 2.1 创建包 + 复制资源
```bash
cd ~/my_sentry_nav
ros2 pkg create --build-type ament_cmake sentry_description
cp -r /home/gyx/ph_sentry_nav_ws/src/mas_nav/sentry_description/{urdf,meshes,launch} sentry_description/
cp /home/gyx/ph_sentry_nav_ws/src/mas_nav/sentry_description/CMakeLists.txt sentry_description/
cp /home/gyx/ph_sentry_nav_ws/src/mas_nav/sentry_description/package.xml sentry_description/
```

### 2.2 需要修改的地方
- **launch/view_model.launch.py**：`urdf_name` 改为 `"mas2027_sentry.urdf"`
- **CMakeLists.txt** 和 **package.xml** 包名已为 `sentry_description`，可直接用

### 2.3 目录结构
```
sentry_description/
├── launch/view_model.launch.py
├── meshes/{mid360,base_link,LakiBeam}.STL
├── urdf/mas2027_sentry.urdf
├── CMakeLists.txt
└── package.xml
```

---

## 第 3 步：编译与验证

### 3.1 编译命令
```bash
sudo docker exec -it my_sentry bash --login
cd /home/my_sentry_ws

# 全量编译
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4

# 或指定包编译（更快）
colcon build --symlink-install --packages-select my_interfaces --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4
```

### 3.2 常见编译错误
| 错误 | 原因 | 解决 |
|------|------|------|
| `find_package(ament_cmake_auto)` 找不到 | 容器没装 `ament_cmake_auto` | 改用标准 `ament_cmake` + `rosidl_default_generators` 手动写法 |
| `failed to create symbolic link` | 旧 build 产物冲突 | `rm -rf build/包名 install/包名` 后重新编译 |

### 3.3 验证命令
```bash
source install/setup.bash

# 验证消息包
ros2 interface show my_interfaces/msg/ChassisCmd
ros2 interface list | grep ChassisCmd

# 验证机器人模型
ros2 launch sentry_description view_model.launch.py

# 宿主机授权 GUI
xhost +si:localuser:root
```

### 3.4 RViz 显示
- RViz 必须在**容器内**启动，否则找不到 `package://` 资源
- 添加 `RobotModel` 显示机器人模型
- 添加 `TF` 显示坐标系，Fixed Frame 设为 `base_footprint`

---

## 第 4 步：添加 MID360 雷达驱动

### 4.1 复制驱动包
```bash
cd ~/my_sentry_nav
mkdir -p sentry_hardware
cp -r /home/gyx/mas_nav_2027/mas2027_perception/mid360_driver sentry_hardware/
```

### 4.2 驱动架构分析

| 文件 | 作用 |
|------|------|
| `launch/mid360_driver.launch.py` | 启动节点，加载参数 |
| `config/params.yaml` | 雷达配置（IP、话题、坐标系等） |
| `src/mid360_driver.cpp` | 底层驱动：UDP 接收 + 二进制协议解析 + CRC 校验 |
| `src/mid360_driver_node.cpp` | ROS2 节点层：创建 publisher、定时器、对接 ROS2 |
| `include/mid360_driver/mid360_driver.hpp` | 驱动类声明 + 数据结构定义 |

**数据流**：
```
MID360 雷达 → UDP 数据包 → ASIO 网络层（端口 56301/56401）
  → mid360_driver.cpp 解析二进制 → Point + ImuMsg
  → LidarPublisher 双缓冲 → 定时器发布
  → /mid360_driver/lidar（PointCloud2）+ /mid360_driver/imu（Imu）
```

**关键设计**：双缓冲解耦
- IO 线程（高频）：收 UDP → 写 `wait_to_publish` 缓冲区
- 定时器线程（固定频率 50ms）：`prepare_xxx()` swap 缓冲区 → `publish_xxx()` 发布

### 4.3 依赖说明

| 依赖 | 作用 | 来源 |
|------|------|------|
| `asio_cmake_module` | ASIO 网络库的 CMake 封装 | UDP 收包必须 |
| `ament_cmake_auto` | CMake 自动构建工具 | mid360_driver 的 CMakeLists 使用 |
| `rclcpp` | ROS2 C++ 客户端库 | 节点、定时器、发布器 |
| `sensor_msgs` | 传感器消息类型 | PointCloud2、Imu |

### 4.4 Dockerfile 修改

在 `apt install` 列表末尾追加：
```dockerfile
    ros-humble-asio-cmake-module \
    ros-humble-ament-cmake-auto \
```

### 4.5 TF 树说明

**静态 TF**（URDF + robot_state_publisher 发布）：
```
base_link（根节点）
├── base_footprint   （地面投影）
├── lidar_link       （MID360 雷达，params.yaml 中 lidar_frame 设为此值）
├── lakibeam_frame   （LakiBeam 雷达）
└── chassis_link     （底盘）
```

**动态 TF**（运行时由算法发布，后续补）：
```
odom → base_link    （里程计，small_point_lio）
map → odom          （地图定位，slam_toolbox）
```

---

## 第 5 步：small_point_lio 配置适配与测试

### 5.1 修改 config/mid360.yaml
```yaml
small_point_lio:
    ros__parameters:
        lidar_topic: /mid360_driver/lidar       # 原 /livox/lidar
        imu_topic: /mid360_driver/imu           # 原 /livox/imu
        lidar_type: custom_mid360_driver         # 原 livox_custom_msg
        lidar_frame: lidar_link                  # 原 livox_frame
        save_pcd: false                          # 不保存点云
```

### 5.2 修改 launch/small_point_lio.launch.py
- 删除 `static_base_link_to_livox_frame` 节点（URDF 已用 robot_state_publisher 发布 TF，避免冲突）

### 5.3 测试验证
```bash
# 三个终端分别启动
ros2 launch sentry_description view_model.launch.py
ros2 launch mid360_driver mid360_driver.launch.py
ros2 launch small_point_lio small_point_lio.launch.py

# RViz 查看
# Fixed Frame: odom
# Add → By topic → /cloud_registered → PointCloud2
# Add → TF → odom → base_link
```

### 5.4 测试结果
- ✅ `odom → base_link` TF 动态更新正常
- ✅ `/cloud_registered` 点云拼接正常
- ✅ 里程计 `Decay Time` 设为 5s 可见历史轨迹
- ✅ `/cloud_registered` 和 `/cloud_registered_full` 话题存在，前者降采样、后者原始

---

## 第 6 步：创建 sentry_bringup 启动编排包

### 6.1 设计理念
sentry_bringup 是纯编排包，**不写任何算法代码**，只负责一键启动所有已有节点。

### 6.2 目录结构
```
sentry_bringup/
├── CMakeLists.txt                 # ament_cmake_auto, install config + launch
├── package.xml                    # 依赖: slam_toolbox, pointcloud_to_laserscan 等
├── config/
│   └── slam_toolbox_mapping.yaml  # pointcloud_to_laserscan + slam_toolbox 参数
└── launch/
    └── mapping_launch.py          # 建图专用启动文件
```

### 6.3 mapping_launch.py 启动的节点
| 节点 | 来源 | 说明 |
|------|------|------|
| `robot_state_publisher` | include sentry_description | 发布静态 TF |
| `mid360_driver` | Node, 用自带的 `params.yaml` | 雷达驱动 |
| `small_point_lio` | Node, 用自带的 `mid360.yaml` | 里程计 |
| `pointcloud_to_laserscan` | Node, 用 `slam_toolbox_mapping.yaml` | 3D 点云 → 2D 激光 |
| `async_slam_toolbox_node` | Node, 用 `slam_toolbox_mapping.yaml` | SLAM 建图 |
| `rviz2` | Node, 可用 `use_rviz:=False` 关闭 | 可视化 |

### 6.4 关键参数（slam_toolbox_mapping.yaml）
```yaml
pointcloud_to_laserscan:
  target_frame: base_link       # 在 base_link 坐标系下做高度裁剪
  min_height: 0.1               # 地面反射以下扔掉
  max_height: 0.5               # 天花板以上扔掉
  range_min: 0.38               # 盲区半径（和 mid360.yaml 一致）
  range_max: 20.0               # 最远 20m
  angle_increment: 0.0087       # ~0.5°/条，360°共 720 条线

slam_toolbox:
  mode: mapping                 # 建图模式
  odom_frame: odom              # 来自 small_point_lio
  map_frame: map                # slam_toolbox 发布
  base_frame: base_link
  resolution: 0.05              # 5cm/格
  do_loop_closing: true         # 开启回环检测
```

### 6.5 建图全流程
```bash
# 1. 编译
cd ~/my_sentry_nav
colcon build
source install/setup.bash

# 2. 启动建图（一键启动所有节点）
ros2 launch sentry_bringup mapping_launch.py

# 3. 手持雷达走一圈场地（慢走，拐弯处稍停让回环闭合）

# 4. 保存地图
ros2 run nav2_map_server map_saver_cli -f ~/my_map
# 输出：my_map.pgm（灰度栅格图）+ my_map.yaml（元信息）
```

### 6.6 数据流总览
```
mid360_driver ──→ /mid360_driver/lidar ──→ small_point_lio
                                               │
                                    /cloud_registered (PointCloud2)
                                               │
                                    pointcloud_to_laserscan
                                               │
                                         /scan (LaserScan)
                                               │
                                    async_slam_toolbox_node
                                               │
                                    map → odom TF + /map (OccupancyGrid)
```

### 6.7 完整 TF 树（建图阶段）
```
map ──(slam_toolbox发布)──→ odom ──(small_point_lio发布)──→ base_link
                                                                │
                                ┌───────────────────────────────┤
                                ↓                               ↓
                          lidar_link                       base_footprint
                          (URDF静态)                       (URDF静态)
```

---

## 第 7 步：实测建图（待实测）

- [ ] 连接雷达 Mini PC，启动建图
- [ ] 手持雷达走一圈场地
- [ ] RViz 观察 `/map` 栅格地图实时生成
- [ ] 回环检测是否触发（走到起点附近看地图修正）
- [ ] 保存地图 `my_map.pgm` + `my_map.yaml`

---

## 第 8 步：底盘通讯（待开发）

将 `cmd_vel`（nav2 输出的速度指令）转发给底层电机控制器。

---

## 第 9 步：nav2 导航（待开发）

```bash
# 需要创建的文件
sentry_bringup/config/nav2_params.yaml   # 导航参数
sentry_bringup/launch/nav_launch.py      # 导航启动文件
```

所需组件（nav2 自带）：
| 组件 | 包 | 作用 |
|------|-----|------|
| map_server | nav2_map_server | 加载已有地图 |
| amcl | nav2_amcl | 蒙特卡洛定位 |
| planner_server | nav2_planner | 全局路径规划（A* / Smac） |
| controller_server | nav2_controller | 局部轨迹跟踪（DWB） |
| bt_navigator | nav2_bt_navigator | 行为树调度 |
| behavior_server | nav2_behaviors | 恢复行为 |
| lifecycle_manager | nav2_lifecycle_manager | 生命周期管理 |