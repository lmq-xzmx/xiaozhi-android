#!/bin/bash
# STT问题修复脚本
echo "🚀 开始STT问题修复..."

# 1. 检查当前状态
echo "1️⃣ 检查当前状态..."
echo "检查服务器进程:"
ps aux | grep xiaozhi-server

echo "检查端口监听:"
lsof -i :8080

# 2. 检查模型文件
echo "2️⃣ 检查模型文件..."
echo "VAD模型:"
ls -la ../main/xiaozhi-server/models/snakers4_silero-vad/ 2>/dev/null || echo "VAD模型不存在"

echo "ASR模型:"
ls -la ../main/xiaozhi-server/models/SenseVoiceSmall/ 2>/dev/null || echo "ASR模型不存在"

# 3. 检查配置文件
echo "3️⃣ 检查配置文件..."
if [ -f "../main/xiaozhi-server/config.yaml" ]; then
    echo "config.yaml存在"
    grep -A 5 "selected_module:" ../main/xiaozhi-server/config.yaml
else
    echo "config.yaml不存在"
fi

# 4. 启动服务器(如果未运行)
echo "4️⃣ 检查服务器状态..."
if ! pgrep -f "xiaozhi-server" > /dev/null; then
    echo "服务器未运行，请手动启动:"
    echo "cd ../main/xiaozhi-server && python app.py"
else
    echo "✅ 服务器正在运行"
fi

# 5. 查看实时日志
echo "5️⃣ 查看服务器日志（最后20行）:"
if [ -f "../main/xiaozhi-server/app.log" ]; then
    tail -20 ../main/xiaozhi-server/app.log
else
    echo "日志文件不存在"
fi

echo "✅ 修复脚本执行完成"
echo "请根据检查结果进行相应修复"
