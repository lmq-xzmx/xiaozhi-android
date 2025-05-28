#!/bin/bash

echo "🎯 开始编译安装APK - OTA配置升级版本"
echo "========================================="

DEVICE_ID="SOZ95PIFVS5H6PIZ"
PACKAGE_NAME="info.dourok.voicebot"

# 步骤1: 检查设备连接
echo "📱 步骤1: 检查设备连接"
if adb devices | grep -q "$DEVICE_ID"; then
    echo "   ✅ 设备 $DEVICE_ID 已连接"
else
    echo "   ❌ 设备 $DEVICE_ID 未连接"
    echo "   💡 请确保设备已连接并开启USB调试"
    exit 1
fi

# 步骤2: 清理项目
echo ""
echo "🧹 步骤2: 清理项目"
./gradlew clean

# 步骤3: 编译APK
echo ""
echo "📦 步骤3: 编译APK（约需3-5分钟）"
echo "   正在编译，请耐心等待..."
./gradlew assembleDebug

# 检查APK是否生成
if [ -f "app/build/outputs/apk/debug/app-debug.apk" ]; then
    SIZE=$(stat -f%z "app/build/outputs/apk/debug/app-debug.apk")
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "   ✅ APK编译成功"
    echo "   📱 APK位置: app/build/outputs/apk/debug/app-debug.apk"
    echo "   📊 文件大小: ${SIZE_MB} MB"
else
    echo "   ❌ APK编译失败"
    exit 1
fi

# 步骤4: 卸载旧版本
echo ""
echo "🗑️ 步骤4: 卸载旧版本"
if adb -s "$DEVICE_ID" uninstall "$PACKAGE_NAME" > /dev/null 2>&1; then
    echo "   ✅ 旧版本已卸载"
else
    echo "   💡 未找到旧版本（正常）"
fi

# 步骤5: 安装新APK
echo ""
echo "📲 步骤5: 安装新APK"
if adb -s "$DEVICE_ID" install "app/build/outputs/apk/debug/app-debug.apk"; then
    echo "   ✅ APK安装成功"
else
    echo "   ❌ APK安装失败"
    exit 1
fi

# 步骤6: 授予权限
echo ""
echo "🔐 步骤6: 授予应用权限"
PERMISSIONS=(
    "android.permission.RECORD_AUDIO"
    "android.permission.INTERNET"
    "android.permission.ACCESS_NETWORK_STATE"
    "android.permission.WAKE_LOCK"
)

for permission in "${PERMISSIONS[@]}"; do
    perm_name=$(echo "$permission" | awk -F. '{print $NF}')
    if adb -s "$DEVICE_ID" shell pm grant "$PACKAGE_NAME" "$permission" > /dev/null 2>&1; then
        echo "   ✅ 权限 $perm_name 已授予"
    else
        echo "   ⚠️ 权限 $perm_name 可能已存在或不需要"
    fi
done

# 步骤7: 启动应用
echo ""
echo "🚀 步骤7: 启动应用"
if adb -s "$DEVICE_ID" shell am start -n "$PACKAGE_NAME/.MainActivity" > /dev/null 2>&1; then
    echo "   ✅ 应用启动成功"
else
    echo "   ⚠️ 应用启动失败，请手动启动"
fi

echo ""
echo "🎉 编译安装完成！"
echo "========================================="
echo "✅ APK已成功编译并安装到设备"
echo "🔧 OTA配置升级功能已集成"
echo "🎙️ STT语音识别功能保持完整"
echo "📱 现在可以测试应用功能"
echo ""
echo "🔍 查看OTA配置日志:"
echo "adb -s $DEVICE_ID logcat -s ChatViewModel OtaConfigManager OtaIntegrationService" 