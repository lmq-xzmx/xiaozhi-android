#!/bin/bash

echo "🚀 执行STT修复的下一步操作..."

# 步骤1: 编译APK
echo "📦 步骤1: 编译Debug APK..."
cd /Users/xzmx/Downloads/my-project/xiaozhi-android
./gradlew app:assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ APK编译成功！"
else
    echo "❌ APK编译失败，请检查错误"
    exit 1
fi

# 步骤2: 检查连接的Android设备
echo "📱 步骤2: 检查连接的Android设备..."
adb devices -l

# 步骤3: 显示APK路径
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    echo "✅ APK已生成: $APK_PATH"
    ls -la "$APK_PATH"
else
    echo "❌ APK文件未找到"
    exit 1
fi

# 步骤4: 提示下一步操作
echo ""
echo "🎯 下一步手动操作指南："
echo "1. 清除应用数据（重要！）："
echo "   - 方法A: 手机设置 → 应用管理 → VoiceBot → 存储 → 清除数据"
echo "   - 方法B: 如果设备连接，运行: adb shell pm clear info.dourok.voicebot"
echo ""
echo "2. 安装更新的APK："
echo "   adb install -r app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "3. 测试STT功能："
echo "   - 启动应用"
echo "   - 点击录音按钮"
echo "   - 说话测试"
echo "   - 期望：显示转录文字！"

echo ""
echo "🔍 验证设备绑定状态..."
cd foobar
python3 test_your_device_id.py 