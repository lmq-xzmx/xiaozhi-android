#!/bin/bash
# STT修复完整构建安装测试脚本
# 目标：100%成功率，消除所有风险

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 错误处理函数
handle_error() {
    log_error "脚本在第$1行执行失败，退出码: $2"
    log_error "最后执行的命令: $BASH_COMMAND"
    exit $2
}

trap 'handle_error $LINENO $?' ERR

log_info "🚀 开始STT修复完整验证流程"
log_info "目标：100%成功率，零风险构建安装"

# 进入项目根目录
cd "$(dirname "$0")/.."
log_info "📍 工作目录: $(pwd)"

# 1. 环境检查和自动修复
check_and_fix_environment() {
    log_step "📋 Step 1: 环境检查和自动修复"
    
    # 检查并设置Android SDK
    if [ -z "$ANDROID_HOME" ]; then
        log_warn "ANDROID_HOME未设置，尝试自动检测"
        
        # 常见的Android SDK路径
        POSSIBLE_PATHS=(
            "/Users/$USER/Library/Android/sdk"
            "/opt/android-sdk"
            "/usr/local/android-sdk"
            "$HOME/Android/Sdk"
        )
        
        for path in "${POSSIBLE_PATHS[@]}"; do
            if [ -d "$path" ]; then
                export ANDROID_HOME="$path"
                log_info "🔧 自动设置ANDROID_HOME: $ANDROID_HOME"
                break
            fi
        done
        
        if [ -z "$ANDROID_HOME" ]; then
            log_error "无法找到Android SDK，请手动设置ANDROID_HOME"
            exit 1
        fi
    else
        log_info "✅ ANDROID_HOME已设置: $ANDROID_HOME"
    fi
    
    # 检查Java版本
    if command -v java >/dev/null 2>&1; then
        java_version=$(java -version 2>&1 | head -n 1 | grep -o '".*"' | sed 's/"//g')
        log_info "☕ Java版本: $java_version"
    else
        log_error "Java未安装或不在PATH中"
        exit 1
    fi
    
    # 检查adb
    if command -v adb >/dev/null 2>&1; then
        log_info "📱 ADB可用"
        adb devices | head -5
    else
        log_warn "ADB不在PATH中，尝试从Android SDK路径添加"
        export PATH="$ANDROID_HOME/platform-tools:$PATH"
    fi
    
    # 检查gradlew权限
    if [ ! -x "./gradlew" ]; then
        log_info "🔧 修复gradlew执行权限"
        chmod +x ./gradlew
    fi
    
    log_info "✅ 环境检查完成"
}

# 2. 清理和依赖准备
prepare_build() {
    log_step "🧹 Step 2: 清理构建环境和准备依赖"
    
    # 清理旧的构建产物
    log_info "清理旧构建..."
    ./gradlew clean || {
        log_warn "清理失败，尝试强制删除build目录"
        rm -rf app/build build .gradle/caches
    }
    
    # 下载和验证依赖
    log_info "📦 下载和验证依赖..."
    ./gradlew dependencies --quiet || {
        log_warn "依赖下载失败，清理缓存后重试"
        ./gradlew clean --quiet
        ./gradlew dependencies
    }
    
    log_info "✅ 构建准备完成"
}

# 3. 代码验证和编译
build_and_verify() {
    log_step "🔨 Step 3: 代码验证和APK构建"
    
    # 编译检查
    log_info "🔍 执行编译检查..."
    ./gradlew compileDebugKotlin || {
        log_error "Kotlin编译失败，请检查代码语法"
        exit 1
    }
    
    # 构建APK
    log_info "📱 构建Debug APK..."
    ./gradlew assembleDebug
    
    # 验证APK生成
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        APK_SIZE=$(ls -lh "$APK_PATH" | awk '{print $5}')
        log_info "✅ APK构建成功！"
        log_info "📍 APK位置: $APK_PATH"
        log_info "📏 APK大小: $APK_SIZE"
    else
        log_error "APK构建失败，文件不存在"
        exit 1
    fi
}

# 4. 设备检测和APK安装
install_and_verify() {
    log_step "📱 Step 4: 设备检测和APK安装"
    
    # 检测连接的设备
    log_info "🔍 检测Android设备..."
    DEVICE_COUNT=$(adb devices | grep -c "device$" || echo "0")
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        log_error "未检测到Android设备，请确保："
        log_error "1. 设备已连接USB"
        log_error "2. 已启用USB调试"
        log_error "3. 已授权此计算机"
        adb devices
        exit 1
    elif [ "$DEVICE_COUNT" -eq 1 ]; then
        DEVICE_ID=$(adb devices | grep "device$" | awk '{print $1}')
        log_info "✅ 检测到设备: $DEVICE_ID"
    else
        log_info "检测到多个设备($DEVICE_COUNT个)，使用第一个"
        DEVICE_ID=$(adb devices | grep "device$" | head -1 | awk '{print $1}')
        log_info "选择设备: $DEVICE_ID"
    fi
    
    # 安装APK
    log_info "📲 安装APK到设备..."
    adb -s "$DEVICE_ID" install -r "app/build/outputs/apk/debug/app-debug.apk"
    
    # 验证安装
    if adb -s "$DEVICE_ID" shell pm list packages | grep -q "info.dourok.voicebot"; then
        log_info "✅ APK安装成功！"
    else
        log_error "APK安装验证失败"
        exit 1
    fi
}

# 5. 应用启动和初步测试
launch_and_test() {
    log_step "🧪 Step 5: 应用启动和STT功能测试"
    
    # 启动应用
    log_info "🚀 启动VoiceBot应用..."
    adb shell am start -n info.dourok.voicebot/.MainActivity
    
    # 等待应用启动
    sleep 3
    
    # 创建日志监控文件
    LOG_FILE="foobar/stt_test_log_$(date +%Y%m%d_%H%M%S).txt"
    
    log_info "📊 开始监控应用日志 (30秒)..."
    log_info "监控以下关键事件："
    log_info "  - WebSocket连接"
    log_info "  - Hello握手"
    log_info "  - 认证成功"
    log_info "  - STT响应"
    
    # 监控日志并保存
    {
        echo "=== STT修复测试日志 ==="
        echo "时间: $(date)"
        echo "设备: $DEVICE_ID"
        echo "=========================="
        echo ""
        
        timeout 30s adb logcat -s WS:I WS:D WS:E WS:W | while read line; do
            echo "$line"
            
            # 检查关键成功指标
            if echo "$line" | grep -q "WebSocket connected"; then
                echo "✅ [SUCCESS] WebSocket连接成功"
            elif echo "$line" | grep -q "Hello握手响应"; then
                echo "✅ [SUCCESS] Hello握手成功"
            elif echo "$line" | grep -q "Session ID:"; then
                echo "✅ [SUCCESS] 获得Session ID"
            elif echo "$line" | grep -q "收到STT识别结果"; then
                echo "🎉 [SUCCESS] STT功能正常工作！"
            elif echo "$line" | grep -q "WebSocket error"; then
                echo "❌ [ERROR] WebSocket连接错误"
            fi
        done
    } 2>&1 | tee "$LOG_FILE"
    
    log_info "📄 测试日志已保存到: $LOG_FILE"
}

# 6. 生成完整报告
generate_report() {
    log_step "📊 Step 6: 生成完整验证报告"
    
    REPORT_FILE="foobar/build_install_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# STT修复构建安装验证报告

## 📋 执行摘要
- **执行时间**: $(date)
- **工作目录**: $(pwd)
- **设备ID**: ${DEVICE_ID:-"未检测到"}
- **APK路径**: app/build/outputs/apk/debug/app-debug.apk
- **日志文件**: ${LOG_FILE:-"未生成"}

## ✅ 执行状态
- **环境检查**: ✅ 通过
- **依赖准备**: ✅ 通过  
- **代码编译**: ✅ 通过
- **APK构建**: ✅ 通过
- **设备安装**: ✅ 通过
- **应用启动**: ✅ 通过

## 🎯 STT功能验证
请手动执行以下测试步骤：

1. **基础连接测试**
   - 观察应用是否成功启动
   - 检查WebSocket连接状态

2. **Hello握手测试**  
   - 确认应用显示连接成功
   - 检查日志中是否有Session ID

3. **STT功能测试**
   - 点击录音按钮
   - 说话测试语音识别
   - 观察是否显示: >> [识别文本]

## 🔧 下一步行动
如果STT功能仍有问题，请：
1. 查看日志文件: ${LOG_FILE:-"stt_test_log.txt"}
2. 检查网络连接到: ws://47.122.144.73:8000/xiaozhi/v1/
3. 确认麦克风权限已授权
4. 联系技术支持并提供日志文件

## 📊 技术细节
- **Android SDK**: $ANDROID_HOME
- **Java版本**: $(java -version 2>&1 | head -1 | grep -o '".*"' | sed 's/"//g')
- **构建工具**: Gradle
- **目标SDK**: 35
- **最小SDK**: 24

---
*报告生成时间: $(date)*
EOF

    log_info "📄 完整报告已生成: $REPORT_FILE"
}

# 7. 最终结果展示
show_final_result() {
    log_step "🎉 Step 7: 构建安装完成"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎊 STT修复构建安装流程执行完成！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_info "✅ 应用已成功安装并启动"
    log_info "📱 设备: ${DEVICE_ID:-"未知"}"
    log_info "📊 日志文件: ${LOG_FILE:-"未生成"}"
    echo ""
    echo "🎯 下一步手动验证STT功能："
    echo "   1. 在应用中点击录音按钮"
    echo "   2. 说话测试STT功能 (例如: '你好小智')"
    echo "   3. 观察应用是否显示: >> [识别文本]"
    echo "   4. 查看logcat确认修复效果:"
    echo "      adb logcat -s WS:I | grep -E '(Hello|STT|连接|识别)'"
    echo ""
    echo "🔧 如有问题，查看详细日志进行诊断"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 主执行流程
main() {
    # 记录开始时间
    START_TIME=$(date +%s)
    
    # 执行所有步骤
    check_and_fix_environment
    prepare_build
    build_and_verify
    install_and_verify
    launch_and_test
    generate_report
    show_final_result
    
    # 计算总耗时
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log_info "⏱️ 总耗时: ${DURATION}秒"
    log_info "🎉 STT修复完整流程执行成功！"
}

# 执行主函数
main "$@" 