#!/bin/bash

echo "🔧 测试修复后的OTA绑定配置"
echo "=" 
echo "验证OTA端点和请求格式是否正确"
echo ""

# 生成测试设备信息
DEVICE_MAC="02:$(openssl rand -hex 5 | sed 's/\(..\)/\1:/g;s/:$//')"
CLIENT_ID="android-app-$(date +%s)"
UUID=$(uuidgen)

echo "📱 测试设备信息:"
echo "   设备ID: $DEVICE_MAC"
echo "   客户端ID: $CLIENT_ID"
echo "   UUID: $UUID"
echo ""

# 服务器配置（修复后的正确配置）
OTA_BASE_URL="http://47.122.144.73:8002"
OTA_ENDPOINT="/xiaozhi/ota/"  # 修复后的正确端点
OTA_FULL_URL="${OTA_BASE_URL}${OTA_ENDPOINT}"

echo "🌐 服务器配置:"
echo "   OTA URL: $OTA_FULL_URL"
echo ""

# 构建标准化的OTA请求（与Android代码一致）
REQUEST_PAYLOAD='{
    "application": {
        "version": "1.0.0",
        "name": "xiaozhi-android",
        "compile_time": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    },
    "macAddress": "'$DEVICE_MAC'",
    "chipModelName": "android",
    "board": {
        "type": "android",
        "manufacturer": "TestManufacturer",
        "model": "TestModel"
    },
    "uuid": "'$UUID'",
    "build_time": '$(date +%s)'
}'

echo "📤 发送OTA绑定检查请求:"
echo "请求体: $REQUEST_PAYLOAD"
echo ""

echo "🔄 正在发送请求..."

# 发送请求并获取响应
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Device-Id: $DEVICE_MAC" \
    -H "Client-Id: $CLIENT_ID" \
    -H "X-Language: Chinese" \
    -d "$REQUEST_PAYLOAD" \
    "$OTA_FULL_URL" 2>/dev/null)

if [ $? -eq 0 ]; then
    HTTP_CODE=$(echo "$RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
    RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)
    
    echo "📥 服务器响应:"
    echo "   状态码: $HTTP_CODE"
    echo "   响应内容: $RESPONSE_BODY"
    echo ""
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "🔍 响应分析:"
        
        # 检查是否包含activation字段
        if echo "$RESPONSE_BODY" | grep -q '"activation"'; then
            ACTIVATION_CODE=$(echo "$RESPONSE_BODY" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
            echo "✅ 服务器返回激活码，需要绑定设备"
            echo "   激活码: $ACTIVATION_CODE"
            echo ""
            echo "📱 下一步操作:"
            echo "1. 访问管理面板: http://47.122.144.73:8002"
            echo "2. 使用激活码 $ACTIVATION_CODE 进行设备绑定"
            echo "3. 绑定成功后，设备将收到WebSocket连接信息"
            BINDING_TEST_RESULT="success_needs_binding"
            
        # 检查是否包含websocket字段
        elif echo "$RESPONSE_BODY" | grep -q '"websocket"'; then
            WS_URL=$(echo "$RESPONSE_BODY" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
            echo "✅ 设备已绑定成功"
            echo "   WebSocket URL: $WS_URL"
            echo "   可以直接使用语音功能"
            BINDING_TEST_RESULT="success_already_bound"
        else
            echo "❓ 未知响应格式，缺少activation或websocket字段"
            echo "   原始响应: $RESPONSE_BODY"
            BINDING_TEST_RESULT="unknown_format"
        fi
    else
        echo "❌ HTTP请求失败 (状态码: $HTTP_CODE)"
        echo "   错误内容: $RESPONSE_BODY"
        BINDING_TEST_RESULT="http_error"
    fi
else
    echo "❌ 网络请求失败"
    BINDING_TEST_RESULT="network_error"
fi

echo ""
echo "🔗 测试WebSocket URL可达性"
echo "=" 

WS_BASE_URL="ws://47.122.144.73:8000/xiaozhi/v1/"
HTTP_TEST_URL="http://47.122.144.73:8000/xiaozhi/v1/"

echo "WebSocket URL: $WS_BASE_URL"
echo "HTTP测试URL: $HTTP_TEST_URL"

# 测试WebSocket端点的HTTP可达性
WS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$HTTP_TEST_URL" 2>/dev/null)

if [ $? -eq 0 ]; then
    WS_HTTP_CODE=$(echo "$WS_RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
    WS_RESPONSE_BODY=$(echo "$WS_RESPONSE" | head -n -1)
    
    echo "✅ WebSocket端点可达 (HTTP $WS_HTTP_CODE)"
    if [ ! -z "$WS_RESPONSE_BODY" ]; then
        echo "   响应: $WS_RESPONSE_BODY"
    fi
    WS_TEST_RESULT="success"
else
    echo "❌ WebSocket端点不可达"
    WS_TEST_RESULT="failed"
fi

echo ""
echo "📊 测试结果总结"
echo "=" 

case $BINDING_TEST_RESULT in
    "success_needs_binding")
        echo "OTA绑定测试: ✅ 通过 (需要绑定)"
        ;;
    "success_already_bound")
        echo "OTA绑定测试: ✅ 通过 (已绑定)"
        ;;
    *)
        echo "OTA绑定测试: ❌ 失败"
        ;;
esac

case $WS_TEST_RESULT in
    "success")
        echo "WebSocket测试: ✅ 通过"
        ;;
    *)
        echo "WebSocket测试: ❌ 失败"
        ;;
esac

echo ""

if [[ "$BINDING_TEST_RESULT" =~ ^success ]] && [ "$WS_TEST_RESULT" = "success" ]; then
    echo "🎉 绑定配置修复成功！"
    echo "应用现在应该能够:"
    echo "1. 正确连接OTA服务进行设备检查"
    echo "2. 获取激活码或WebSocket连接信息"
    echo "3. 成功建立语音通信连接"
else
    echo "⚠️ 仍存在问题，需要进一步检查:"
    if [[ ! "$BINDING_TEST_RESULT" =~ ^success ]]; then
        echo "- OTA端点或请求格式可能仍有问题"
    fi
    if [ "$WS_TEST_RESULT" != "success" ]; then
        echo "- WebSocket服务可能不可用"
    fi
fi

echo ""
echo "🔧 如果需要调试，可以查看:"
echo "1. 设备生成的MAC地址: $DEVICE_MAC"
echo "2. OTA请求格式: 使用了修复后的 /xiaozhi/ota/ 端点"
echo "3. 请求字段: 使用驼峰命名 macAddress, chipModelName"
echo "4. 应用信息: 包含了完整的 application 对象"
echo ""
echo "🏁 测试完成" 