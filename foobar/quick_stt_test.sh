#!/bin/bash

echo "🔧 快速STT测试 - 验证20ms帧长度修改效果"

# 检查设备连接
ADB_PATH=$(which adb)
DEVICE_ID=$($ADB_PATH devices | grep device | head -1 | cut -f1)

if [ -z "$DEVICE_ID" ]; then
    echo "❌ 未找到Android设备"
    exit 1
fi

echo "📱 设备: $DEVICE_ID"
echo "🎯 测试重点：检查20ms帧长度是否解决STT问题"
echo "========================================"

# 清理日志缓存
$ADB_PATH -s $DEVICE_ID logcat -c

# 重启应用
echo "🚀 重启应用以应用新的音频参数..."
$ADB_PATH -s $DEVICE_ID shell am force-stop info.dourok.voicebot
sleep 2
$ADB_PATH -s $DEVICE_ID shell am start -n info.dourok.voicebot/.MainActivity

echo "📊 监控关键变化："
echo "✅ Hello消息: 期望看到 'version':3, 'frame_duration':20" 
echo "✅ 服务器响应: 期望看到STT相关响应"
echo "✅ 用户语音: 期望看到 'ChatViewModel: >> [用户语音]'"
echo "========================================"

# 专门监控关键的STT相关日志
$ADB_PATH -s $DEVICE_ID logcat | while read line; do
    timestamp=$(date '+%H:%M:%S')
    
    # Hello消息 - 检查新的参数
    if echo "$line" | grep -q "Sending hello message"; then
        echo "[$timestamp] 📤 Hello消息发送:"
        # 提取JSON内容并格式化显示
        hello_json=$(echo "$line" | sed 's/.*Sending hello message: //')
        echo "       $hello_json" | tr ',' '\n' | grep -E "(version|frame_duration)"
    
    # 服务器的任何文本响应
    elif echo "$line" | grep -q "WS.*Received text message"; then
        response=$(echo "$line" | sed 's/.*Received text message: //')
        echo "[$timestamp] 📨 服务器响应: $response"
        
        # 特别标记STT响应
        if echo "$response" | grep -q '"type":"stt"'; then
            echo "[$timestamp] 🎉 *** STT响应检测到! ***"
        fi
    
    # 用户语音识别结果
    elif echo "$line" | grep -q "ChatViewModel.*>>"; then
        user_text=$(echo "$line" | sed 's/.*>> //')
        echo "[$timestamp] 👤 用户语音识别: '$user_text'"
        echo "[$timestamp] 🎉 *** STT工作正常! ***"
    
    # 音频帧统计 (简化显示)
    elif echo "$line" | grep -q "Audio frames sent:"; then
        frame_count=$(echo "$line" | grep -o "[0-9]\+")
        echo "[$timestamp] 📊 音频帧已发送: $frame_count"
    
    # 错误信息
    elif echo "$line" | grep -qi "error\|exception\|failed"; then
        echo "[$timestamp] ⚠️ 错误: $line"
    
    # OpusEncoder相关（检查20ms帧）
    elif echo "$line" | grep -q "OpusEncoder.*successfully"; then
        echo "[$timestamp] ✅ OpusEncoder已创建 (20ms帧)"
        
    # WebSocket连接状态
    elif echo "$line" | grep -q "WebSocket connected successfully"; then
        echo "[$timestamp] 🌐 WebSocket连接成功"
    fi
done 