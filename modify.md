# 修复 minipc 死机重启：禁用海康 MVS 相机驱动 gevfilter

> 日期：2026-09-22
> 作者：maple0738
> 状态：待执行（sudo 需要密码，需手动运行 `sudo bash modify.sh`）

---

## 1. 问题现象

开启 rog_map（mapping_3d_launch）后，运行一段时间 minipc 就会死机并自动重启。
2.5 小时内重启了约 10 次（`journalctl --list-boots` 可见）。

## 2. 根因诊断（结论）

**不是 rog_map 的问题，是海康 MVS 相机驱动的内核模块 `gevfilter.ko` 在开机时崩溃。**

证据链：

1. **rog_map 源码与学长 `mas_nav` 逐字节一致**。`diff -rq` 对比两边
   `sentry_hardware/rog_map` 与 `mas2027_perception/rog_map`，所有 `.cpp/.hpp` 完全相同，
   只有 `CMakeLists.txt`（多一句 `install(DIRECTORY config ...)`）和新增的
   `config/rog_map_params.yaml` 不同；且关键参数（map_size、分辨率、raycasting、
   projection、field、dirty-column）与学长 `planner_params.yaml` 的 `rog_map` 段一致。

2. **每一轮开机内核都在崩**。`journalctl -k` 每轮 boot 都有：

   ```
   BUG: unable to handle page fault for address: ffff....3028
   RIP: 0010: InitModuleDevice+0x35/0x100 [gevfilter]
   Call Trace: MV_InitModule [gevfilter] -> do_init_module -> load_module
   ```

   以及 boot -6 出现 `modprobe` 软锁死：

   ```
   watchdog: BUG: soft lockup - CPU#4 stuck for 231s! [modprobe]
   ```

3. **罪魁祸首**：海康 MVS SDK 的 GigE 相机过滤驱动
   `/opt/MVS/driver/gige/gevfilter.ko`，版本 `4.4.0.1 build 20240422`。
   当前内核为 `7.0.0-31-generic`（Ubuntu 24.04 HWE），这个 2024 年的旧版驱动
   源码不兼容 7.0 内核，即使开机脚本用 build.sh 重新编译出 vermagic 匹配的 .ko，
   加载时仍会缺页崩溃。

4. **加载来源**：海康 SDK 自带的 4 个 `/etc/init.d/` 自启脚本，开机自动 insmod：

   | 脚本 | 作用 |
   |------|------|
   | `MvLogServer` | 启动海康日志服务，顺带加载 gevfilter |
   | `DriverServer` | 加载 GigE 相机驱动 `gevfilter.ko`（每次开机重编译） |
   | `FGDriverServer` | 加载 PCIe 采集卡驱动 `driver/pcie/*.ko` |
   | `ScriptServer` | 设置 usbfs/socket/rp_filter 等系统参数 |

> 说明：这些脚本是**海康 SDK 下载安装时自带的**，与我们自己写的视觉程序自启动无关。

## 3. 本次执行的修改

见同目录 `modify.sh`，共四步：

1. 卸载当前已加载的 `gevfilter` 模块；
2. 把 `/opt/MVS/driver/gige/gevfilter.ko` 改名为 `.bak`（自启脚本检测到文件不存在就不会加载）；
3. 用 `update-rc.d ... remove` 移除 4 个 MVS 自启脚本；
4. 重启验证。

手动执行（等价于脚本）：

```bash
sudo rmmod gevfilter
sudo mv /opt/MVS/driver/gige/gevfilter.ko /opt/MVS/driver/gige/gevfilter.ko.bak
sudo update-rc.d DriverServer remove
sudo update-rc.d FGDriverServer remove
sudo update-rc.d ScriptServer remove
sudo update-rc.d MvLogServer remove
```

## 4. 验证方法（重启后）

```bash
# 1. 驱动应已不在
lsmod | grep gevfilter          # 应无输出

# 2. 内核日志应不再有 gevfilter 缺页崩溃
journalctl -k | grep -iE "gevfilter|page fault|soft lockup"
```

确认干净后，再单独跑 `ros2 launch sentry_bringup mapping_3d_launch.py`，观察是否还死机。

## 5. 以后要重新用相机（比赛时）

1. 去海康官网下载**适配 7.0 内核的新版 MVS SDK**（当前 4.4.0.1 build 20240422 不兼容），
   下载前先看 ReleaseNote 是否支持 Ubuntu 24.04 / 内核 7.0.x。
2. 装好后验证：

   ```bash
   modinfo /opt/MVS/driver/gige/gevfilter.ko | grep vermagic   # 确认 7.0.0-31
   sudo modprobe gevfilter
   sudo dmesg | tail -20                                        # 无 page fault 才算成
   ```

3. 在**我们自己的视觉程序自启动脚本**里显式写清顺序：
   先 `sudo insmod /opt/MVS/driver/gige/gevfilter.ko`（或新版提供的加载方式），
   再启动视觉程序，不要依赖海康的 init.d 脚本。

4. 恢复被改名的旧驱动（如仍要用旧版，一般不推荐）：

   ```bash
   sudo mv /opt/MVS/driver/gige/gevfilter.ko.bak /opt/MVS/driver/gige/gevfilter.ko
   ```

## 6. 相关文件

- 相机驱动：`/opt/MVS/driver/gige/gevfilter.ko`（已改名 `.bak`）
- 自启脚本：`/etc/init.d/{MvLogServer,DriverServer,FGDriverServer,ScriptServer}`
- 本次操作记录：本文件 `modify.md` + `modify.sh`
- rog_map 独立节点：`sentry_hardware/rog_map/src/rog_map_node/rog_map_node.cpp`
- 建图 launch：`sentry_bringup/launch/mapping_3d_launch.py`
