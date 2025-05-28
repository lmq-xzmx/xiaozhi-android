#!/bin/bash
# 重新编译替换后的STT方案

echo "🚀 开始编译替换后的STT方案..."

# 清理缓存
echo "🧹 清理构建缓存..."
./gradlew clean

# 检查代码语法
echo "🔍 检查Kotlin代码语法..."
./gradlew app:compileDebugKotlin

if [ $? -eq 0 ]; then
    echo "✅ 代码语法检查通过"
else
    echo "❌ 代码语法检查失败，请检查错误信息"
    exit 1
fi

# 编译APK
echo "📦 编译调试版APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ STT完整方案编译成功！"
    echo "📱 APK位置: app/build/outputs/apk/debug/app-debug.apk"
else
    echo "❌ 编译失败，请检查错误信息"
    exit 1
fi
