#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试OTA响应问题
分析为什么Android应用收到"服务器响应格式异常"错误
"""

import requests
import json
import time
import hashlib

def generate_android_device_id() -> str:
    """生成Android设备ID"""
    android_id = "mock_android_id_12345"
    manufacturer = "Samsung"
    model = "Galaxy S21"
    fingerprint = f"{manufacturer}-{model}-mock_fingerprint"
    
    combined = f"{android_id}-{fingerprint}"
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()[:6]
    
    return ':'.join(f'{b:02x}' for b in hash_bytes).upper()

def test_ota_request_detailed():
    """详细测试OTA请求"""
    print("🔍 调试OTA响应问题")
    print("=" * 60)
    
    device_id = generate_android_device_id()
    print(f"📱 设备ID: {device_id}")
    
    # 测试ESP32精确格式（之前验证可用的格式）
    request_data = {
        "version": 2,
        "flash_size": 8589934592,
        "psram_size": 8589934592,
        "mac_address": device_id,
        "uuid": "android-app-uuid-12345",
        "chip_model_name": "ESP32",
        "chip_info": {
            "model": 1030,
            "cores": 8,
            "revision": 1,
            "features": 63
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
            "type": "esp32",
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "version": "14"
        }
    }
    
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": "android-app-12345",
        "X-Language": "Chinese"
    }
    
    print(f"\n📤 发送OTA请求")
    print(f"URL: {ota_url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Body size: {len(json.dumps(request_data))} bytes")
    
    try:
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_data,
            timeout=15
        )
        
        print(f"\n📥 服务器响应")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 获取原始响应文本
        response_text = response.text
        print(f"响应长度: {len(response_text)} 字符")
        print(f"原始响应: {response_text}")
        
        # 分析响应
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ JSON解析成功")
                print(f"响应结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 检查响应字段
                has_activation = "activation" in result
                has_websocket = "websocket" in result
                has_error = "error" in result
                has_server_time = "server_time" in result
                has_firmware = "firmware" in result
                
                print(f"\n🔍 响应字段分析:")
                print(f"  activation: {has_activation}")
                print(f"  websocket: {has_websocket}")
                print(f"  error: {has_error}")
                print(f"  server_time: {has_server_time}")
                print(f"  firmware: {has_firmware}")
                
                if has_activation:
                    activation = result["activation"]
                    print(f"\n🎯 激活信息:")
                    print(f"  code: {activation.get('code', 'N/A')}")
                    print(f"  message: {activation.get('message', 'N/A')}")
                    print(f"  challenge: {activation.get('challenge', 'N/A')}")
                    
                if has_websocket:
                    websocket = result["websocket"]
                    print(f"\n🔗 WebSocket信息:")
                    print(f"  url: {websocket.get('url', 'N/A')}")
                    
                if has_error:
                    print(f"\n❌ 错误信息: {result['error']}")
                    
                # 判断Android应用会如何处理这个响应
                print(f"\n📱 Android应用处理预测:")
                if has_activation and not has_websocket:
                    print(f"  ✅ 应该识别为需要激活")
                elif has_websocket and not has_activation:
                    print(f"  ✅ 应该识别为已激活")
                elif has_activation and has_websocket:
                    print(f"  ⚠️ 同时包含激活和WebSocket，可能导致混淆")
                elif has_error:
                    print(f"  ❌ 包含错误信息")
                else:
                    print(f"  ❌ 既没有activation也没有websocket，会触发'服务器响应格式异常'")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON解析失败: {e}")
                print(f"这会导致Android应用报告'服务器响应格式异常'")
                
        elif response.status_code == 500:
            print(f"\n❌ 服务器内部错误 (500)")
            print(f"这可能是ESP32精确格式导致的服务器端问题")
            print(f"错误内容: {response_text}")
            
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            print(f"错误内容: {response_text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 网络请求失败: {e}")
        
    return response.status_code if 'response' in locals() else None

def test_simplified_format():
    """测试简化格式"""
    print(f"\n\n🔧 测试简化格式")
    print("=" * 40)
    
    device_id = generate_android_device_id()
    
    # 简化的请求格式
    request_data = {
        "mac_address": device_id,
        "chip_model_name": "android",
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android"
        },
        "board": {
            "type": "android"
        },
        "uuid": "android-app-uuid-12345"
    }
    
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": "android-app-12345",
        "X-Language": "Chinese"
    }
    
    print(f"📤 发送简化格式请求")
    print(f"Body: {json.dumps(request_data, indent=2)}")
    
    try:
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_data,
            timeout=15
        )
        
        print(f"\n📥 响应: {response.status_code}")
        print(f"内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                has_activation = "activation" in result
                has_websocket = "websocket" in result
                print(f"✅ 简化格式成功，包含activation: {has_activation}, websocket: {has_websocket}")
                return True
            except:
                print(f"❌ 简化格式JSON解析失败")
                return False
        else:
            print(f"❌ 简化格式HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 简化格式请求失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 OTA响应调试工具")
    print("分析Android应用'服务器响应格式异常'问题")
    print()
    
    # 测试ESP32精确格式
    status_code = test_ota_request_detailed()
    
    # 如果ESP32格式有问题，测试简化格式
    if status_code != 200:
        simplified_success = test_simplified_format()
        
        print(f"\n📊 测试结果总结")
        print("=" * 30)
        print(f"ESP32精确格式: {'❌ 失败' if status_code != 200 else '✅ 成功'}")
        print(f"简化格式: {'✅ 成功' if simplified_success else '❌ 失败'}")
        
        if simplified_success:
            print(f"\n💡 建议:")
            print(f"1. Android应用应该回退到简化格式")
            print(f"2. 修改Ota.kt中的格式优先级")
            print(f"3. 将简化格式放在ESP32精确格式之前")
        else:
            print(f"\n⚠️ 警告:")
            print(f"所有格式都失败，可能是服务器端问题")
    else:
        print(f"\n✅ ESP32精确格式工作正常")
        print(f"问题可能在Android应用的响应解析逻辑")
    
    print(f"\n🏁 调试完成")

if __name__ == "__main__":
    main() 