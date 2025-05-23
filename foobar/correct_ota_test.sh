#!/bin/bash

# 🎯 正确的OTA测试脚本
# 基于DeviceServiceImpl.java源码分析的准确格式

echo "=== 小智设备绑定OTA测试 ==="
echo "目标：获取激活码用于管理面板绑定"
echo

# 测试参数
DEVICE_ID="aa:bb:cc:dd:ee:ff"
CLIENT_ID="android-test-$(date +%s)"
OTA_URL="http://47.122.144.73:8002/xiaozhi/ota/"

echo "设备ID: $DEVICE_ID"
echo "客户端ID: $CLIENT_ID"
echo "OTA地址: $OTA_URL"
echo

# 正确的OTA请求（基于DeviceServiceImpl.java的checkDeviceActive方法）
echo "发送OTA请求..."
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: $DEVICE_ID" \
  -H "Client-Id: $CLIENT_ID" \
  -d '{
    "macAddress": "'$DEVICE_ID'",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    },
    "chipModelName": "android"
  }' \
  "$OTA_URL")

echo "服务器响应："
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo

# 解析响应
if echo "$RESPONSE" | grep -q '"activation"'; then
    echo "✅ 成功！设备需要激活"
    
    # 提取激活码
    ACTIVATION_CODE=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('activation', {}).get('code', '未找到激活码'))
except:
    print('解析失败')
" 2>/dev/null)
    
    echo "🔑 激活码: $ACTIVATION_CODE"
    echo
    echo "📋 下一步操作："
    echo "1. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30"
    echo "2. 在设备绑定界面输入激活码: $ACTIVATION_CODE"
    echo "3. 完成绑定后重新测试Android应用的STT功能"
    
elif echo "$RESPONSE" | grep -q '"websocket"' && ! echo "$RESPONSE" | grep -q '"activation"'; then
    echo "ℹ️  设备已绑定，直接返回WebSocket配置"
    
    WEBSOCKET_URL=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('websocket', {}).get('url', '未找到WebSocket URL'))
except:
    print('解析失败')
" 2>/dev/null)
    
    echo "🔗 WebSocket地址: $WEBSOCKET_URL"
    echo "✅ 此设备已完成绑定，STT功能应该正常工作"
    
elif echo "$RESPONSE" | grep -q '"error"'; then
    echo "❌ OTA请求失败"
    echo "错误信息: $RESPONSE"
    echo
    echo "🔧 可能的原因："
    echo "1. 请求格式不正确"
    echo "2. 服务器端OTA接口有问题"
    echo "3. 网络连接问题"
    
else
    echo "⚠️  意外的响应格式"
    echo "原始响应: $RESPONSE"
    echo
    echo "🔧 调试建议："
    echo "1. 检查服务器OTA服务是否正常运行"
    echo "2. 验证请求格式是否正确"
    echo "3. 查看服务器日志获取更多信息"
fi

echo
echo "=== 测试完成 ===" 