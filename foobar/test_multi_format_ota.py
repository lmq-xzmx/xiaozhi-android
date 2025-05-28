#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多格式OTA请求策略
验证Android应用的多种OTA请求格式是否能被服务器接受
"""

import requests
import json
import time
import hashlib
import uuid
from typing import Dict, Any, Tuple

def generate_stable_device_id() -> str:
    """生成稳定的设备ID（模拟Android设备指纹）"""
    android_id = "mock_android_id_12345"
    manufacturer = "Samsung"
    model = "Galaxy S21"
    fingerprint = f"{manufacturer}-{model}-mock_fingerprint"
    
    combined = f"{android_id}-{fingerprint}"
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()[:6]
    
    return ':'.join(f'{b:02x}' for b in hash_bytes).upper()

def build_android_standard_format(device_id: str) -> Dict[str, Any]:
    """构建Android标准格式的OTA请求"""
    return {
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": "2025-02-28 12:34:56"
        },
        "macAddress": device_id,  # 驼峰命名
        "chipModelName": "android",  # 驼峰命名
        "board": {
            "type": "android",
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "version": "14"
        },
        "uuid": str(uuid.uuid4()),
        "build_time": int(time.time())
    }

def build_esp32_compatible_format(device_id: str) -> Dict[str, Any]:
    """构建ESP32兼容格式的OTA请求"""
    return {
        "mac": device_id,  # 不是macAddress
        "chip_model": "android",  # 不是chipModelName
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi"  # 不是xiaozhi-android
        },
        "board": {
            "type": "android"
        },
        "uuid": str(uuid.uuid4())
    }

def build_minimal_format(device_id: str) -> Dict[str, Any]:
    """构建最简化格式的OTA请求"""
    return {
        "mac": device_id,
        "chip_model": "android",
        "version": "1.0.0",
        "uuid": str(uuid.uuid4())
    }

def test_ota_format(format_name: str, request_data: Dict[str, Any], device_id: str) -> Tuple[bool, str]:
    """测试特定格式的OTA请求"""
    print(f"\n🔧 测试 {format_name}")
    print("=" * 50)
    
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    client_id = f"android-test-{int(time.time())}"
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": client_id,
        "X-Language": "Chinese"
    }
    
    print(f"📤 发送请求到: {ota_url}")
    print(f"📋 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"📋 请求体: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_data,
            timeout=10
        )
        
        print(f"🔄 HTTP状态码: {response.status_code}")
        response_text = response.text
        print(f"📥 服务器响应: {response_text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "activation" in result:
                    activation_code = result["activation"]["code"]
                    print(f"✅ {format_name} 成功 - 需要绑定")
                    print(f"   激活码: {activation_code}")
                    return True, f"需要绑定，激活码: {activation_code}"
                    
                elif "websocket" in result:
                    websocket_url = result["websocket"]["url"]
                    print(f"✅ {format_name} 成功 - 已绑定")
                    print(f"   WebSocket URL: {websocket_url}")
                    return True, f"已绑定，WebSocket: {websocket_url}"
                    
                else:
                    print(f"❓ {format_name} 响应格式未知")
                    return False, "响应格式未知"
                    
            except json.JSONDecodeError:
                print(f"❌ {format_name} 响应不是有效JSON")
                return False, "响应不是有效JSON"
                
        else:
            if "Invalid OTA request" in response_text:
                print(f"❌ {format_name} 被服务器拒绝")
                return False, "服务器拒绝请求格式"
            else:
                print(f"❌ {format_name} HTTP错误: {response.status_code}")
                return False, f"HTTP错误: {response.status_code}"
                
    except requests.exceptions.RequestException as e:
        print(f"❌ {format_name} 网络错误: {e}")
        return False, f"网络错误: {e}"

def main():
    """主测试函数"""
    print("🚀 多格式OTA请求测试")
    print("=" * 60)
    print("测试Android应用的多种OTA请求格式")
    print("验证服务器对不同格式的支持情况")
    print()
    
    # 生成设备ID
    device_id = generate_stable_device_id()
    print(f"📱 使用设备ID: {device_id}")
    
    # 定义测试格式
    test_formats = [
        ("Android标准格式", lambda: build_android_standard_format(device_id)),
        ("ESP32兼容格式", lambda: build_esp32_compatible_format(device_id)),
        ("最简化格式", lambda: build_minimal_format(device_id))
    ]
    
    results = []
    
    # 依次测试每种格式
    for format_name, format_builder in test_formats:
        request_data = format_builder()
        success, message = test_ota_format(format_name, request_data, device_id)
        results.append((format_name, success, message))
        
        if success:
            print(f"\n🎯 找到可用格式: {format_name}")
            break
        
        time.sleep(1)  # 避免请求过于频繁
    
    # 输出测试总结
    print(f"\n📊 测试结果总结")
    print("=" * 30)
    
    successful_formats = []
    failed_formats = []
    
    for format_name, success, message in results:
        if success:
            successful_formats.append(format_name)
            print(f"✅ {format_name}: {message}")
        else:
            failed_formats.append(format_name)
            print(f"❌ {format_name}: {message}")
    
    print(f"\n📈 统计信息:")
    print(f"成功格式: {len(successful_formats)}/{len(test_formats)}")
    print(f"失败格式: {len(failed_formats)}/{len(test_formats)}")
    
    if successful_formats:
        print(f"\n💡 建议:")
        print(f"Android应用应优先使用: {successful_formats[0]}")
        if len(successful_formats) > 1:
            print(f"备用格式: {', '.join(successful_formats[1:])}")
    else:
        print(f"\n⚠️ 警告:")
        print(f"所有格式都失败，需要检查服务器配置或网络连接")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 