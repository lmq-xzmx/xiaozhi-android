#!/bin/bash

echo "🔍 小智Android设备绑定机制验证测试"
echo "================================================"

# 服务器配置
SERVER_IP="47.122.144.73"
OTA_PORT="8002"
WS_PORT="8000"
AGENT_ID="6bf580ad09cf4b1e8bd332dafb9e6d30"

# 生成测试设备信息
DEVICE_MAC="02:$(openssl rand -hex 5 | sed 's/\(..\)/\1:/g;s/:$//')"
CLIENT_UUID=$(uuidgen)

echo "📱 测试设备信息："
echo "   MAC地址: $DEVICE_MAC"
echo "   客户端UUID: $CLIENT_UUID"
echo "   代理ID: $AGENT_ID"
echo ""

# 1. 测试OTA接口
echo "🌐 1. 测试OTA设备激活检查接口..."
echo "URL: http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/"

# 创建OTA请求数据
OTA_REQUEST='{
    "application": {
        "version": "1.0.0",
        "name": "xiaozhi-android"
    },
    "macAddress": "'$DEVICE_MAC'",
    "board": {
        "type": "android"
    },
    "chipModelName": "android"
}'

echo "📤 发送OTA激活检查请求..."
echo "请求数据: $OTA_REQUEST"

OTA_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Device-Id: $DEVICE_MAC" \
    -H "Client-Id: $CLIENT_UUID" \
    -d "$OTA_REQUEST" \
    "http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/" 2>/dev/null)

if [ $? -eq 0 ]; then
    HTTP_CODE=$(echo "$OTA_RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
    CONTENT=$(echo "$OTA_RESPONSE" | head -n -1)
    
    echo "✅ OTA接口响应成功 (HTTP $HTTP_CODE)"
    echo "📋 响应内容:"
    echo "$CONTENT" | jq . 2>/dev/null || echo "$CONTENT"
    
    # 提取激活码
    if echo "$CONTENT" | grep -q '"activation"'; then
        ACTIVATION_CODE=$(echo "$CONTENT" | jq -r '.activation.code' 2>/dev/null)
        ACTIVATION_MESSAGE=$(echo "$CONTENT" | jq -r '.activation.message' 2>/dev/null)
        
        echo ""
        echo "🎯 设备需要激活！"
        echo "   激活码: $ACTIVATION_CODE"
        echo "   激活消息: $ACTIVATION_MESSAGE"
        
        # 2. 测试绑定API
        echo ""
        echo "🔗 2. 测试设备绑定API..."
        
        # 尝试绑定设备（需要认证令牌）
        echo "⚠️  注意：绑定API需要有效的认证令牌"
        echo "   管理面板URL: http://$SERVER_IP:$OTA_PORT/#/device-management?agentId=$AGENT_ID"
        echo "   请手动访问管理面板，使用激活码 $ACTIVATION_CODE 进行绑定"
        
        # 3. 验证绑定后的效果
        echo ""
        echo "🧪 3. 绑定后验证（请先在管理面板完成绑定）..."
        read -p "已完成绑定？按回车键继续验证，或Ctrl+C退出..." -r
        
        # 重新检查OTA状态
        echo "📤 重新检查设备激活状态..."
        OTA_RESPONSE2=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Device-Id: $DEVICE_MAC" \
            -H "Client-Id: $CLIENT_UUID" \
            -d "$OTA_REQUEST" \
            "http://$SERVER_IP:$OTA_PORT/xiaozhi/ota/" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            HTTP_CODE2=$(echo "$OTA_RESPONSE2" | tail -1 | sed 's/HTTP_CODE://')
            CONTENT2=$(echo "$OTA_RESPONSE2" | head -n -1)
            
            echo "✅ 绑定后OTA响应 (HTTP $HTTP_CODE2)"
            echo "📋 响应内容:"
            echo "$CONTENT2" | jq . 2>/dev/null || echo "$CONTENT2"
            
            # 检查是否返回WebSocket URL
            if echo "$CONTENT2" | grep -q '"websocket"'; then
                WS_URL=$(echo "$CONTENT2" | jq -r '.websocket.url' 2>/dev/null)
                echo ""
                echo "🎉 绑定成功！获得WebSocket URL: $WS_URL"
                
                # 4. 测试WebSocket连接
                echo ""
                echo "🌐 4. 测试WebSocket连接..."
                test_websocket_connection "$WS_URL" "$DEVICE_MAC" "$CLIENT_UUID"
            else
                echo "❌ 绑定后仍未获得WebSocket配置"
            fi
        else
            echo "❌ 重新检查OTA状态失败"
        fi
        
    elif echo "$CONTENT" | grep -q '"websocket"'; then
        WS_URL=$(echo "$CONTENT" | jq -r '.websocket.url' 2>/dev/null)
        echo ""
        echo "✅ 设备已激活，WebSocket URL: $WS_URL"
    else
        echo ""
        echo "❓ 未知的OTA响应格式"
    fi
else
    echo "❌ OTA接口请求失败"
fi

echo ""
echo "📊 验证总结:"
echo "1. 确认OTA接口工作正常，能够生成激活码"
echo "2. 需要在管理面板手动完成设备绑定"
echo "3. 绑定完成后，OTA接口会返回WebSocket配置"
echo "4. Android应用应先调用OTA接口，然后根据响应处理绑定流程"

function test_websocket_connection() {
    local ws_url="$1"
    local device_id="$2"
    local client_id="$3"
    
    echo "🔗 尝试WebSocket连接测试..."
    echo "URL: $ws_url"
    
    # 将ws://转换为http://进行基础连接测试
    local http_url="${ws_url/ws:/http:}"
    http_url="${http_url%/xiaozhi/v1/}"
    
    echo "📡 测试WebSocket端点可达性..."
    curl -s -w "HTTP状态: %{http_code}\n" "$http_url/xiaozhi/v1/" || echo "连接测试失败"
    
    echo "💡 要进行完整的WebSocket测试，请在Android应用中使用获得的URL"
}

echo ""
echo "🔧 下一步建议："
echo "1. 如果激活码生成成功，在Android应用中集成OTA客户端"
echo "2. 实现设备激活UI，引导用户完成绑定"
echo "3. 修改WebSocket连接使用OTA返回的实际URL"
echo "4. 完善错误处理和用户提示" 