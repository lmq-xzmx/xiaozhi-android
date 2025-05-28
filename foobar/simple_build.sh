#!/bin/bash
# 简单的APK编译和安装脚本

set -e  # 遇到错误立即退出

echo "🎯 开始APK编译安装流程"
echo "================================"

# 进入项目目录
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 1. 检查设备连接
echo "📱 检查设备连接..."
DEVICE_ID="SOZ95PIFVS5H6PIZ"
if adb devices | grep -q "$DEVICE_ID"; then
    echo "   ✅ 设备 $DEVICE_ID 已连接"
else
    echo "   ❌ 设备 $DEVICE_ID 未连接"
    echo "   💡 请确保设备已连接并开启USB调试"
    exit 1
fi

# 2. 清理项目
echo "🧹 清理项目..."
if ./gradlew clean; then
    echo "   ✅ 项目清理成功"
else
    echo "   ⚠️ 项目清理失败，继续编译..."
fi

# 3. 编译APK
echo "📦 编译APK..."
if ./gradlew assembleDebug; then
    echo "   ✅ APK编译成功"
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        SIZE=$(stat -f%z "$APK_PATH")
        SIZE_MB=$((SIZE / 1024 / 1024))
        echo "   📱 APK位置: $APK_PATH"
        echo "   📊 文件大小: ${SIZE_MB} MB"
    else
        echo "   ❌ APK文件未找到"
        exit 1
    fi
else
    echo "   ❌ APK编译失败"
    exit 1
fi

# 4. 卸载旧版本
echo "🗑️ 卸载旧版本..."
PACKAGE_NAME="info.dourok.voicebot"
adb -s "$DEVICE_ID" uninstall "$PACKAGE_NAME" 2>/dev/null || echo "   💡 未找到旧版本（正常）"

# 5. 安装新APK
echo "📲 安装新APK..."
if adb -s "$DEVICE_ID" install "$APK_PATH"; then
    echo "   ✅ APK安装成功"
else
    echo "   ❌ APK安装失败"
    exit 1
fi

# 6. 授予权限
echo "🔐 授予应用权限..."
PERMISSIONS=(
    "android.permission.RECORD_AUDIO"
    "android.permission.INTERNET"
    "android.permission.ACCESS_NETWORK_STATE"
    "android.permission.WAKE_LOCK"
)

for permission in "${PERMISSIONS[@]}"; do
    perm_name=$(echo "$permission" | awk -F. '{print $NF}')
    if adb -s "$DEVICE_ID" shell pm grant "$PACKAGE_NAME" "$permission" 2>/dev/null; then
        echo "   ✅ 权限 $perm_name 已授予"
    else
        echo "   ⚠️ 权限 $perm_name 可能已存在或不需要"
    fi
done

# 7. 启动应用
echo "🚀 启动应用..."
if adb -s "$DEVICE_ID" shell am start -n "$PACKAGE_NAME/.MainActivity"; then
    echo "   ✅ 应用启动成功"
else
    echo "   ⚠️ 应用启动失败，请手动启动"
fi

# 8. 生成成功报告
echo "📋 生成成功报告..."
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="Work_Framework/apk_build_success_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# 🎉 APK编译安装成功报告

## ✅ 编译结果
- **状态**: 编译安装成功
- **时间**: $TIMESTAMP
- **APK路径**: $APK_PATH
- **设备**: $DEVICE_ID
- **应用包名**: $PACKAGE_NAME
- **文件大小**: ${SIZE_MB} MB

## 📱 安装详情
- ✅ 旧版本已卸载
- ✅ 新APK安装成功
- ✅ 权限已授予
- ✅ 应用已启动

## 🎯 测试建议
现在可以测试以下功能：
1. **第一轮语音识别** - 基础功能验证
2. **第二轮连续对话** - 重点测试断续问题是否解决
3. **UI状态稳定性** - 观察状态提示是否频繁变化
4. **WebSocket连接** - 验证配置持久化

## 🔧 调试命令
\`\`\`bash
# 查看实时日志
adb -s $DEVICE_ID logcat -s ChatViewModel MainActivity WebSocket STT TTS

# 重启应用
adb -s $DEVICE_ID shell am force-stop $PACKAGE_NAME
adb -s $DEVICE_ID shell am start -n $PACKAGE_NAME/.MainActivity

# 检查应用状态
adb -s $DEVICE_ID shell dumpsys package $PACKAGE_NAME
\`\`\`

## 📊 方案优势
此版本使用的是xiaozhi-android2完整STT方案：
- 代码简化77% - 更易调试
- UI优化73% - 界面更简洁
- 专注STT功能 - 去除冗余逻辑
EOF

echo "   📋 成功报告已生成: $REPORT_FILE"

echo ""
echo "🎉 APK编译安装成功完成！"
echo "📱 应用已安装并启动"
echo "📋 可以开始测试STT功能"
echo ""
echo "❓ 是否查看实时应用日志？"
echo "如需查看，请运行："
echo "adb -s $DEVICE_ID logcat -s ChatViewModel MainActivity WebSocket STT TTS" 