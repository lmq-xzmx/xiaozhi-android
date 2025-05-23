#!/bin/bash

echo "=== 测试Android项目编译 ==="
echo ""

cd ..

echo "📂 当前目录: $(pwd)"
echo ""

echo "🔨 开始编译Kotlin代码..."
./gradlew app:compileDebugKotlin

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Kotlin编译成功！"
    echo ""
    echo "🔨 尝试完整构建..."
    ./gradlew app:assembleDebug
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 完整构建成功！"
        echo ""
        echo "📋 下一步操作："
        echo "1. 清除应用数据（手动在设备上操作）"
        echo "2. 安装APK到设备"
        echo "3. 测试STT功能"
        echo "4. 检查设备ID日志: 00:11:22:33:44:55"
    else
        echo ""
        echo "⚠️ 完整构建失败，但Kotlin编译成功"
        echo "请检查其他构建错误"
    fi
else
    echo ""
    echo "❌ Kotlin编译失败"
    echo "请检查编译错误并修正代码"
    exit 1
fi

echo ""
echo "📱 验证设备绑定状态:"
echo "cd foobar && python3 test_your_device_id.py" 