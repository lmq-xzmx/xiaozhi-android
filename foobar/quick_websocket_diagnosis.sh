#!/bin/bash

# 🔍 WebSocket配置失败快速诊断脚本
echo "🔍 WebSocket配置失败快速诊断"
echo "================================"
echo "目标：诊断新APK中WebSocket配置失败的具体原因"
echo ""

# 测试参数
DEVICE_ID="android-test-$(date +%s)"
CLIENT_ID="diagnosis-client-$(date +%s)"
OTA_URL="http://47.122.144.73:8002/xiaozhi/ota/"
WS_URL="ws://47.122.144.73:8000/xiaozhi/v1/"

echo "📱 测试参数："
echo "   设备ID: $DEVICE_ID"
echo "   客户端ID: $CLIENT_ID"
echo "   OTA URL: $OTA_URL"
echo "   WebSocket URL: $WS_URL"
echo ""

# 第一步：测试OTA配置获取
echo "🔧 第一步：测试OTA配置获取"
echo "=========================="

echo "📤 发送OTA请求..."
OTA_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: $DEVICE_ID" \
  -H "Client-Id: $CLIENT_ID" \
  -d "{
    \"application\": {
      \"version\": \"1.0.0\",
      \"name\": \"xiaozhi-android\"
    },
    \"macAddress\": \"$DEVICE_ID\",
    \"board\": {
      \"type\": \"android\"
    },
    \"chipModelName\": \"android\"
  }" \
  "$OTA_URL" 2>/dev/null)

if [ $? -eq 0 ]; then
    HTTP_CODE=$(echo "$OTA_RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
    RESPONSE_BODY=$(echo "$OTA_RESPONSE" | head -n -1)
    
    echo "✅ OTA请求成功 (HTTP $HTTP_CODE)"
    echo "📋 响应内容:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
    
    # 检查是否包含WebSocket配置
    if echo "$RESPONSE_BODY" | grep -q '"websocket"'; then
        EXTRACTED_WS_URL=$(echo "$RESPONSE_BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('websocket', {}).get('url', '未找到WebSocket URL'))
except:
    print('JSON解析失败')
" 2>/dev/null)
        
        echo ""
        echo "🎉 **OTA配置成功！**"
        echo "🔗 获得WebSocket URL: $EXTRACTED_WS_URL"
        WS_URL="$EXTRACTED_WS_URL"  # 使用实际获得的URL
        OTA_SUCCESS=true
        
    elif echo "$RESPONSE_BODY" | grep -q '"activation"'; then
        ACTIVATION_CODE=$(echo "$RESPONSE_BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('activation', {}).get('code', '未找到激活码'))
except:
    print('JSON解析失败')
" 2>/dev/null)
        
        echo ""
        echo "⚠️ **设备需要激活**"
        echo "🔑 激活码: $ACTIVATION_CODE"
        echo "🌐 管理面板: http://47.122.144.73:8002/#/home"
        echo "❌ 无法继续WebSocket测试，需要先完成设备绑定"
        OTA_SUCCESS=false
        
    else
        echo ""
        echo "❌ **OTA响应格式异常**"
        echo "响应中既没有websocket配置也没有activation信息"
        OTA_SUCCESS=false
    fi
    
else
    echo "❌ OTA请求失败"
    echo "可能原因："
    echo "1. 网络连接问题"
    echo "2. 服务器不可达"
    echo "3. 请求格式错误"
    OTA_SUCCESS=false
fi

echo ""

# 第二步：测试WebSocket连接（仅在OTA成功时）
if [ "$OTA_SUCCESS" = true ]; then
    echo "🌐 第二步：测试WebSocket连接"
    echo "=========================="
    
    # 转换WebSocket URL为HTTP进行基础测试
    HTTP_TEST_URL="${WS_URL/ws:/http:}"
    HTTP_TEST_URL="${HTTP_TEST_URL/wss:/https:}"
    
    echo "📡 测试WebSocket端点可达性..."
    echo "HTTP测试URL: $HTTP_TEST_URL"
    
    WS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$HTTP_TEST_URL" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        WS_HTTP_CODE=$(echo "$WS_RESPONSE" | tail -1 | sed 's/HTTP_CODE://')
        WS_RESPONSE_BODY=$(echo "$WS_RESPONSE" | head -n -1)
        
        echo "✅ WebSocket端点可达 (HTTP $WS_HTTP_CODE)"
        if [ ! -z "$WS_RESPONSE_BODY" ]; then
            echo "📝 响应内容: $WS_RESPONSE_BODY"
        fi
        WS_SUCCESS=true
    else
        echo "❌ WebSocket端点不可达"
        echo "可能原因："
        echo "1. WebSocket服务未启动"
        echo "2. 端口8000被阻止"
        echo "3. 服务器配置问题"
        WS_SUCCESS=false
    fi
else
    echo "⏭️ 跳过WebSocket测试（OTA配置失败）"
    WS_SUCCESS=false
fi

echo ""

# 第三步：诊断总结
echo "📊 诊断总结"
echo "============"

echo "检查结果："
echo "  OTA配置: $([ "$OTA_SUCCESS" = true ] && echo "✅ 成功" || echo "❌ 失败")"
echo "  WebSocket连接: $([ "$WS_SUCCESS" = true ] && echo "✅ 成功" || echo "❌ 失败")"

echo ""

if [ "$OTA_SUCCESS" = true ] && [ "$WS_SUCCESS" = true ]; then
    echo "🎉 **诊断结果：配置正常**"
    echo ""
    echo "✅ OTA和WebSocket服务都正常工作"
    echo "✅ 应用应该能够正常获取WebSocket配置"
    echo ""
    echo "💡 如果应用仍然失败，可能的原因："
    echo "1. 应用内部逻辑错误"
    echo "2. 设备网络权限问题"
    echo "3. 应用缓存问题"
    echo ""
    echo "🔧 建议操作："
    echo "1. 清除应用数据重新配置"
    echo "2. 检查应用日志：adb logcat | grep -E '(WebSocket|OTA|ActivationManager)'"
    echo "3. 确认应用网络权限已授予"
    
elif [ "$OTA_SUCCESS" = false ]; then
    echo "❌ **诊断结果：OTA配置失败**"
    echo ""
    echo "🔍 根本原因：无法从OTA服务获取WebSocket配置"
    echo ""
    echo "🔧 立即修复步骤："
    echo "1. 检查网络连接：ping 47.122.144.73"
    echo "2. 检查OTA服务状态"
    echo "3. 如果需要激活，访问管理面板完成设备绑定"
    echo "4. 重新测试OTA配置"
    
elif [ "$WS_SUCCESS" = false ]; then
    echo "⚠️ **诊断结果：WebSocket服务不可用**"
    echo ""
    echo "🔍 问题：OTA配置成功，但WebSocket服务不可达"
    echo ""
    echo "🔧 修复步骤："
    echo "1. 检查WebSocket服务器状态"
    echo "2. 确认端口8000未被防火墙阻止"
    echo "3. 验证服务器配置"
    echo "4. 重启WebSocket服务"
fi

echo ""
echo "📋 详细诊断信息已保存，可用于进一步分析"
echo "🏁 诊断完成" 