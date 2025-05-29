#!/bin/bash

echo "🔍 WebSocket连接时序问题最终诊断"
echo "======================================="

# 1. 强制清理和重新安装
echo "1. 强制清理应用数据..."
adb shell pm clear info.dourok.voicebot

echo "2. 卸载并重新安装APK..."
adb uninstall info.dourok.voicebot
adb install app/build/outputs/apk/debug/app-debug.apk

# 2. 清空日志并启动
echo "3. 清空日志并启动应用..."
adb logcat -c
adb shell am start -n info.dourok.voicebot/.MainActivity

# 3. 等待应用启动
echo "4. 等待应用启动(3秒)..."
sleep 3

# 4. 检查关键日志
echo "5. 检查启动日志..."
echo "=== 查找修复后的启动日志 ==="

# 检查是否有我们的修复日志
START_LOG=$(adb logcat -d | grep "WebSocket协议启动开始")
CONNECT_LOG=$(adb logcat -d | grep "开始建立WebSocket连接")

if [[ -n "$START_LOG" ]]; then
    echo "✅ 找到启动日志: WebSocket协议启动开始"
    echo "$START_LOG"
else
    echo "❌ 未找到启动日志: WebSocket协议启动开始"
fi

if [[ -n "$CONNECT_LOG" ]]; then
    echo "✅ 找到连接日志: 开始建立WebSocket连接"
    echo "$CONNECT_LOG"
else
    echo "❌ 未找到连接日志: 开始建立WebSocket连接"
fi

# 5. 检查是否还有WebSocket null错误
echo ""
echo "=== 检查WebSocket null错误 ==="
NULL_ERRORS=$(adb logcat -d | grep "WebSocket is null" | wc -l)
echo "WebSocket is null 错误计数: $NULL_ERRORS"

if [[ $NULL_ERRORS -gt 0 ]]; then
    echo "❌ 仍然存在 WebSocket is null 错误!"
    echo "最近的错误:"
    adb logcat -d | grep "WebSocket is null" | tail -5
else
    echo "✅ 没有发现 WebSocket is null 错误"
fi

# 6. 显示完整的启动日志
echo ""
echo "=== 完整的应用启动日志 ==="
adb logcat -d | grep -E "(ChatViewModel|WS|WebSocket)" | head -20

echo ""
echo "=== 诊断完成 ===" 