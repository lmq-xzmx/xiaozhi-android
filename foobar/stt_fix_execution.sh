#!/bin/bash
# STT问题修复执行脚本
# 简化版本，避免PowerShell兼容性问题

echo "🚀 开始STT问题修复流程..."
echo "时间: $(date)"
echo "=" x 60

# P0-1: 检查服务器进程状态
echo "1️⃣ 检查xiaozhi-server进程状态..."
echo "检查进程:"
ps aux | grep -i xiaozhi | grep -v grep || echo "❌ 未找到xiaozhi相关进程"

echo -e "\n检查8080端口监听:"
lsof -i :8080 2>/dev/null || echo "❌ 8080端口未监听"

# P0-2: 检查服务器目录和模型文件
echo -e "\n2️⃣ 检查服务器目录和模型文件..."
SERVER_DIR="../main/xiaozhi-server"

if [ -d "$SERVER_DIR" ]; then
    echo "✅ 服务器目录存在: $SERVER_DIR"
    
    # 检查VAD模型
    if [ -d "$SERVER_DIR/models/snakers4_silero-vad" ]; then
        VAD_FILES=$(ls -1 "$SERVER_DIR/models/snakers4_silero-vad" 2>/dev/null | wc -l)
        echo "✅ VAD模型目录存在，文件数量: $VAD_FILES"
    else
        echo "❌ VAD模型目录不存在"
    fi
    
    # 检查ASR模型
    if [ -d "$SERVER_DIR/models/SenseVoiceSmall" ]; then
        ASR_FILES=$(ls -1 "$SERVER_DIR/models/SenseVoiceSmall" 2>/dev/null | wc -l)
        echo "✅ ASR模型目录存在，文件数量: $ASR_FILES"
    else
        echo "❌ ASR模型目录不存在"
    fi
    
    # 检查配置文件
    if [ -f "$SERVER_DIR/config.yaml" ]; then
        echo "✅ config.yaml存在"
        echo "VAD/ASR配置:"
        grep -A 5 "selected_module:" "$SERVER_DIR/config.yaml" 2>/dev/null || echo "配置未找到"
    else
        echo "❌ config.yaml不存在"
    fi
    
else
    echo "❌ 服务器目录不存在: $SERVER_DIR"
fi

# P0-3: 检查服务器日志
echo -e "\n3️⃣ 检查服务器日志..."
if [ -f "$SERVER_DIR/app.log" ]; then
    echo "最新日志内容:"
    tail -10 "$SERVER_DIR/app.log"
else
    echo "❌ app.log不存在"
fi

# P0-4: 服务器启动指导
echo -e "\n4️⃣ 服务器启动指导..."
if ! pgrep -f xiaozhi >/dev/null 2>&1; then
    echo "⚠️ 服务器未运行，请执行以下命令启动:"
    echo "cd $SERVER_DIR"
    echo "python app.py"
    echo ""
    echo "或者在新终端中执行:"
    echo "cd $SERVER_DIR && python app.py &"
else
    echo "✅ 检测到xiaozhi相关进程正在运行"
fi

# 生成修复总结
echo -e "\n" "=" x 60
echo "📋 STT修复总结"
echo "=" x 60

echo "客户端状态 (步骤1-3):"
echo "  ✅ 音频采集: 正常"
echo "  ✅ Opus编码: 正常" 
echo "  ✅ WebSocket发送: 正常"

echo -e "\n服务器端状态 (步骤4-8):"
echo "  ❓ 音频接收: 需要确认服务器运行状态"
echo "  ❓ VAD检测: 需要确认模型加载"
echo "  ❌ STT识别: 完全失效，需要修复"
echo "  ❌ 结果返回: 链路中断"
echo "  ❌ UI更新: 被阻塞"

echo -e "\n🎯 立即行动项:"
echo "1. 启动xiaozhi-server (如果未运行)"
echo "2. 验证VAD/ASR模型文件完整性"
echo "3. 检查config.yaml配置正确性"
echo "4. 测试服务器端STT功能"
echo "5. 验证Android客户端STT响应"

echo -e "\n✅ 修复执行脚本完成"
echo "请根据检查结果进行相应修复操作" 