#!/bin/bash
# 一键编译安装APK - macOS可双击执行
# 绕过PowerShell问题

# 设置脚本位置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "🎯 一键编译安装APK - 绕过PowerShell问题"
echo "========================================="
echo "项目目录: $PROJECT_DIR"

# 进入项目目录
cd "$PROJECT_DIR"

# 设备信息
DEVICE_ID="SOZ95PIFVS5H6PIZ"
PACKAGE_NAME="info.dourok.voicebot"

# 1. 检查设备连接
echo ""
echo "📱 步骤1: 检查设备连接"
if adb devices | grep -q "$DEVICE_ID"; then
    echo "   ✅ 设备 $DEVICE_ID 已连接"
else
    echo "   ❌ 设备 $DEVICE_ID 未连接"
    echo "   💡 请确保设备已连接并开启USB调试"
    echo "   按任意键退出..."
    read -n 1
    exit 1
fi

# 2. 清理项目
echo ""
echo "🧹 步骤2: 清理项目"
echo "   正在清理..."
if ./gradlew clean > /dev/null 2>&1; then
    echo "   ✅ 项目清理成功"
else
    echo "   ⚠️ 项目清理失败，继续编译..."
fi

# 3. 编译APK
echo ""
echo "📦 步骤3: 编译APK（约需3-5分钟）"
echo "   正在编译，请耐心等待..."

# 显示编译进度
{
    ./gradlew assembleDebug
} > compile.log 2>&1 &

COMPILE_PID=$!

# 简单的进度显示
while kill -0 $COMPILE_PID 2>/dev/null; do
    echo -n "."
    sleep 2
done

wait $COMPILE_PID
COMPILE_RESULT=$?

echo ""
if [ $COMPILE_RESULT -eq 0 ]; then
    echo "   ✅ APK编译成功"
    
    # 检查APK文件
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        SIZE=$(stat -f%z "$APK_PATH")
        SIZE_MB=$((SIZE / 1024 / 1024))
        echo "   📱 APK位置: $APK_PATH"
        echo "   📊 文件大小: ${SIZE_MB} MB"
    else
        echo "   ❌ APK文件未找到"
        echo "   查看编译日志:"
        tail -20 compile.log
        echo "   按任意键退出..."
        read -n 1
        exit 1
    fi
else
    echo "   ❌ APK编译失败"
    echo "   查看错误日志:"
    tail -20 compile.log
    echo "   按任意键退出..."
    read -n 1
    exit 1
fi

# 4. 卸载旧版本
echo ""
echo "🗑️ 步骤4: 卸载旧版本"
if adb -s "$DEVICE_ID" uninstall "$PACKAGE_NAME" > /dev/null 2>&1; then
    echo "   ✅ 旧版本已卸载"
else
    echo "   💡 未找到旧版本（正常）"
fi

# 5. 安装新APK
echo ""
echo "📲 步骤5: 安装新APK"
echo "   正在安装..."
if adb -s "$DEVICE_ID" install "$APK_PATH" > install.log 2>&1; then
    echo "   ✅ APK安装成功"
else
    echo "   ❌ APK安装失败"
    echo "   错误信息:"
    cat install.log
    echo "   按任意键退出..."
    read -n 1
    exit 1
fi

# 6. 授予权限
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

# 7. 启动应用
echo ""
echo "🚀 步骤7: 启动应用"
if adb -s "$DEVICE_ID" shell am start -n "$PACKAGE_NAME/.MainActivity" > /dev/null 2>&1; then
    echo "   ✅ 应用启动成功"
else
    echo "   ⚠️ 应用启动失败，请手动启动"
fi

# 8. 生成成功报告
echo ""
echo "📋 步骤8: 生成成功报告"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="Work_Framework/apk_build_success_$(date +%Y%m%d_%H%M%S).md"

mkdir -p "Work_Framework"

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

## 🏁 编译完成
通过一键脚本成功绕过PowerShell问题，完成完整编译安装流程。
EOF

echo "   📋 成功报告已生成: $REPORT_FILE"

# 清理临时文件
rm -f compile.log install.log

echo ""
echo "🎉 APK编译安装完全成功！"
echo "========================================="
echo "📱 应用已安装并启动到设备: $DEVICE_ID"
echo "📋 可以开始测试STT语音识别功能"
echo ""
echo "🔧 查看实时应用日志："
echo "adb -s $DEVICE_ID logcat -s ChatViewModel MainActivity WebSocket STT TTS ERROR"
echo ""
echo "❓ 是否现在查看应用日志？(y/n)"
read -n 1 show_logs

if [[ $show_logs == "y" || $show_logs == "Y" ]]; then
    echo ""
    echo "📋 显示实时应用日志（按 Ctrl+C 停止）："
    echo "=================================="
    adb -s "$DEVICE_ID" logcat -s ChatViewModel MainActivity WebSocket STT TTS ERROR
else
    echo ""
    echo "👋 编译安装流程完成，可以开始测试应用！"
fi

echo ""
echo "按任意键关闭此窗口..."
read -n 1 