#!/bin/bash

# WebSocket迁移测试脚本
echo "🔧 开始测试MQTT到WebSocket迁移..."

# 检查设备连接
ADB_PATH=$(which adb)
if [ -z "$ADB_PATH" ]; then
    echo "❌ 错误：未找到adb命令，请确保Android SDK已安装"
    exit 1
fi

DEVICE_ID=$($ADB_PATH devices | grep device | head -1 | cut -f1)
if [ -z "$DEVICE_ID" ]; then
    echo "❌ 错误：未找到连接的Android设备"
    exit 1
fi

echo "📱 使用设备：$DEVICE_ID"

# 清理日志缓存
echo "🧹 清理旧日志..."
$ADB_PATH -s $DEVICE_ID logcat -c

echo "🚀 启动应用并监控关键日志..."
echo "======================================"
echo "监控说明："
echo "✅ 看到 'TransportType.*WebSockets' 表示配置正确"
echo "✅ 看到 'WebSocket connected successfully' 表示连接成功"  
echo "✅ 看到 'OpusEncoder created successfully' 表示音频编码正常"
echo "✅ 看到 'Audio frames sent' 表示音频发送正常"
echo "✅ 看到 'Received.*stt' 表示STT识别成功"
echo "❌ 看到 'MQTT配置未初始化' 表示配置错误"
echo "❌ 看到 'Failed to open audio channel' 表示连接失败"
echo "======================================"

# 启动应用
$ADB_PATH -s $DEVICE_ID shell am start -n info.dourok.voicebot/.MainActivity

echo "📊 开始监控应用日志 (按Ctrl+C停止)..."

# 监控关键日志
$ADB_PATH -s $DEVICE_ID logcat | grep -E "(ChatViewModel|SettingsRepository|WebsocketProtocol|AudioRecorder|OpusEncoder|transportType|MQTT配置|WebSocket.*connect|STT|stt)" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    
    # 根据关键词标记日志类型
    if echo "$line" | grep -qi "websockets\|websocket.*connect"; then
        echo "[$timestamp] 🌐 $line"
    elif echo "$line" | grep -qi "transporttype"; then
        echo "[$timestamp] ⚙️ $line"  
    elif echo "$line" | grep -qi "mqtt配置未初始化\|mqtt.*null"; then
        echo "[$timestamp] ❌ $line"
    elif echo "$line" | grep -qi "opus.*created\|audio.*created"; then
        echo "[$timestamp] 🎤 $line"
    elif echo "$line" | grep -qi "audio frames sent\|sending audio"; then
        echo "[$timestamp] 📤 $line"
    elif echo "$line" | grep -qi "stt\|received.*text"; then
        echo "[$timestamp] 🗣️ $line"
    elif echo "$line" | grep -qi "error\|exception\|failed"; then
        echo "[$timestamp] ⚠️ $line"
    else
        echo "[$timestamp] ℹ️ $line"
    fi
done 