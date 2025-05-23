#!/bin/bash

echo "=== 修正ADB多设备问题 ==="
echo ""

# 1. 检查adb是否可用
if ! command -v adb &> /dev/null; then
    echo "❌ ADB未找到，请确保Android SDK已安装"
    exit 1
fi

# 2. 列出连接的设备
echo "📱 连接的Android设备/模拟器："
adb devices -l

echo ""
echo "=== 选择设备并清除应用数据 ==="

# 3. 获取设备列表
devices=$(adb devices | grep -v "List of devices" | grep "device$" | cut -f1)
device_count=$(echo "$devices" | wc -l | tr -d ' ')

if [ "$device_count" -eq 0 ]; then
    echo "❌ 没有找到连接的Android设备"
    exit 1
elif [ "$device_count" -eq 1 ]; then
    # 只有一个设备，直接使用
    device_id=$(echo "$devices" | head -n1)
    echo "✅ 自动选择设备: $device_id"
    
    echo "🧹 清除VoiceBot应用数据..."
    adb -s "$device_id" shell pm clear info.dourok.voicebot
    
    if [ $? -eq 0 ]; then
        echo "✅ 应用数据清除成功！"
        echo ""
        echo "📋 下一步操作："
        echo "1. 重新编译Android项目"
        echo "2. 安装到设备"
        echo "3. 启动应用测试STT功能"
        echo "4. 检查日志中的设备ID应为: 00:11:22:33:44:55"
    else
        echo "❌ 清除应用数据失败"
        exit 1
    fi
    
else
    # 多个设备，让用户选择
    echo "发现多个设备，请选择："
    i=1
    while IFS= read -r device; do
        echo "$i) $device"
        i=$((i+1))
    done <<< "$devices"
    
    echo ""
    read -p "请输入设备编号 (1-$device_count): " selection
    
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "$device_count" ]; then
        device_id=$(echo "$devices" | sed -n "${selection}p")
        echo "✅ 选择的设备: $device_id"
        
        echo "🧹 清除VoiceBot应用数据..."
        adb -s "$device_id" shell pm clear info.dourok.voicebot
        
        if [ $? -eq 0 ]; then
            echo "✅ 应用数据清除成功！"
            echo ""
            echo "📋 下一步操作："
            echo "1. 重新编译Android项目"
            echo "2. 安装到设备"
            echo "3. 启动应用测试STT功能"
            echo "4. 检查日志中的设备ID应为: 00:11:22:33:44:55"
        else
            echo "❌ 清除应用数据失败"
            exit 1
        fi
    else
        echo "❌ 无效的选择"
        exit 1
    fi
fi

echo ""
echo "🔍 验证设备绑定状态（可选）："
echo "运行: python3 test_your_device_id.py" 