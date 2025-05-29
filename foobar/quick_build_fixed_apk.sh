#!/bin/bash
# 快速构建修复版本APK脚本

echo "🔧 快速构建WebSocket连接修复版APK"
echo "================================="

# 进入项目目录
cd "$(dirname "$0")/.."

echo "1. 清理旧构建..."
./gradlew clean --quiet

echo "2. 编译修复版APK..."
./gradlew assembleDebug

if [ -f "app/build/outputs/apk/debug/app-debug.apk" ]; then
    echo "✅ APK构建成功!"
    echo "📍 APK路径: app/build/outputs/apk/debug/app-debug.apk"
    
    # 检查设备连接
    DEVICE_COUNT=$(adb devices | grep -c "device$" || echo "0")
    if [ "$DEVICE_COUNT" -gt 0 ]; then
        echo "📱 检测到Android设备，准备安装..."
        adb install -r app/build/outputs/apk/debug/app-debug.apk
        echo "✅ APK安装完成!"
        
        echo "🚀 启动应用..."
        adb shell am start -n info.dourok.voicebot/.MainActivity
        
        echo "📊 监控WebSocket连接日志 (15秒)..."
        echo "请注意观察以下关键日志:"
        echo "  🚀 WebSocket协议启动开始"
        echo "  🔗 开始建立WebSocket连接"
        echo "  ✅ WebSocket连接成功建立!"
        echo "  ✅ 音频通道已建立成功"
        echo ""
        
        timeout 15s adb logcat -s WS:I WS:E ChatViewModel:I | grep -E "(🚀|🔗|✅|❌|WebSocket|连接|启动)" || true
        
    else
        echo "⚠️ 未检测到Android设备"
        echo "请手动安装APK: app/build/outputs/apk/debug/app-debug.apk"
    fi
else
    echo "❌ APK构建失败"
    exit 1
fi 