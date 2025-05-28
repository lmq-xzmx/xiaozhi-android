#!/bin/bash
# WebSocket配置修复验证脚本

echo "🚀 开始验证WebSocket配置修复效果..."

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查ADB连接
echo "📱 检查设备连接..."
if ! adb devices | grep -q "device"; then
    echo -e "${RED}❌ 未检测到设备，请确保设备已连接并启用USB调试${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 设备已连接${NC}"

# 检查应用是否安装
echo "📦 检查应用安装状态..."
PACKAGE_NAME="info.dourok.voicebot"
if ! adb shell pm list packages | grep -q "$PACKAGE_NAME"; then
    echo -e "${RED}❌ 应用未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 应用已安装${NC}"

# 清除旧日志
echo "🧹 清除旧日志..."
adb logcat -c

# 启动应用并监控日志
echo "🚀 启动应用..."
adb shell am start -n "$PACKAGE_NAME/.MainActivity"

echo "📊 监控启动日志（15秒）..."
echo "寻找关键日志：'WebSocket URL已保存到持久化存储' 或 '使用持久化WebSocket URL'"

# 启动后台日志监控
timeout 15s adb logcat | grep -E "(SettingsRepository|WebSocket|持久化)" &
LOGCAT_PID=$!

sleep 15

# 停止日志监控
kill $LOGCAT_PID 2>/dev/null || true

echo ""
echo "🔄 测试应用重启后配置持久性..."

# 强制停止应用
echo "1️⃣ 强制停止应用..."
adb shell am force-stop "$PACKAGE_NAME"
sleep 2

# 重新启动应用
echo "2️⃣ 重新启动应用..."
adb shell am start -n "$PACKAGE_NAME/.MainActivity"

# 监控重启后的日志
echo "3️⃣ 监控重启日志（10秒）..."
echo "寻找：'使用持久化WebSocket URL' 日志"

timeout 10s adb logcat | grep -E "(SettingsRepository|WebSocket|持久化|配置)" | head -20

echo ""
echo "📋 验证步骤完成！"
echo ""
echo "💡 如何判断修复是否成功："
echo "  ✅ 看到 '✅ WebSocket URL已保存到持久化存储' - 配置保存成功"
echo "  ✅ 重启后看到 '使用持久化WebSocket URL' - 配置持久化成功"
echo "  ❌ 看到 'WebSocket URL未配置' - 修复可能失败"
echo ""
echo "📱 如需手动验证，可执行："
echo "  adb logcat | grep SettingsRepository" 