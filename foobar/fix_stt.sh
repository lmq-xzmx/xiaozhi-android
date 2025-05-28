#!/bin/bash

echo "🎯 开始STT功能修复流程..."

# 设置项目目录
PROJECT_DIR="/Users/xzmx/Downloads/my-project/xiaozhi-android"
cd "$PROJECT_DIR"

echo "📂 当前目录: $(pwd)"

# 步骤1: 清理项目
echo "🧹 步骤1: 清理项目..."
./gradlew clean
if [ $? -ne 0 ]; then
    echo "❌ 清理失败"
    exit 1
fi

# 步骤2: 编译APK
echo "📦 步骤2: 编译Debug APK..."
./gradlew app:assembleDebug
if [ $? -ne 0 ]; then
    echo "❌ 编译失败"
    exit 1
fi

# 步骤3: 检查APK文件
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    echo "✅ APK编译成功: $APK_PATH"
    ls -la "$APK_PATH"
else
    echo "❌ APK文件未找到"
    exit 1
fi

# 步骤4: 检查连接的设备
echo "📱 步骤4: 检查连接的Android设备..."
adb devices -l

# 步骤5: 验证设备绑定
echo "🔍 步骤5: 验证设备绑定状态..."
cd foobar
if [ -f "test_your_device_id.py" ]; then
    python3 test_your_device_id.py
else
    echo "⚠️  设备ID测试脚本不存在"
fi

cd "$PROJECT_DIR"

echo ""
echo "🎯 下一步手动操作："
echo "1. 清除应用数据（重要！）："
echo "   - 手机设置 → 应用管理 → VoiceBot → 存储 → 清除数据"
echo "   - 或运行: adb shell pm clear info.dourok.voicebot"
echo ""
echo "2. 安装APK："
echo "   adb install -r $APK_PATH"
echo ""
echo "3. 测试STT功能："
echo "   - 启动应用 → 点击录音 → 说话测试"
echo "   - 期望：显示转录文字！"

echo ""
echo "✅ 准备工作完成！请按照上述步骤进行测试。" 