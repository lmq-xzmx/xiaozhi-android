#!/bin/bash
echo "🔧 构建和安装WebSocket连接时序修复版APK"
echo "============================================"

# 清理和构建
echo "1. 清理旧构建..."
./gradlew clean

echo "2. 构建修复版APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ APK构建成功!"
    
    # 卸载旧版本
    echo "3. 卸载旧版本..."
    adb uninstall info.dourok.voicebot
    
    # 安装新版本
    echo "4. 安装新版本..."
    adb install app/build/outputs/apk/debug/app-debug.apk
    
    if [ $? -eq 0 ]; then
        echo "✅ APK安装成功!"
        
        # 启动应用
        echo "5. 启动应用..."
        adb shell am start -n info.dourok.voicebot/.MainActivity
        
        echo "6. 监控WebSocket连接状态..."
        echo "请观察以下关键日志："
        echo "  ✅ 🚀 WebSocket协议启动开始"
        echo "  ✅ 🔗 开始建立WebSocket连接"
        echo "  ✅ ✅ WebSocket连接成功建立!"
        echo "  ✅ ✅ 音频通道已建立成功"
        echo ""
        echo "如果看到这些日志，说明时序问题已修复！"
        echo ""
        
        # 监控关键日志10秒
        timeout 10s adb logcat -s WS:I WS:E ChatViewModel:I | grep -E "(🚀|🔗|✅|❌|WebSocket|连接|启动|null)"
        
    else
        echo "❌ APK安装失败"
    fi
else
    echo "❌ APK构建失败"
fi 