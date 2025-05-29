#!/bin/bash

echo "🔧 WebSocket连接时序问题修复测试"
echo "==============================="

# 检查设备
echo "1. 检查连接的设备..."
adb devices -l

# 获取第一个设备
DEVICE=$(adb devices | grep -E "device$|emulator" | head -1 | awk '{print $1}')

if [ -z "$DEVICE" ]; then
    echo "❌ 没有找到连接的设备"
    exit 1
fi

echo "📱 选择设备: $DEVICE"

# 卸载旧版本
echo "2. 卸载旧版本..."
adb -s "$DEVICE" shell pm clear info.dourok.voicebot
adb -s "$DEVICE" uninstall info.dourok.voicebot

# 安装新版本
echo "3. 安装修复版APK..."
adb -s "$DEVICE" install app/build/outputs/apk/debug/app-debug.apk

if [ $? -ne 0 ]; then
    echo "❌ APK安装失败"
    exit 1
fi

# 清空日志并启动
echo "4. 清空日志并启动应用..."
adb -s "$DEVICE" logcat -c
adb -s "$DEVICE" shell am start -n info.dourok.voicebot/.MainActivity

# 等待应用启动
echo "5. 等待应用启动(3秒)..."
sleep 3

# 检查修复效果
echo "6. 检查修复效果..."
echo "================================="

# 查找关键日志
echo "查找启动日志..."
START_LOGS=$(adb -s "$DEVICE" logcat -d | grep "WebSocket协议启动开始")
if [ -n "$START_LOGS" ]; then
    echo "✅ 找到启动日志:"
    echo "$START_LOGS"
else
    echo "❌ 未找到启动日志"
fi

echo ""
echo "查找认证日志..."
AUTH_LOGS=$(adb -s "$DEVICE" logcat -d | grep "创建服务器兼容的认证Hello消息")
if [ -n "$AUTH_LOGS" ]; then
    echo "✅ 找到认证日志:"
    echo "$AUTH_LOGS"
else
    echo "❌ 未找到认证日志"
fi

echo ""
echo "查找握手成功日志..."
HANDSHAKE_LOGS=$(adb -s "$DEVICE" logcat -d | grep "Hello握手成功完成")
if [ -n "$HANDSHAKE_LOGS" ]; then
    echo "✅ 找到握手成功日志:"
    echo "$HANDSHAKE_LOGS"
else
    echo "❌ 未找到握手成功日志"
fi

echo ""
echo "检查WebSocket null错误..."
NULL_ERRORS=$(adb -s "$DEVICE" logcat -d | grep "WebSocket is null" | wc -l)
echo "WebSocket is null 错误计数: $NULL_ERRORS"

if [ "$NULL_ERRORS" -gt 0 ]; then
    echo "❌ 仍然存在WebSocket null错误!"
    echo "最近的错误:"
    adb -s "$DEVICE" logcat -d | grep "WebSocket is null" | tail -3
else
    echo "✅ 没有发现WebSocket null错误"
fi

echo ""
echo "=== 完整的WebSocket相关日志 ==="
adb -s "$DEVICE" logcat -d | grep -E "(WS:|WebSocket|Hello|握手|认证)" | tail -20 