#!/bin/bash

echo "🎯 最终STT验证测试 - 参数匹配修复"
echo "==========================================="

# 检查设备连接
ADB_PATH=$(which adb)
DEVICE_ID=$($ADB_PATH devices | grep device | head -1 | cut -f1)

if [ -z "$DEVICE_ID" ]; then
    echo "❌ 未找到Android设备"
    exit 1
fi

echo "📱 设备: $DEVICE_ID"
echo "🔧 验证修复: version=1, frame_duration=60ms"
echo "==========================================="

# 清理日志缓存
$ADB_PATH -s $DEVICE_ID logcat -c

# 重启应用以应用修复
echo "🚀 重启应用应用参数修复..."
$ADB_PATH -s $DEVICE_ID shell am force-stop info.dourok.voicebot
sleep 2
$ADB_PATH -s $DEVICE_ID shell am start -n info.dourok.voicebot/.MainActivity

echo "📊 监控关键修复验证点："
echo "✅ 期望Hello消息: \"version\":1, \"frame_duration\":60"  
echo "✅ 期望服务器匹配响应: version:1, frame_duration:60"
echo "✅ 期望STT响应: {\"type\":\"stt\",\"text\":\"...\"}"
echo "==========================================="

# 监控关键日志点
$ADB_PATH -s $DEVICE_ID logcat | while read line; do
    timestamp=$(date '+%H:%M:%S')
    
    # 检查修复后的Hello消息
    if echo "$line" | grep -q "WS.*Sending hello message"; then
        hello_json=$(echo "$line" | sed 's/.*Sending hello message: //')
        echo "[$timestamp] 🔧 Hello消息发送:"
        echo "       $hello_json"
        
        # 验证关键参数
        if echo "$hello_json" | grep -q '"version":1'; then
            echo "       ✅ 版本参数正确: version=1"
        else
            echo "       ❌ 版本参数错误!"
        fi
        
        if echo "$hello_json" | grep -q '"frame_duration":60'; then
            echo "       ✅ 帧长度参数正确: frame_duration=60"
        else
            echo "       ❌ 帧长度参数错误!"
        fi
        echo ""
    fi
    
    # 检查服务器响应匹配
    if echo "$line" | grep -q "WS.*原始消息.*hello"; then
        server_response=$(echo "$line" | sed 's/.*原始消息: //')
        echo "[$timestamp] 📨 服务器Hello响应:"
        echo "       $server_response"
        
        if echo "$server_response" | grep -q '"version":1'; then
            echo "       ✅ 服务器版本匹配: version=1"
        fi
        
        if echo "$server_response" | grep -q '"frame_duration":60'; then
            echo "       ✅ 服务器帧长度匹配: frame_duration=60"
        fi
        echo ""
    fi
    
    # 检查STT响应（最关键）
    if echo "$line" | grep -q "WS.*🎉.*收到STT响应"; then
        echo "[$timestamp] 🎉 *** STT功能恢复成功! ***"
        stt_content=$(echo "$line" | sed 's/.*STT内容: //')
        echo "       STT响应: $stt_content"
        echo ""
    fi
    
    # 检查用户语音显示
    if echo "$line" | grep -q "ChatViewModel: >>"; then
        user_speech=$(echo "$line" | sed 's/.*ChatViewModel: >> //')
        echo "[$timestamp] 🗣️  用户语音识别: \"$user_speech\""
        echo ""
    fi
    
    # 检查错误
    if echo "$line" | grep -q "WS.*❌.*服务器返回错误"; then
        echo "[$timestamp] ❌ 服务器错误:"
        echo "       $line"
        echo ""
    fi
    
    # 检查连接状态
    if echo "$line" | grep -q "WS.*WebSocket connected successfully"; then
        echo "[$timestamp] ✅ WebSocket连接成功"
        echo ""
    fi
    
    if echo "$line" | grep -q "WS.*WebSocket closed"; then
        echo "[$timestamp] 🔌 连接关闭"
        echo ""
    fi
done 