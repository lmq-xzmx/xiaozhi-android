#!/bin/bash
# 语音助手应用调试脚本

ADB_PATH="$HOME/Library/Android/sdk/platform-tools/adb"

echo "🔧 语音助手应用调试工具"
echo "=========================="

# 检查设备连接
echo "📱 检查设备连接..."
$ADB_PATH devices

echo ""
echo "🧹 清空日志缓冲区..."
$ADB_PATH logcat -c

echo ""
echo "📦 安装最新应用..."
$ADB_PATH install -r app/build/outputs/apk/debug/app-debug.apk

echo ""
echo "🎤 手动授予录音权限..."
$ADB_PATH shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO

echo ""
echo "🔍 开始监控关键日志..."
echo "注意：请在另一个终端窗口或手动启动应用并测试语音功能"
echo "按 Ctrl+C 停止日志监控"
echo ""

# 监控关键组件的日志
$ADB_PATH logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder | while read line; do
    # 添加时间戳和颜色标记
    timestamp=$(date '+%H:%M:%S')
    
    # 根据关键词高亮显示
    if echo "$line" | grep -q "Starting audio"; then
        echo "[$timestamp] 🎤 $line"
    elif echo "$line" | grep -q "initialized successfully"; then
        echo "[$timestamp] ✅ $line"
    elif echo "$line" | grep -q "Audio frames"; then
        echo "[$timestamp] 📊 $line"
    elif echo "$line" | grep -q "Sending audio frame"; then
        echo "[$timestamp] 📤 $line"
    elif echo "$line" | grep -q "Received.*stt"; then
        echo "[$timestamp] 🗣️ $line"
    elif echo "$line" | grep -q "ERROR\|FATAL"; then
        echo "[$timestamp] ❌ $line"
    elif echo "$line" | grep -q "WARNING\|WARN"; then
        echo "[$timestamp] ⚠️ $line"
    else
        echo "[$timestamp] ℹ️ $line"
    fi
done 