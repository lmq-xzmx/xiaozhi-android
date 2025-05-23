#!/bin/bash

echo "🧪 快速OTA接口测试"
echo "==================="

# 生成测试设备MAC
DEVICE_MAC="02:42:ac:11:00:02"
CLIENT_UUID="android-test-device"

echo "📱 测试设备信息："
echo "   MAC地址: $DEVICE_MAC"
echo "   客户端ID: $CLIENT_UUID"
echo ""

echo "🌐 测试OTA接口..."
echo "URL: http://47.122.144.73:8002/xiaozhi/ota/"

# 简单测试
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: $DEVICE_MAC" \
  -H "Client-Id: $CLIENT_UUID" \
  -d "{
    \"application\": {
      \"version\": \"1.0.0\",
      \"name\": \"xiaozhi-android\"
    },
    \"macAddress\": \"$DEVICE_MAC\",
    \"board\": {
      \"type\": \"android\"
    },
    \"chipModelName\": \"android\"
  }" \
  "http://47.122.144.73:8002/xiaozhi/ota/" 2>/dev/null

echo ""
echo ""
echo "📋 如果上面返回了包含'activation'的JSON响应："
echo "1. 记下激活码（通常是6位数字）"
echo "2. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30"
echo "3. 登录后点击'新增'按钮"
echo "4. 输入激活码完成绑定"
echo ""
echo "📋 如果上面返回了包含'websocket'的JSON响应："
echo "   设备已经绑定，可以直接使用WebSocket URL" 