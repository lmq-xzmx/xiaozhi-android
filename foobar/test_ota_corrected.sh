#!/bin/bash

echo "🧪 修正的OTA接口测试"
echo "==================="

# 使用符合MAC地址格式的设备ID
DEVICE_MAC="aa:bb:cc:dd:ee:ff"
CLIENT_UUID="android-test-uuid"

echo "📱 测试设备信息："
echo "   MAC地址: $DEVICE_MAC"
echo "   客户端ID: $CLIENT_UUID"
echo ""

echo "🌐 测试OTA接口..."

# 修正的请求格式 - 根据DeviceServiceImpl的要求
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: $DEVICE_MAC" \
  -H "Client-Id: $CLIENT_UUID" \
  -d "{
    \"macAddress\": \"$DEVICE_MAC\",
    \"application\": {
      \"version\": \"1.0.0\"
    },
    \"board\": {
      \"type\": \"android\"
    },
    \"chipModelName\": \"android\"
  }" \
  "http://47.122.144.73:8002/xiaozhi/ota/")

# 解析响应
HTTP_CODE=$(echo "$RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
CONTENT=$(echo "$RESPONSE" | head -n -1)

echo "HTTP状态码: $HTTP_CODE"
echo "响应内容: $CONTENT"
echo ""

# 解析响应内容
if echo "$CONTENT" | grep -q '"activation"'; then
    echo "🎯 成功！设备需要激活"
    
    # 尝试提取激活码
    if command -v jq > /dev/null; then
        ACTIVATION_CODE=$(echo "$CONTENT" | jq -r '.activation.code' 2>/dev/null)
        echo "📱 激活码: $ACTIVATION_CODE"
    else
        echo "📱 请从上面的JSON中找到activation.code字段的值"
    fi
    
    echo ""
    echo "📋 下一步操作："
    echo "1. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30"
    echo "2. 登录管理员账号"
    echo "3. 点击'新增'按钮"
    echo "4. 输入激活码: $ACTIVATION_CODE"
    echo "5. 完成绑定后，重新测试Android应用的STT功能"
    
elif echo "$CONTENT" | grep -q '"websocket"'; then
    echo "✅ 设备已绑定！"
    WS_URL=$(echo "$CONTENT" | jq -r '.websocket.url' 2>/dev/null || echo "请从JSON中提取websocket.url")
    echo "🌐 WebSocket URL: $WS_URL"
    echo ""
    echo "📋 设备已绑定，可以直接使用STT功能"
    
elif echo "$CONTENT" | grep -q '"error"'; then
    echo "❌ 请求格式错误"
    echo "📋 尝试其他设备ID格式..."
    
    # 尝试其他格式
    DEVICE_MAC2="02-42-ac-11-00-02"
    echo ""
    echo "🔄 尝试使用连字符格式: $DEVICE_MAC2"
    
    RESPONSE2=$(curl -s \
      -X POST \
      -H "Content-Type: application/json" \
      -H "Device-Id: $DEVICE_MAC2" \
      -H "Client-Id: $CLIENT_UUID" \
      -d "{
        \"macAddress\": \"$DEVICE_MAC2\",
        \"application\": {
          \"version\": \"1.0.0\"
        },
        \"board\": {
          \"type\": \"android\"
        }
      }" \
      "http://47.122.144.73:8002/xiaozhi/ota/")
    
    echo "第二次尝试响应: $RESPONSE2"
    
else
    echo "❓ 未知响应格式"
fi

echo ""
echo "💡 如果仍然失败，可能需要："
echo "1. 检查MAC地址格式要求"
echo "2. 确认Device-Id和macAddress字段的一致性要求"
echo "3. 联系服务器管理员确认设备注册流程" 