#!/usr/bin/env python3
"""
小智设备绑定OTA测试脚本（使用mac_address字段）
基于DeviceReportReqDTO.java的JsonProperty注解
"""

import requests
import json
import time

def test_ota_request():
    print("=== 小智设备绑定OTA测试（mac_address字段）===")
    print("目标：获取激活码用于管理面板绑定")
    print()
    
    # 测试参数
    device_id = "aa:bb:cc:dd:ee:ff"
    client_id = f"android-test-{int(time.time())}"
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    print(f"设备ID: {device_id}")
    print(f"客户端ID: {client_id}")
    print(f"OTA地址: {ota_url}")
    print()
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": client_id
    }
    
    # 请求体（使用mac_address字段名）
    payload = {
        "mac_address": device_id,  # 使用JsonProperty注解的字段名
        "application": {
            "version": "1.0.0"
        },
        "board": {
            "type": "android"
        },
        "chip_model_name": "android"  # 也使用下划线格式
    }
    
    print("🔧 尝试使用JsonProperty字段名：")
    print("- mac_address 而不是 macAddress")
    print("- chip_model_name 而不是 chipModelName")
    print()
    
    print("发送OTA请求...")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(ota_url, headers=headers, json=payload, timeout=10)
        
        print(f"HTTP状态码: {response.status_code}")
        print("服务器响应:")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 解析响应
            if "activation" in response_data:
                print("\n🎉 成功！设备需要激活")
                activation_code = response_data.get("activation", {}).get("code", "未找到激活码")
                message = response_data.get("activation", {}).get("message", "")
                print(f"🔑 激活码: {activation_code}")
                print(f"💬 消息: {message}")
                print()
                print("📋 下一步操作：")
                print("1. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30")
                print(f"2. 在设备绑定界面输入激活码: {activation_code}")
                print("3. 完成绑定后重新测试Android应用的STT功能")
                
            elif "websocket" in response_data and "activation" not in response_data:
                print("\nℹ️  设备已绑定，直接返回WebSocket配置")
                websocket_url = response_data.get("websocket", {}).get("url", "未找到WebSocket URL")
                print(f"🔗 WebSocket地址: {websocket_url}")
                print("✅ 此设备已完成绑定，STT功能应该正常工作")
                
            elif "error" in response_data:
                print("\n❌ OTA请求失败")
                error_msg = response_data.get("error", "未知错误")
                print(f"错误信息: {error_msg}")
                
            else:
                print("\n⚠️  意外的响应格式")
                
        else:
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        print()
        print("🔧 可能的原因：")
        print("1. 网络连接问题")
        print("2. 服务器不可用")
        print("3. URL地址错误")
    
    print()
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_ota_request() 