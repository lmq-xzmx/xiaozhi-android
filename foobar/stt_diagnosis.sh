#!/bin/bash

echo "🔍 STT问题专项诊断 - 检查语音识别响应"

# 检查设备连接
ADB_PATH=$(which adb)
DEVICE_ID=$($ADB_PATH devices | grep device | head -1 | cut -f1)

if [ -z "$DEVICE_ID" ]; then
    echo "❌ 未找到Android设备"
    exit 1
fi

echo "📱 设备ID: $DEVICE_ID"
echo "🔍 开始监控STT相关日志..."
echo "=================================="

# 清理日志
$ADB_PATH -s $DEVICE_ID logcat -c

# 重启应用
echo "🚀 重启应用进行新的测试..."
$ADB_PATH -s $DEVICE_ID shell am force-stop info.dourok.voicebot
sleep 2
$ADB_PATH -s $DEVICE_ID shell am start -n info.dourok.voicebot/.MainActivity

echo "📊 监控以下关键指标："
echo "1. 服务器所有响应消息"
echo "2. STT相关的任何响应"
echo "3. 音频质量和传输状态"
echo "4. 错误和异常信息"
echo "=================================="

# 监控所有可能的服务器响应
$ADB_PATH -s $DEVICE_ID logcat | while read line; do
    timestamp=$(date '+%H:%M:%S')
    
    # WebSocket收到的所有消息
    if echo "$line" | grep -q "WS.*Received text message"; then
        echo "[$timestamp] 📨 服务器响应: $(echo "$line" | sed 's/.*Received text message: //')"
    
    # STT相关的任何消息
    elif echo "$line" | grep -qi "stt\|speech\|recogni\|transcript"; then
        echo "[$timestamp] 🗣️ STT相关: $line"
    
    # ChatViewModel中用户消息显示
    elif echo "$line" | grep -q "ChatViewModel.*>>"; then
        echo "[$timestamp] 👤 用户语音: $line"
    
    # ChatViewModel中助手消息显示  
    elif echo "$line" | grep -q "ChatViewModel.*<<"; then
        echo "[$timestamp] 🤖 助手回复: $line"
    
    # 音频帧统计（每50帧显示一次）
    elif echo "$line" | grep -q "Audio frames sent:"; then
        echo "[$timestamp] 📊 音频统计: $line"
    
    # WebSocket连接状态
    elif echo "$line" | grep -q "WS.*connect\|WS.*disconnect\|WS.*closed"; then
        echo "[$timestamp] 🌐 连接状态: $line"
    
    # 任何错误或异常
    elif echo "$line" | grep -qi "error\|exception\|failed\|timeout"; then
        echo "[$timestamp] ⚠️ 错误信息: $line"
    
    # 监听状态变化
    elif echo "$line" | grep -q "Device state\|DeviceState\|LISTENING\|SPEAKING"; then
        echo "[$timestamp] 🔄 状态变化: $line"
        
    # WebSocket发送的控制消息
    elif echo "$line" | grep -q "WS.*Sending text.*listen\|WS.*Sending text.*stop"; then
        echo "[$timestamp] 📤 控制消息: $line"
    fi
done 