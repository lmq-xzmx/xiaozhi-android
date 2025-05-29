#!/bin/bash

echo "🔧 WebSocket连接时序问题终极修复"
echo "================================"

echo "1. 清理构建..."
./gradlew clean

echo "2. 构建修复版APK..."
./gradlew assembleDebug

echo "3. 强制卸载旧版本..."
adb shell pm clear info.dourok.voicebot
adb uninstall info.dourok.voicebot

echo "4. 安装修复版..."
adb install app/build/outputs/apk/debug/app-debug.apk

echo "5. 清空日志并启动..."
adb logcat -c
adb shell am start -n info.dourok.voicebot/.MainActivity

echo "6. 监控关键日志..."
echo "正在监控关键日志，请观察以下修复效果:"
echo "✅ 应该看到: 🚀 WebSocket协议启动开始"
echo "✅ 应该看到: 🔧 创建服务器兼容的认证Hello消息"
echo "✅ 应该看到: ✅ Hello握手成功完成"
echo "❌ 不应该看到: WebSocket is null"

# 监控10秒
timeout 10s adb logcat | grep -E "(🚀|🔧|✅|❌|WebSocket|null|认证|Hello|握手)" 