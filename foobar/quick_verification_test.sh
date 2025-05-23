#!/bin/bash

echo "🔍 快速验证服务器接口和设备绑定状态"
echo "==============================================="

SERVER_IP="47.122.144.73"
OTA_PORT="8002"
WS_PORT="8000"

echo "📡 1. 检查OTA接口是否可访问..."
echo "URL: http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/"

OTA_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/" 2>/dev/null)
if [ $? -eq 0 ]; then
    HTTP_CODE=$(echo "$OTA_RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
    CONTENT=$(echo "$OTA_RESPONSE" | head -n -1)
    
    echo "✅ OTA接口响应成功 (HTTP $HTTP_CODE)"
    echo "📝 响应内容: $CONTENT"
    
    # 从响应中提取WebSocket URL
    if echo "$CONTENT" | grep -q "websocket地址"; then
        WS_URL=$(echo "$CONTENT" | grep -o 'ws://[^,]*' | head -1)
        echo "🔗 实际WebSocket地址: $WS_URL"
    fi
else
    echo "❌ OTA接口无法访问"
fi

echo ""
echo "🌐 2. 检查可能的管理面板端口..."

# 常见的Web管理面板端口
WEB_PORTS=(8080 8081 3000 9000 8090 8888)

for port in "${WEB_PORTS[@]}"; do
    echo -n "检查端口 $port... "
    if timeout 3 bash -c "</dev/tcp/$SERVER_IP/$port" 2>/dev/null; then
        echo "✅ 端口 $port 开放"
        
        # 尝试获取Web页面
        WEB_RESPONSE=$(curl -s -m 3 "http://$SERVER_IP:$port" 2>/dev/null)
        if echo "$WEB_RESPONSE" | grep -qi -E "(xiaozhi|管理|面板|device|设备)"; then
            echo "   🎯 可能是管理面板: http://$SERVER_IP:$port"
        fi
    else
        echo "❌ 端口 $port 关闭"
    fi
done

echo ""
echo "📱 3. 检查WebSocket服务器状态..."
echo "URL: ws://$SERVER_IP:$WS_PORT/xiaozhi/v1/"

# 使用curl检查WebSocket端点（HTTP方式）
WS_CHECK=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://$SERVER_IP:$WS_PORT/xiaozhi/v1/" 2>/dev/null)
if [ $? -eq 0 ]; then
    WS_HTTP_CODE=$(echo "$WS_CHECK" | tail -1 | sed 's/HTTP_CODE://')
    WS_CONTENT=$(echo "$WS_CHECK" | head -n -1)
    
    echo "✅ WebSocket端点响应 (HTTP $WS_HTTP_CODE)"
    echo "📝 响应内容: $WS_CONTENT"
else
    echo "❌ WebSocket端点无法访问"
fi

echo ""
echo "📋 4. 生成设备信息用于绑定..."
DEVICE_MAC=$(uuidgen | tr '[:upper:]' '[:lower:]' | sed 's/-//g' | cut -c1-12 | sed 's/\(..\)/\1:/g' | sed 's/:$//')
CLIENT_UUID=$(uuidgen)

echo "设备MAC地址: $DEVICE_MAC"
echo "客户端UUID: $CLIENT_UUID"

echo ""
echo "🚀 5. 测试OTA配置获取..."

# 创建测试请求数据
TEST_REQUEST='{
    "application": {
        "version": "1.0.0",
        "name": "xiaozhi-android"
    },
    "device": {
        "mac": "'$DEVICE_MAC'",
        "uuid": "'$CLIENT_UUID'"
    }
}'

echo "📤 发送OTA请求..."
echo "Request: $TEST_REQUEST"

OTA_CONFIG=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "device-id: $DEVICE_MAC" \
    -H "client-id: $CLIENT_UUID" \
    -d "$TEST_REQUEST" \
    "http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ OTA配置获取成功"
    echo "📋 配置响应: $OTA_CONFIG"
    
    # 解析WebSocket URL
    if echo "$OTA_CONFIG" | grep -q '"url"'; then
        ACTUAL_WS_URL=$(echo "$OTA_CONFIG" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
        echo "🔗 服务器返回的WebSocket URL: $ACTUAL_WS_URL"
    fi
else
    echo "❌ OTA配置获取失败"
fi

echo ""
echo "📊 验证总结:"
echo "1. 请检查上面的输出，确认OTA和WebSocket服务是否正常"
echo "2. 如果找到管理面板，请访问并尝试添加设备"
echo "3. 使用上面生成的设备信息进行绑定测试"
echo "4. 如果服务器返回了不同的WebSocket URL，请更新Android应用配置" 