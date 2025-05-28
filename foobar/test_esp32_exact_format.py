#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ESP32精确格式的OTA请求
基于ESP32硬件设备的实际请求格式进行测试
"""

import requests
import json
import time
import hashlib

def generate_device_id() -> str:
    """生成设备ID"""
    return "8E:40:7C:54:67:81"

def build_esp32_exact_format(device_id: str) -> dict:
    """构建ESP32精确格式的OTA请求"""
    return {
        "version": 2,
        "flash_size": 4194304,
        "psram_size": 0,
        "mac_address": device_id,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "chip_model_name": "ESP32",
        "chip_info": {
            "model": 1,
            "cores": 2,
            "revision": 1,
            "features": 50
        },
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi",
            "compile_time": "Feb 28 2025 12:34:56",
            "compile_date": "Feb 28 2025",
            "compile_time_str": "12:34:56",
            "idf_version": "v4.4.4"
        },
        "partition_table": [
            {
                "label": "nvs",
                "offset": 36864,
                "size": 24576,
                "type": 1,
                "subtype": 2
            },
            {
                "label": "phy_init",
                "offset": 61440,
                "size": 4096,
                "type": 1,
                "subtype": 1
            },
            {
                "label": "factory",
                "offset": 65536,
                "size": 1048576,
                "type": 0,
                "subtype": 0
            }
        ],
        "ota": {
            "state": "app_update"
        },
        "board": {
            "type": "esp32",
            "manufacturer": "Espressif",
            "model": "ESP32-DevKitC",
            "version": "v4"
        }
    }

def build_android_esp32_hybrid(device_id: str) -> dict:
    """构建Android-ESP32混合格式"""
    return {
        "version": 2,
        "flash_size": 8589934592,  # 8GB Android存储
        "psram_size": 8589934592,  # 8GB RAM
        "mac_address": device_id,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "chip_model_name": "android",
        "chip_info": {
            "model": 1030,  # Android API 30
            "cores": 8,
            "revision": 1,
            "features": 63  # 所有功能
        },
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi",
            "compile_time": "Feb 28 2025 12:34:56",
            "compile_date": "Feb 28 2025",
            "compile_time_str": "12:34:56",
            "idf_version": "android-14"
        },
        "partition_table": [
            {
                "label": "system",
                "offset": 0,
                "size": 4294967296,
                "type": 0,
                "subtype": 0
            }
        ],
        "ota": {
            "state": "app_update"
        },
        "board": {
            "type": "android",
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "version": "14"
        }
    }

def build_simple_esp32_format(device_id: str) -> dict:
    """构建简化的ESP32格式"""
    return {
        "mac_address": device_id,
        "chip_model_name": "ESP32",
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi"
        },
        "board": {
            "type": "esp32"
        }
    }

def test_format(format_name: str, request_data: dict, device_id: str):
    """测试特定格式"""
    print(f"\n🔧 测试 {format_name}")
    print("=" * 50)
    
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": f"test-{int(time.time())}",
        "X-Language": "Chinese"
    }
    
    print(f"📤 发送请求到: {ota_url}")
    print(f"📋 请求体大小: {len(json.dumps(request_data))} 字节")
    print(f"📋 主要字段: {list(request_data.keys())}")
    
    try:
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_data,
            timeout=15
        )
        
        print(f"🔄 HTTP状态码: {response.status_code}")
        response_text = response.text
        print(f"📥 服务器响应: {response_text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "activation" in result:
                    activation_code = result["activation"]["code"]
                    print(f"✅ {format_name} 成功 - 获得激活码: {activation_code}")
                    return True, activation_code
                    
                elif "websocket" in result:
                    websocket_url = result["websocket"]["url"]
                    print(f"✅ {format_name} 成功 - 设备已绑定")
                    return True, websocket_url
                    
                elif "error" in result:
                    print(f"❌ {format_name} 服务器错误: {result['error']}")
                    return False, result['error']
                    
                else:
                    print(f"❓ {format_name} 未知响应格式")
                    return False, "未知响应格式"
                    
            except json.JSONDecodeError:
                print(f"❌ {format_name} 响应不是JSON格式")
                return False, "非JSON响应"
        else:
            print(f"❌ {format_name} HTTP错误: {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        print(f"❌ {format_name} 异常: {e}")
        return False, str(e)

def main():
    """主测试函数"""
    print("🚀 ESP32精确格式OTA测试")
    print("=" * 60)
    print("尝试使用更接近ESP32实际格式的请求")
    print()
    
    device_id = generate_device_id()
    print(f"📱 使用设备ID: {device_id}")
    
    # 测试格式列表
    test_formats = [
        ("ESP32精确格式", build_esp32_exact_format),
        ("Android-ESP32混合格式", build_android_esp32_hybrid),
        ("简化ESP32格式", build_simple_esp32_format)
    ]
    
    results = []
    
    for format_name, format_builder in test_formats:
        request_data = format_builder(device_id)
        success, message = test_format(format_name, request_data, device_id)
        results.append((format_name, success, message))
        
        if success:
            print(f"\n🎯 找到可用格式: {format_name}")
            print(f"📋 完整请求体:")
            print(json.dumps(request_data, indent=2, ensure_ascii=False))
            break
        
        time.sleep(2)  # 避免请求过于频繁
    
    # 总结
    print(f"\n📊 测试结果总结")
    print("=" * 30)
    
    for format_name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {format_name}: {message}")
    
    successful_count = sum(1 for _, success, _ in results if success)
    print(f"\n📈 成功率: {successful_count}/{len(results)}")
    
    if successful_count == 0:
        print(f"\n💡 建议:")
        print(f"1. 检查服务器是否正在运行")
        print(f"2. 验证OTA接口的具体要求")
        print(f"3. 查看服务器端日志获取更多信息")
        print(f"4. 尝试使用ESP32硬件设备的实际请求进行对比")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 