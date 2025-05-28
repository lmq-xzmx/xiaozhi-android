#!/bin/bash

# 🚀 WebSocket配置修复自动化执行脚本
echo "🚀 WebSocket配置修复自动化执行脚本"
echo "=================================="
echo "目标：自动完成编译、安装、测试的完整流程"
echo ""

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 应用包名
PACKAGE_NAME="info.dourok.voicebot"

# 函数：打印带颜色的消息
print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 第一步：编译修复后的代码
print_step "第一步：编译修复后的代码"
echo "=========================="

echo "🧹 清理之前的构建..."
./gradlew clean

if [ $? -eq 0 ]; then
    print_success "清理完成"
else
    print_error "清理失败"
    exit 1
fi

echo ""
echo "🔨 开始编译..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    print_success "编译成功！"
    
    # 检查APK文件是否存在
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        APK_SIZE=$(ls -lh "$APK_PATH" | awk '{print $5}')
        print_success "APK已生成: $APK_PATH (大小: $APK_SIZE)"
    else
        print_error "APK文件未找到: $APK_PATH"
        exit 1
    fi
else
    print_error "编译失败！"
    echo ""
    echo "🔍 尝试查看详细错误信息..."
    ./gradlew assembleDebug --stacktrace
    exit 1
fi

echo ""

# 第二步：检查设备连接
print_step "第二步：检查设备连接"
echo "========================"

echo "📱 检查ADB设备连接..."
DEVICES=$(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l)

if [ $DEVICES -eq 0 ]; then
    print_error "没有检测到Android设备"
    echo "请确保："
    echo "1. 设备已连接并开启USB调试"
    echo "2. 已授权此计算机进行调试"
    echo "3. ADB服务正常运行"
    exit 1
elif [ $DEVICES -eq 1 ]; then
    DEVICE_INFO=$(adb devices | grep -v "List of devices" | grep -v "^$")
    print_success "检测到设备: $DEVICE_INFO"
else
    print_warning "检测到多个设备 ($DEVICES 个)"
    echo "设备列表："
    adb devices
    echo ""
    echo "将使用第一个设备进行安装"
fi

echo ""

# 第三步：安装修复后的APK
print_step "第三步：安装修复后的APK"
echo "========================="

echo "📦 安装APK到设备..."
adb install -r "$APK_PATH"

if [ $? -eq 0 ]; then
    print_success "APK安装成功！"
    
    # 获取安装后的版本信息
    VERSION_INFO=$(adb shell dumpsys package $PACKAGE_NAME | grep versionName | head -1)
    if [ ! -z "$VERSION_INFO" ]; then
        print_success "应用版本: $VERSION_INFO"
    fi
else
    print_error "APK安装失败！"
    echo ""
    echo "🔍 尝试卸载旧版本后重新安装..."
    adb uninstall $PACKAGE_NAME
    sleep 2
    adb install "$APK_PATH"
    
    if [ $? -eq 0 ]; then
        print_success "重新安装成功！"
    else
        print_error "重新安装也失败了"
        exit 1
    fi
fi

echo ""

# 第四步：运行修复验证测试
print_step "第四步：运行修复验证测试"
echo "=========================="

if [ -f "foobar/websocket_config_fix_test.sh" ]; then
    print_success "找到测试脚本，开始执行..."
    echo ""
    
    # 确保测试脚本有执行权限
    chmod +x foobar/websocket_config_fix_test.sh
    
    # 执行测试脚本
    ./foobar/websocket_config_fix_test.sh
    
    TEST_RESULT=$?
    echo ""
    
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "测试脚本执行完成"
    else
        print_warning "测试脚本执行过程中有警告或错误"
    fi
else
    print_error "测试脚本未找到: foobar/websocket_config_fix_test.sh"
    echo ""
    echo "🔧 手动测试步骤："
    echo "1. 启动应用: adb shell am start -n $PACKAGE_NAME/.MainActivity"
    echo "2. 观察日志: adb logcat | grep -E '(WebSocket|ActivationManager|ChatViewModel)'"
    echo "3. 测试重启: adb shell am force-stop $PACKAGE_NAME && adb shell am start -n $PACKAGE_NAME/.MainActivity"
fi

echo ""

# 第五步：总结和下一步建议
print_step "第五步：总结和下一步建议"
echo "=========================="

print_success "WebSocket配置修复流程执行完成！"
echo ""
echo "📋 已完成的步骤："
echo "✅ 编译修复后的代码"
echo "✅ 安装新APK到设备"
echo "✅ 运行验证测试"
echo ""
echo "🎯 下一步手动验证："
echo "1. 打开应用，完成设备绑定（如需要）"
echo "2. 测试语音功能是否正常"
echo "3. 重启应用，检查是否自动恢复连接"
echo ""
echo "📊 关键成功标志："
echo "- 应用重启后无需重新绑定"
echo "- 日志显示 '✅ 使用缓存的WebSocket配置' 或 '✅ 配置已从DeviceConfigManager恢复'"
echo "- WebSocket连接自动建立"
echo ""
echo "🔍 如果仍有问题，请查看："
echo "- foobar/next_steps_websocket_fix.md - 详细故障排除指南"
echo "- foobar/websocket_config_failure_root_cause_analysis.md - 根本原因分析"
echo ""
print_success "�� 修复流程完成！请测试应用功能。" 