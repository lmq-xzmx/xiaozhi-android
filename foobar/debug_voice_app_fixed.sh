#!/bin/bash
# 语音助手应用调试脚本 - 多设备支持版本

ADB_PATH="$HOME/Library/Android/sdk/platform-tools/adb"

echo "🔧 语音助手应用调试工具 (多设备版)"
echo "================================="

# 检查设备连接
echo "📱 检查设备连接..."
$ADB_PATH devices

echo ""
echo "🎯 可用设备："
echo "1. SOZ95PIFVS5H6PIZ (真实设备)"
echo "2. emulator-5554 (模拟器)"
echo ""

# 让用户选择设备
read -p "请选择设备 (1=真实设备, 2=模拟器): " choice

case $choice in
    1)
        DEVICE_ID="SOZ95PIFVS5H6PIZ"
        echo "✅ 选择了真实设备: $DEVICE_ID"
        ;;
    2)
        DEVICE_ID="emulator-5554"
        echo "✅ 选择了模拟器: $DEVICE_ID"
        ;;
    *)
        echo "❌ 无效选择，默认使用真实设备"
        DEVICE_ID="SOZ95PIFVS5H6PIZ"
        ;;
esac

echo ""
echo "🧹 清空日志缓冲区..."
$ADB_PATH -s $DEVICE_ID logcat -c

echo ""
echo "📦 安装最新应用..."
$ADB_PATH -s $DEVICE_ID install -r app/build/outputs/apk/debug/app-debug.apk

echo ""
echo "🎤 手动授予录音权限..."
$ADB_PATH -s $DEVICE_ID shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO

echo ""
echo "🔍 开始监控关键日志 (设备: $DEVICE_ID)..."
echo "注意：请在选定设备上启动应用并测试语音功能"
echo "按 Ctrl+C 停止日志监控"
echo ""

# 监控关键组件的日志
$ADB_PATH -s $DEVICE_ID logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder | while read line; do
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