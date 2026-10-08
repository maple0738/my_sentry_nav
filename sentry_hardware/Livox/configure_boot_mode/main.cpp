#include "livox_lidar_def.h"
#include "livox_lidar_api.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <chrono>
#include <iostream>
#include <atomic>
#include <csignal>

#ifdef _WIN32
#include <winsock2.h>
#else
#include <arpa/inet.h>
#endif

std::atomic<bool> g_configured(false);
std::atomic<bool> g_lidar_found(false);

void WorkModeAfterBootCallback(livox_status status, uint32_t handle,
    LivoxLidarAsyncControlResponse *response, void *client_data) {
  if (response == nullptr) return;
  if (status == kLivoxLidarStatusSuccess && response->ret_code == 0) {
    std::cout << "\n✅ 上电后模式已设为 Normal（已写入雷达 Flash，永久生效）" << std::endl;
    g_configured = true;
  } else {
    std::cout << "\n❌ 设置失败，status: " << status
              << ", ret_code: " << response->ret_code
              << ", error_key: " << response->error_key << std::endl;
  }
}

void WorkModeCallback(livox_status status, uint32_t handle,
    LivoxLidarAsyncControlResponse *response, void *client_data) {
  if (response == nullptr) return;
  if (status == kLivoxLidarStatusSuccess && response->ret_code == 0) {
    std::cout << "✅ 当前模式已设为 Normal（雷达已启动，可接收数据）" << std::endl;
  } else {
    std::cout << "⚠️  启动当前模式返回 status: " << status
              << ", ret_code: " << response->ret_code << std::endl;
  }
}

void LidarInfoChangeCallback(const uint32_t handle, const LivoxLidarInfo* info, void* client_data) {
  if (info == nullptr) return;

  struct in_addr addr;
  addr.s_addr = handle;
  std::cout << "\n📍 发现雷达! IP: " << inet_ntoa(addr) << ", SN: " << info->sn << std::endl;
  g_lidar_found = true;

  // 1. 设置"上电后模式"为 Normal（写入 Flash，永久生效）
  std::cout << "⏳ 正在设置上电后模式为 Normal（写入 Flash）..." << std::endl;
  SetLivoxLidarWorkModeAfterBoot(handle, kLivoxLidarWorkModeAfterBootNormal,
      WorkModeAfterBootCallback, nullptr);

  // 2. 同时设置当前模式为 Normal（立即启动雷达）
  std::cout << "⏳ 正在启动雷达（当前模式 Normal）..." << std::endl;
  SetLivoxLidarWorkMode(handle, kLivoxLidarNormal, WorkModeCallback, nullptr);
}

int main(int argc, const char *argv[]) {
  std::cout << "============================================" << std::endl;
  std::cout << "  Mid-360s 启动模式配置工具 v1.0" << std::endl;
  std::cout << "  作用：将雷达上电后模式改为 Normal（永久生效）" << std::endl;
  std::cout << "  使用：仅需运行一次，之后雷达上电自动发数据" << std::endl;
  std::cout << "============================================" << std::endl;

  // 获取 config 路径
  std::string config_path;
  if (argc >= 2) {
    config_path = argv[1];
  } else {
    config_path = "./config.json";
  }
  std::cout << "  配置文件: " << config_path << "\n" << std::endl;

  // 初始化 SDK
  if (!LivoxLidarSdkInit(config_path.c_str())) {
    std::cerr << "❌ Livox SDK 初始化失败！" << std::endl;
    std::cerr << "  请检查：" << std::endl;
    std::cerr << "    1. config.json 中的 host_ip 是否为本机 IP" << std::endl;
    std::cerr << "    2. 雷达是否已经上电并连接到网络" << std::endl;
    std::cerr << "    3. liblivox_lidar_sdk_shared.so 是否已安装到系统" << std::endl;
    LivoxLidarSdkUninit();
    return -1;
  }

  // 注册雷达发现回调
  SetLivoxLidarInfoChangeCallback(LidarInfoChangeCallback, nullptr);

  std::cout << "⏳ 等待发现雷达（最多 10 秒）..." << std::endl;

  // 等待配置完成或超时（10 秒）
  int wait_count = 0;
  while (!g_configured && wait_count < 100) {
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    wait_count++;
  }

  LivoxLidarSdkUninit();

  if (g_configured) {
    std::cout << "\n============================================" << std::endl;
    std::cout << "  ✅ 全部配置完成！" << std::endl;
    std::cout << "============================================" << std::endl;
    std::cout << "  现在你可以：" << std::endl;
    std::cout << "  1. 断电重启雷达，之后它会自动发数据" << std::endl;
    std::cout << "  2. 或直接启动你的 mid360_driver 接收数据" << std::endl;
    std::cout << "  3. 此工具只需运行一次，以后无需再运行" << std::endl;
    return 0;
  } else if (g_lidar_found) {
    std::cout << "\n⚠️  已发现雷达但配置未确认完成。" << std::endl;
    std::cout << "  请检查网络连接后重试。" << std::endl;
    return 1;
  } else {
    std::cout << "\n❌ 未发现雷达，请检查：" << std::endl;
    std::cout << "  1. 雷达是否上电" << std::endl;
    std::cout << "  2. 网线是否连接，网口指示灯是否亮" << std::endl;
    std::cout << "  3. 本机 IP 是否设为 192.168.1.x" << std::endl;
    std::cout << "  4. config.json 中的 host_ip 是否等于本机 IP" << std::endl;
    return 1;
  }
}