#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化的Android OTA格式
验证新的简化格式是否能避免服务器500错误
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

def test_simplified_android_format():
    """测试简化的Android格式"""
    print("🔧 测试简化的Android OTA格式")
    print("=" * 50)
    
    device_id = generate_android_device_id()
    print(f"📱 设备ID: {device_id}")
    
    # 简化的Android格式（新的优先格式）
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
    
    print(f"\n📤 发送简化Android格式请求")
    print(f"URL: {ota_url}")
    print(f"请求体: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
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
        
        response_text = response.text
        print(f"响应内容: {response_text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ JSON解析成功")
                
                # 检查是否是标准API响应格式
                if "code" in result and "msg" in result:
                    code = result["code"]
                    msg = result["msg"]
                    data = result.get("data")
                    
                    print(f"📋 标准API响应:")
                    print(f"  code: {code}")
                    print(f"  msg: {msg}")
                    print(f"  data: {data}")
                    
                    if code == 0:
                        print(f"✅ API调用成功")
                        if data:
                            print(f"📦 数据内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                            # 检查data中的OTA字段
                            if isinstance(data, dict):
                                has_activation = "activation" in data
                                has_websocket = "websocket" in data
                                print(f"🔍 OTA字段检查:")
                                print(f"  activation: {has_activation}")
                                print(f"  websocket: {has_websocket}")
                                
                                if has_activation:
                                    activation = data["activation"]
                                    print(f"🎯 激活信息: {activation}")
                                    return True, "需要激活", activation.get("code", "")
                                elif has_websocket:
                                    websocket = data["websocket"]
                                    print(f"🔗 WebSocket信息: {websocket}")
                                    return True, "已激活", websocket.get("url", "")
                        else:
                            print(f"⚠️ data字段为空")
                            return False, "data为空", ""
                    else:
                        print(f"❌ API调用失败: {msg}")
                        return False, f"API错误: {msg}", ""
                        
                else:
                    # 直接的OTA响应格式
                    print(f"📋 直接OTA响应格式:")
                    has_activation = "activation" in result
                    has_websocket = "websocket" in result
                    
                    print(f"🔍 OTA字段检查:")
                    print(f"  activation: {has_activation}")
                    print(f"  websocket: {has_websocket}")
                    
                    if has_activation:
                        activation = result["activation"]
                        print(f"🎯 激活信息: {activation}")
                        return True, "需要激活", activation.get("code", "")
                    elif has_websocket:
                        websocket = result["websocket"]
                        print(f"🔗 WebSocket信息: {websocket}")
                        return True, "已激活", websocket.get("url", "")
                    else:
                        print(f"❌ 既没有activation也没有websocket")
                        return False, "响应格式异常", ""
                        
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON解析失败: {e}")
                return False, "JSON解析失败", ""
                
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            return False, f"HTTP {response.status_code}", ""
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 网络请求失败: {e}")
        return False, f"网络错误: {e}", ""

def main():
    """主函数"""
    print("🚀 简化Android OTA格式测试")
    print("验证新的简化格式是否能避免服务器500错误")
    print()
    
    success, status, data = test_simplified_android_format()
    
    print(f"\n📊 测试结果")
    print("=" * 30)
    print(f"成功: {'✅' if success else '❌'}")
    print(f"状态: {status}")
    print(f"数据: {data}")
    
    if success:
        print(f"\n🎉 简化Android格式测试成功！")
        print(f"💡 建议:")
        print(f"1. 将此格式设为Android应用的首选格式")
        print(f"2. 重新构建APK并测试")
        print(f"3. 验证完整的激活流程")
    else:
        print(f"\n⚠️ 简化格式仍有问题")
        print(f"💡 建议:")
        print(f"1. 检查服务器端配置")
        print(f"2. 尝试其他格式")
        print(f"3. 联系服务器端开发人员")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 