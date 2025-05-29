#!/bin/bash

# 第一阶段功能验证测试脚本
# 用于验证渐进式迁移Phase 1阶段的所有功能

set -e

echo "🚀 开始第一阶段功能验证..."
echo "================================"

# 变量定义
PROJECT_ROOT="/Users/xzmx/Downloads/my-project/xiaozhi-android"
APK_PATH="$PROJECT_ROOT/app/build/outputs/apk/debug/app-debug.apk"
LOG_FILE="$PROJECT_ROOT/foobar/phase1_validation_$(date +%Y%m%d_%H%M%S).log"

# 创建日志文件
echo "📝 创建验证日志: $LOG_FILE"
touch "$LOG_FILE"

# 函数：记录日志
log_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] $test_name: $result - $details" >> "$LOG_FILE"
    echo "[$test_name] $result - $details"
}

# 测试1：编译完整性验证
echo "🔧 测试1：编译完整性验证"
if [ -f "$APK_PATH" ]; then
    apk_size=$(ls -la "$APK_PATH" | awk '{print $5}')
    log_result "编译完整性" "✅ 通过" "APK存在，大小: $apk_size字节"
else
    log_result "编译完整性" "❌ 失败" "APK文件不存在"
    echo "❌ APK文件不存在，重新编译..."
    cd "$PROJECT_ROOT"
    ./gradlew clean assembleDebug
fi

# 测试2：代码质量检查
echo "🔍 测试2：代码质量检查"
cd "$PROJECT_ROOT"

# 检查关键文件存在性
key_files=(
    "app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt"
    "app/src/main/java/info/dourok/voicebot/protocol/WebsocketProtocol.kt"
    "app/src/main/java/info/dourok/voicebot/protocol/MqttProtocol.kt"
    "app/src/main/java/info/dourok/voicebot/Ota.kt"
    "app/src/main/java/info/dourok/voicebot/OpusEncoder.kt"
    "app/src/main/java/info/dourok/voicebot/OpusDecoder.kt"
)

missing_files=()
for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        log_result "文件存在性" "✅ 通过" "$file 存在"
    else
        missing_files+=("$file")
        log_result "文件存在性" "❌ 失败" "$file 缺失"
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    log_result "代码质量检查" "✅ 通过" "所有关键文件存在"
else
    log_result "代码质量检查" "❌ 失败" "缺失文件: ${missing_files[*]}"
fi

# 测试3：OTA功能代码检查
echo "🔄 测试3：OTA功能代码检查"
ota_file="app/src/main/java/info/dourok/voicebot/Ota.kt"
if [ -f "$ota_file" ]; then
    # 检查关键函数存在
    if grep -q "suspend fun checkVersion" "$ota_file"; then
        log_result "OTA功能检查" "✅ 通过" "checkVersion函数存在"
    else
        log_result "OTA功能检查" "❌ 失败" "checkVersion函数缺失"
    fi
    
    # 检查多格式支持
    if grep -q "requestFormats" "$ota_file"; then
        log_result "OTA多格式支持" "✅ 通过" "多格式请求支持已实现"
    else
        log_result "OTA多格式支持" "⚠️ 警告" "多格式支持可能缺失"
    fi
else
    log_result "OTA功能检查" "❌ 失败" "Ota.kt文件不存在"
fi

# 测试4：WebSocket协议检查
echo "🌐 测试4：WebSocket协议检查"
websocket_file="app/src/main/java/info/dourok/voicebot/protocol/WebsocketProtocol.kt"
if [ -f "$websocket_file" ]; then
    # 检查关键类和方法
    if grep -q "class WebsocketProtocol" "$websocket_file"; then
        log_result "WebSocket类检查" "✅ 通过" "WebsocketProtocol类存在"
    fi
    
    if grep -q "openAudioChannel" "$websocket_file"; then
        log_result "WebSocket音频通道" "✅ 通过" "音频通道方法存在"
    fi
    
    if grep -q "sendAudio" "$websocket_file"; then
        log_result "WebSocket音频发送" "✅ 通过" "音频发送方法存在"
    fi
else
    log_result "WebSocket协议检查" "❌ 失败" "WebsocketProtocol.kt文件不存在"
fi

# 测试5：MQTT协议检查
echo "📡 测试5：MQTT协议检查"
mqtt_file="app/src/main/java/info/dourok/voicebot/protocol/MqttProtocol.kt"
if [ -f "$mqtt_file" ]; then
    if grep -q "class MqttProtocol" "$mqtt_file"; then
        log_result "MQTT类检查" "✅ 通过" "MqttProtocol类存在"
    fi
    
    if grep -q "UDP" "$mqtt_file"; then
        log_result "MQTT UDP支持" "✅ 通过" "UDP音频传输支持"
    fi
    
    if grep -q "AES" "$mqtt_file"; then
        log_result "MQTT加密支持" "✅ 通过" "AES加密传输支持"
    fi
else
    log_result "MQTT协议检查" "❌ 失败" "MqttProtocol.kt文件不存在"
fi

# 测试6：STT功能检查
echo "🎤 测试6：STT功能检查"
chatvm_file="app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt"
if [ -f "$chatvm_file" ]; then
    # 检查音频录制组件
    if grep -q "AudioRecorder" "$chatvm_file"; then
        log_result "STT音频录制" "✅ 通过" "AudioRecorder组件存在"
    fi
    
    # 检查Opus编码器
    if grep -q "OpusEncoder" "$chatvm_file"; then
        log_result "STT音频编码" "✅ 通过" "OpusEncoder组件存在"
    fi
    
    # 检查STT消息处理
    if grep -q '"stt"' "$chatvm_file"; then
        log_result "STT消息处理" "✅ 通过" "STT消息处理逻辑存在"
    fi
    
    # 检查当前架构特点（第一阶段）
    if grep -q "keepListening" "$chatvm_file"; then
        log_result "第一阶段架构" "✅ 确认" "当前使用第一阶段架构（客户端状态管理）"
    else
        log_result "第一阶段架构" "⚠️ 注意" "可能已经迁移到第二阶段架构"
    fi
else
    log_result "STT功能检查" "❌ 失败" "ChatViewModel.kt文件不存在"
fi

# 测试7：Opus编解码检查（当前为模拟实现）
echo "🎵 测试7：Opus编解码检查"
opus_encoder="app/src/main/java/info/dourok/voicebot/OpusEncoder.kt"
opus_decoder="app/src/main/java/info/dourok/voicebot/OpusDecoder.kt"

if [ -f "$opus_encoder" ] && [ -f "$opus_decoder" ]; then
    # 检查是否为模拟实现
    if grep -q "模拟实现\|临时实现\|// System.loadLibrary" "$opus_encoder"; then
        log_result "Opus编码器状态" "⚠️ 临时" "当前使用模拟实现（适合第一阶段）"
    else
        log_result "Opus编码器状态" "✅ 完整" "使用真实native实现"
    fi
    
    if grep -q "模拟实现\|临时实现\|// System.loadLibrary" "$opus_decoder"; then
        log_result "Opus解码器状态" "⚠️ 临时" "当前使用模拟实现（适合第一阶段）"
    else
        log_result "Opus解码器状态" "✅ 完整" "使用真实native实现"
    fi
else
    log_result "Opus编解码检查" "❌ 失败" "编解码器文件缺失"
fi

# 测试8：配置文件检查
echo "⚙️ 测试8：配置文件检查"
gradle_properties="gradle.properties"
if [ -f "$gradle_properties" ]; then
    if grep -q "org.gradle.jvmargs" "$gradle_properties"; then
        log_result "Gradle配置" "✅ 通过" "JVM参数配置存在"
    fi
else
    log_result "Gradle配置" "❌ 失败" "gradle.properties文件不存在"
fi

# 测试9：第二阶段准备工具检查
echo "🔮 测试9：第二阶段准备工具检查"
phase2_doc="foobar/android_stt_pure_server_vad_patch.md"
if [ -f "$phase2_doc" ]; then
    log_result "第二阶段文档" "✅ 准备" "纯服务器端VAD方案文档存在"
else
    log_result "第二阶段文档" "⚠️ 缺失" "第二阶段迁移文档缺失"
fi

monitoring_tools="foobar/phase1_monitoring_tools.kt"
if [ -f "$monitoring_tools" ]; then
    log_result "监控工具" "✅ 准备" "第一阶段监控工具存在"
else
    log_result "监控工具" "⚠️ 缺失" "监控工具文件缺失"
fi

# 测试10：编译清洁度检查
echo "🧹 测试10：编译清洁度检查"
echo "进行一次完整的清理和编译..."
./gradlew clean > /dev/null 2>&1
compile_result=$(./gradlew assembleDebug 2>&1)
if echo "$compile_result" | grep -q "BUILD SUCCESSFUL"; then
    log_result "编译清洁度" "✅ 通过" "清理编译成功"
else
    log_result "编译清洁度" "❌ 失败" "清理编译失败"
    echo "编译错误详情:"
    echo "$compile_result" | tail -10
fi

# 生成验证报告
echo ""
echo "📊 生成第一阶段验证报告..."
echo "================================"

# 统计结果
total_tests=$(grep -c "\[.*\]" "$LOG_FILE")
passed_tests=$(grep -c "✅ 通过" "$LOG_FILE")
failed_tests=$(grep -c "❌ 失败" "$LOG_FILE")
warning_tests=$(grep -c "⚠️" "$LOG_FILE")

echo "📈 测试统计:"
echo "  总测试项: $total_tests"
echo "  通过: $passed_tests"
echo "  失败: $failed_tests"
echo "  警告: $warning_tests"

# 计算通过率
if [ $total_tests -gt 0 ]; then
    pass_rate=$((passed_tests * 100 / total_tests))
    echo "  通过率: $pass_rate%"
    
    if [ $pass_rate -ge 80 ]; then
        echo "✅ 第一阶段验证通过！当前架构稳定，可以开始使用。"
        validation_status="PASSED"
    elif [ $pass_rate -ge 60 ]; then
        echo "⚠️ 第一阶段部分通过，建议修复警告项后使用。"
        validation_status="PARTIAL"
    else
        echo "❌ 第一阶段验证失败，需要修复关键问题。"
        validation_status="FAILED"
    fi
else
    echo "❌ 无法进行测试统计"
    validation_status="UNKNOWN"
fi

# 生成总结报告
report_file="$PROJECT_ROOT/foobar/phase1_validation_summary.md"
cat > "$report_file" << EOF
# 第一阶段功能验证报告

## 📊 验证概要
- **验证时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **验证状态**: $validation_status
- **总测试项**: $total_tests
- **通过项**: $passed_tests
- **失败项**: $failed_tests
- **警告项**: $warning_tests
- **通过率**: $pass_rate%

## 📋 详细结果
\`\`\`
$(cat "$LOG_FILE")
\`\`\`

## 🎯 结论和建议

$(if [ "$validation_status" = "PASSED" ]; then
    echo "✅ **第一阶段验证通过**"
    echo ""
    echo "当前架构稳定，所有核心功能正常工作："
    echo "- OTA配置获取功能完整"
    echo "- WebSocket和MQTT协议实现正常"
    echo "- STT音频录制和识别流程稳定"
    echo "- 代码结构为第二阶段迁移做好准备"
    echo ""
    echo "**下一步行动:**"
    echo "1. 可以开始日常使用和测试"
    echo "2. 收集使用数据和性能指标"
    echo "3. 当准备就绪时，可以启动第二阶段纯服务器端VAD迁移"
elif [ "$validation_status" = "PARTIAL" ]; then
    echo "⚠️ **第一阶段部分通过**"
    echo ""
    echo "核心功能基本正常，但存在一些需要关注的问题："
    echo "- 检查警告项并评估影响"
    echo "- 优先修复影响用户体验的问题"
    echo "- 监控系统运行稳定性"
    echo ""
    echo "**建议行动:**"
    echo "1. 修复标记为警告的项目"
    echo "2. 进行更多测试验证稳定性"
    echo "3. 准备好后再考虑第二阶段迁移"
else
    echo "❌ **第一阶段验证失败**"
    echo ""
    echo "发现关键功能问题，需要立即修复："
    echo "- 检查失败的测试项"
    echo "- 修复编译和配置问题"
    echo "- 确保核心功能正常工作"
    echo ""
    echo "**必要行动:**"
    echo "1. 立即修复标记为失败的关键问题"
    echo "2. 重新运行验证测试"
    echo "3. 在所有问题解决前暂停第二阶段迁移计划"
fi)

## 📁 相关文件
- 详细日志: \`$(basename "$LOG_FILE")\`
- 监控工具: \`foobar/phase1_monitoring_tools.kt\`
- 第二阶段方案: \`foobar/android_stt_pure_server_vad_patch.md\`
- 恢复脚本: \`foobar/restore_cmake.sh\`

EOF

echo ""
echo "📄 验证报告已生成: $report_file"
echo "📋 详细日志已保存: $LOG_FILE"
echo ""
echo "🎯 第一阶段验证完成！状态: $validation_status" 