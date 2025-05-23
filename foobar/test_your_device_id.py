#!/usr/bin/env python3
"""
测试您设置的固定设备ID: 00:11:22:33:44:55
"""

import requests
import json

def test_your_device_id():
    print("=== 测试您的固定设备ID ===")
    device_id = "00:11:22:33:44:55"  # 您在DeviceInfo.kt中设置的ID
    print(f"设备ID: {device_id}")
    print()
    
    try:
        response = requests.post(
            "http://47.122.144.73:8002/xiaozhi/ota/",
            headers={
                "Content-Type": "application/json",
                "Device-Id": device_id,
                "Client-Id": "android-app"
            },
            json={
                "mac_address": device_id,
                "application": {"version": "1.0.0"},
                "board": {"type": "android"},
                "chip_model_name": "android"
            },
            timeout=10
        )
        
        print(f"HTTP状态码: {response.status_code}")
        result = response.json()
        print("服务器响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        if "activation" in result:
            activation_code = result.get("activation", {}).get("code", "")
            print(f"🔑 需要绑定！激活码: {activation_code}")
            print()
            print("📋 请立即执行以下步骤:")
            print("1. 访问管理面板: http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30")
            print(f"2. 输入激活码: {activation_code}")
            print("3. 完成绑定")
            print()
            print("然后继续下一步验证STT功能...")
            return False, activation_code
            
        elif "websocket" in result and "activation" not in result:
            print("✅ 设备已绑定！可以直接测试STT功能")
            websocket_url = result.get("websocket", {}).get("url", "")
            print(f"🔗 WebSocket地址: {websocket_url}")
            return True, None
            
        else:
            print("⚠️ 意外的响应格式")
            return False, None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False, None

if __name__ == "__main__":
    is_bound, activation_code = test_your_device_id()
    
    if is_bound:
        print("\n🎯 下一步: 验证STT功能")
        print("1. 清除应用数据: adb shell pm clear info.dourok.voicebot")
        print("2. 重新编译运行Android应用")
        print("3. 测试语音输入功能")
    elif activation_code:
        print(f"\n🔑 请使用激活码 {activation_code} 完成设备绑定!")
    else:
        print("\n❌ 请检查网络连接和服务器状态") 