#!/bin/bash
# 编译和部署WebSocket配置修复后的APK

echo "🔧 开始编译WebSocket配置修复后的APK..."

# 清理之前的构建
echo "🧹 清理之前的构建..."
./gradlew clean

# 编译Debug版本
echo "🔨 编译Debug APK..."
./gradlew assembleDebug

# 检查编译结果
if [ $? -eq 0 ]; then
    echo "✅ APK编译成功！"
    
    # 检查设备连接
    if adb devices | grep -q "device"; then
        echo "📱 检测到设备，开始安装..."
        
        # 安装APK
        adb install -r app/build/outputs/apk/debug/app-debug.apk
        
        if [ $? -eq 0 ]; then
            echo "✅ APK安装成功！"
            echo ""
            echo "🚀 修复内容："
            echo "  ✅ SettingsRepository现在使用SharedPreferences持久化存储"
            echo "  ✅ WebSocket URL在应用重启后不会丢失"
            echo "  ✅ OTA自动化配置功能完全保留"
            echo ""
            echo "📱 请测试以下场景："
            echo "  1. 进行OTA配置，获取WebSocket URL"
            echo "  2. 重启应用，检查WebSocket连接是否正常"
            echo "  3. 观察logcat日志中的持久化相关信息"
            echo ""
            echo "🔍 监控日志命令："
            echo "  adb logcat | grep SettingsRepository"
        else
            echo "❌ APK安装失败"
        fi
    else
        echo "⚠️ 未检测到设备，APK已编译完成，位置："
        echo "    app/build/outputs/apk/debug/app-debug.apk"
    fi
else
    echo "❌ APK编译失败，请检查错误信息"
fi 