#!/bin/bash

echo "🔧 测试OTA服务器响应"
echo "===================="

# 生成测试数据
TEST_MAC="02:$(openssl rand -hex 5 | sed 's/\(..\)/\1:/g;s/:$//')"
TEST_UUID=$(uuidgen)

echo "📱 测试设备: $TEST_MAC"
echo "🔑 测试UUID: $TEST_UUID"
echo ""

# 测试1: 基础连通性
echo "📡 测试1: 基础连通性"
echo "-------------------"
curl -s -w "状态码: %{http_code}\n" -X GET http://47.122.144.73:8002/
echo ""

# 测试2: OTA端点可达性
echo "📡 测试2: OTA端点可达性"
echo "-------------------"
curl -s -w "状态码: %{http_code}\n" -X GET http://47.122.144.73:8002/xiaozhi/ota/
echo ""

# 测试3: 发送标准OTA请求
echo "📡 测试3: 发送标准OTA请求"
echo "-------------------"

REQUEST_DATA="{
  \"application\": {
    \"version\": \"1.0.0\",
    \"name\": \"xiaozhi-android\",
    \"compile_time\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  },
  \"macAddress\": \"$TEST_MAC\",
  \"chipModelName\": \"android\",
  \"board\": {
    \"type\": \"android\",
    \"manufacturer\": \"TestManufacturer\",
    \"model\": \"TestModel\"
  },
  \"uuid\": \"$TEST_UUID\",
  \"build_time\": $(date +%s)
}"

echo "发送请求:"
echo "$REQUEST_DATA" | jq . 2>/dev/null || echo "$REQUEST_DATA"
echo ""
echo "服务器响应:"

RESPONSE=$(curl -s -w "\n状态码:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: $TEST_MAC" \
  -H "Client-Id: android-test-$(date +%s)" \
  -d "$REQUEST_DATA" \
  http://47.122.144.73:8002/xiaozhi/ota/)

echo "$RESPONSE"
echo ""

# 测试4: 检查响应内容
echo "📡 测试4: 分析响应内容"
echo "-------------------"

RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)
STATUS_CODE=$(echo "$RESPONSE" | tail -1 | sed 's/状态码://')

echo "状态码: $STATUS_CODE"
echo "响应体: $RESPONSE_BODY"

if [ "$STATUS_CODE" = "200" ]; then
    if echo "$RESPONSE_BODY" | grep -q "activation"; then
        echo "✅ 响应包含激活字段"
        ACTIVATION_CODE=$(echo "$RESPONSE_BODY" | grep -o '"code":"[^"]*"' | cut -d'"' -f4 || echo "解析失败")
        echo "激活码: $ACTIVATION_CODE"
    elif echo "$RESPONSE_BODY" | grep -q "websocket"; then
        echo "✅ 响应包含WebSocket字段"
        WS_URL=$(echo "$RESPONSE_BODY" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "解析失败")
        echo "WebSocket URL: $WS_URL"
    else
        echo "❓ 响应格式不符合预期"
        echo "可能的错误信息:"
        echo "$RESPONSE_BODY" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 || echo "无错误信息"
    fi
else
    echo "❌ HTTP状态码错误: $STATUS_CODE"
fi

echo ""
echo "🏁 测试完成" 