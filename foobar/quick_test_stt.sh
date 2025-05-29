#!/bin/bash
# 快速STT功能测试脚本

echo "🧪 快速STT功能测试"
echo "=================="

# 检查设备连接
echo "📱 检查设备连接..."
DEVICE_COUNT=$(adb devices | grep -c "device$" || echo "0")

if [ "$DEVICE_COUNT" -eq 0 ]; then
    echo "❌ 未检测到Android设备"
    echo "请确保设备已连接并启用USB调试"
    exit 1
fi

DEVICE_ID=$(adb devices | grep "device$" | head -1 | awk '{print $1}')
echo "✅ 检测到设备: $DEVICE_ID"

# 检查应用是否已安装
if adb shell pm list packages | grep -q "info.dourok.voicebot"; then
    echo "✅ VoiceBot应用已安装"
else
    echo "❌ VoiceBot应用未安装"
    echo "请先运行构建安装脚本"
    exit 1
fi

# 启动应用
echo "🚀 启动VoiceBot应用..."
adb shell am start -n info.dourok.voicebot/.MainActivity

# 等待启动
sleep 2

# 创建日志文件
LOG_FILE="stt_quick_test_$(date +%Y%m%d_%H%M%S).log"

echo "📊 监控STT关键日志 (15秒)..."
echo "请在应用中测试录音功能"

# 监控关键日志
{
    echo "=== STT快速测试日志 ==="
    echo "时间: $(date)"
    echo "设备: $DEVICE_ID"
    echo "======================="
    echo ""
    
    timeout 15s adb logcat -s WS:I WS:D WS:E | while read line; do
        echo "$line"
        
        # 检查关键成功指标并高亮显示
        if echo "$line" | grep -q "WebSocket connected"; then
            echo "🎉 [成功] WebSocket连接建立"
        elif echo "$line" | grep -q "WebSocket hello with enhanced auth"; then
            echo "🎉 [成功] 发送增强认证Hello消息"
        elif echo "$line" | grep -q "Hello握手响应"; then
            echo "🎉 [成功] Hello握手成功"
        elif echo "$line" | grep -q "Session ID:"; then
            echo "🎉 [成功] 获得Session ID - 认证成功！"
        elif echo "$line" | grep -q "收到STT识别结果"; then
            echo "🏆 [大成功] STT功能正常工作！"
        elif echo "$line" | grep -q "STT文本:"; then
            echo "🏆 [大成功] 收到语音识别结果！"
        fi
    done
} 2>&1 | tee "$LOG_FILE"

echo ""
echo "📄 测试日志已保存到: $LOG_FILE"
echo ""
echo "🎯 测试结果解读："
echo "  ✅ 如果看到 'Session ID' - 表示Hello握手成功"
echo "  ✅ 如果看到 'STT识别结果' - 表示STT功能正常"
echo "  ❌ 如果只有连接日志 - 可能需要在应用中手动测试录音"
echo ""
echo "🔧 继续监控命令:"
echo "  adb logcat -s WS:I | grep -E '(Hello|STT|Session)'" 