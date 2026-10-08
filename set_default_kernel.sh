#!/bin/bash
# 将 6.14.0-37 内核设为永久默认启动（重启直接进入，不显示菜单）
# 用法：sudo bash set_default_kernel.sh
# 说明：只改 GRUB_DEFAULT；保持 GRUB_TIMEOUT_STYLE=hidden、GRUB_TIMEOUT=0，
#       即重启后仍像现在一样不弹菜单、直接进系统。

set -u

GRUB=/etc/default/grub
NEW_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 6.14.0-37-generic"

echo "=== 1/3 备份 $GRUB ==="
cp -v "$GRUB" "${GRUB}.bak.$(date +%Y%m%d_%H%M%S)"

echo "=== 2/3 修改 GRUB_DEFAULT 为 6.14 ==="
if grep -qE '^GRUB_DEFAULT=' "$GRUB"; then
    sed -i "s|^GRUB_DEFAULT=.*|GRUB_DEFAULT=\"$NEW_DEFAULT\"|" "$GRUB"
else
    echo "GRUB_DEFAULT=\"$NEW_DEFAULT\"" >> "$GRUB"
fi

# 保持不显示菜单、直接进（比赛时开机即自启程序，不需要菜单）
sed -i 's|^GRUB_TIMEOUT_STYLE=.*|GRUB_TIMEOUT_STYLE=hidden|' "$GRUB"
sed -i 's|^GRUB_TIMEOUT=.*|GRUB_TIMEOUT=0|' "$GRUB"

echo "--- 改后的关键行 ---"
grep -E '^GRUB_DEFAULT=|^GRUB_TIMEOUT' "$GRUB"

echo "=== 3/3 重新生成 grub.cfg ==="
update-grub

echo
echo "=== 完成 ==="
echo "重启后验证：uname -r 应显示 6.14.0-37-generic"
