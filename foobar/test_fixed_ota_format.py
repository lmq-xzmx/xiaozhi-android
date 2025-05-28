#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的OTA请求格式
验证使用下划线命名的请求是否能正确获取激活码
"""

import requests
import json
import time
import random
import uuid

def generate_test_device_id():
    """生成测试用的设备ID（MAC地址格式）"""
    mac_parts = []
    for _ in range(6):
        part = ''.join(random.choices('0123456789ABCDEF', k=2))
        mac_parts.append(part)
    return ':'.join(mac_parts)

def test_fixed_ota_format():
    """测试修复后的OTA请求格式"""
    print("🔧 测试修复后的OTA请求格式")
    print("=" * 50)
    
    device_id = generate_test_device_id()
    client_id = f"android-app-{int(time.time())}"
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    # 使用修复后的请求格式（下划线命名）
    request_payload = {
        "application": {
            "version": "1.0.0"
        },
        "mac_address": device_id,  # 下划线命名
        "chip_model_name": "android",  # 下划线命名
        "board": {
            "type": "android"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": client_id
    }
    
    print(f"📱 测试设备ID: {device_id}")
    print(f"🌐 OTA URL: {ota_url}")
    print(f"📋 请求格式（修复后）:")
    print(json.dumps(request_payload, indent=2, ensure_ascii=False))
    print()
    
    try:
        print("📤 发送OTA请求...")
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_payload,
            timeout=10
        )
        
        print(f"📥 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功！")
            print("📋 服务器响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查响应内容
            if "activation" in result:
                activation_code = result["activation"]["code"]
                print(f"\n🎯 成功获取激活码: {activation_code}")
                print("✅ OTA请求格式修复成功！")
                return True, activation_code
                
            elif "websocket" in result:
                websocket_url = result["websocket"]["url"]
                print(f"\n🔗 设备已绑定，WebSocket URL: {websocket_url}")
                return True, None
                
            else:
                print("\n❓ 响应格式异常，缺少activation或websocket字段")
                return False, None
                
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False, None

def compare_formats():
    """对比新旧请求格式"""
    print("\n📊 请求格式对比")
    print("=" * 50)
    
    print("❌ 旧格式（驼峰命名 - 导致错误）:")
    old_format = {
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": "2025-05-27T00:00:00Z"
        },
        "macAddress": "XX:XX:XX:XX:XX:XX",  # 驼峰命名
        "chipModelName": "android",  # 驼峰命名
        "board": {
            "type": "android",
            "manufacturer": "Samsung",
            "model": "Galaxy S21"
        },
        "uuid": "uuid-string",
        "build_time": 1234567890
    }
    print(json.dumps(old_format, indent=2, ensure_ascii=False))
    
    print("\n✅ 新格式（下划线命名 - 修复后）:")
    new_format = {
        "application": {
            "version": "1.0.0"
        },
        "mac_address": "XX:XX:XX:XX:XX:XX",  # 下划线命名
        "chip_model_name": "android",  # 下划线命名
        "board": {
            "type": "android"
        }
    }
    print(json.dumps(new_format, indent=2, ensure_ascii=False))

def main():
    """主测试函数"""
    print("🚀 OTA请求格式修复验证")
    print("=" * 60)
    print("测试修复后的下划线命名格式是否能正确获取激活码")
    print()
    
    # 对比格式
    compare_formats()
    
    # 测试修复后的格式
    success, activation_code = test_fixed_ota_format()
    
    print(f"\n📊 测试结果")
    print("=" * 30)
    if success:
        if activation_code:
            print("✅ 测试成功！成功获取激活码")
            print(f"🎯 激活码: {activation_code}")
            print("\n💡 修复说明:")
            print("- 将 macAddress 改为 mac_address")
            print("- 将 chipModelName 改为 chip_model_name")
            print("- 简化了请求体结构")
            print("- 移除了不必要的字段")
        else:
            print("✅ 测试成功！设备已绑定")
    else:
        print("❌ 测试失败，需要进一步检查")
        print("\n🔍 可能的问题:")
        print("- 网络连接问题")
        print("- 服务器配置问题")
        print("- 请求格式仍需调整")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 