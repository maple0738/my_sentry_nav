#!/bin/bash
# 禁用海康 MVS 相机驱动 gevfilter，修复 minipc 死机重启
# 用法：sudo bash modify.sh
# 详见同目录 modify.md

set -u

echo "=== 1/4 卸载 gevfilter 驱动 ==="
if lsmod | grep -q gevfilter; then
    rmmod gevfilter && echo "  已卸载 gevfilter" || echo "  卸载失败（可能有进程占用）"
else
    echo "  gevfilter 未加载，跳过"
fi

echo "=== 2/4 改名 gevfilter.ko，阻止开机加载 ==="
KO=/opt/MVS/driver/gige/gevfilter.ko
if [ -f "$KO" ]; then
    mv "$KO" "$KO.bak" && echo "  已改名 -> gevfilter.ko.bak" || echo "  改名失败"
else
    echo "  $KO 不存在，跳过"
fi

echo "=== 3/4 移除 MVS 开机自启脚本 ==="
for s in DriverServer FGDriverServer ScriptServer MvLogServer; do
    if [ -f "/etc/init.d/$s" ]; then
        if update-rc.d "$s" remove >/dev/null 2>&1; then
            echo "  已移除 $s 自启"
        else
            echo "  $s 移除失败（update-rc.d 报错，可尝试 systemctl disable $s）"
        fi
    else
        echo "  $s 不存在，跳过"
    fi
done

echo "=== 4/4 完成 ==="
echo "请重启后验证："
echo "  lsmod | grep gevfilter          # 应无输出"
echo "  journalctl -k | grep -i gevfilter  # 应无 page fault"
