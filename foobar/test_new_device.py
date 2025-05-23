#!/usr/bin/env python3
"""
测试新设备获取激活码
"""

import requests
import json
import time
import random

def test_new_device():
    print("=== 测试新设备获取激活码 ===")
    print()
    
    # 生成新的设备ID
    device_id = f"00:11:22:33:44:{'%02x' % random.randint(0, 255)}"
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
    
    # 请求体
    payload = {
        "mac_address": device_id,
        "application": {
            "version": "1.0.0"
        },
        "board": {
            "type": "android"
        },
        "chip_model_name": "android"
    }
    
    print("发送OTA请求...")
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
                activation_code = response_data.get("activation", {}).get("code", "")
                message = response_data.get("activation", {}).get("message", "")
                
                print(f"\n🎉 成功获取激活码！")
                print(f"🔑 激活码: {activation_code}")
                print(f"💬 消息: {message}")
                print()
                print("📋 立即执行以下步骤：")
                print("1. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30")
                print(f"2. 在设备绑定界面输入激活码: {activation_code}")
                print("3. 完成绑定")
                print()
                print("🔍 绑定完成后，您的Android应用就可以使用此设备ID进行STT了！")
                print(f"📝 记住这个设备ID: {device_id}")
                
                return device_id, activation_code
                
            elif "websocket" in response_data and "activation" not in response_data:
                print("\nℹ️  设备已绑定，直接返回WebSocket配置")
                
            else:
                print("\n⚠️  意外的响应格式")
                
        else:
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
    
    print()
    print("=== 测试完成 ===")
    return None, None

if __name__ == "__main__":
    device_id, activation_code = test_new_device()
    if activation_code:
        print(f"\n✅ 请使用激活码 {activation_code} 在管理面板绑定设备 {device_id}")
    else:
        print("\n❌ 未能获取激活码，请检查网络连接和服务器状态") 