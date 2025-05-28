#!/usr/bin/env python3
"""
测试设备ID升级后的OTA功能
验证新的设备ID生成策略是否正常工作
"""

import requests
import json
import time
import hashlib
import uuid

def generate_mock_android_device_id():
    """模拟Android设备ID生成策略"""
    # 模拟Android ID
    android_id = "mock_android_id_12345"
    
    # 模拟设备指纹
    manufacturer = "Samsung"
    model = "Galaxy S21"
    fingerprint = f"{manufacturer}-{model}-mock_fingerprint"
    
    # 生成组合标识符
    combined = f"{android_id}-{fingerprint}"
    
    # SHA-256哈希
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()[:6]  # 取前6个字节
    
    # 转换为MAC格式
    mac_id = ':'.join(f'{b:02x}' for b in hash_bytes).upper()
    
    return mac_id, {
        "android_id": android_id,
        "manufacturer": manufacturer,
        "model": model,
        "fingerprint": fingerprint,
        "combined": combined
    }

def test_device_id_generation():
    """测试设备ID生成"""
    print("🔧 测试设备ID生成策略")
    print("=" * 50)
    
    device_id, debug_info = generate_mock_android_device_id()
    
    print(f"📱 生成的设备ID: {device_id}")
    print(f"🔍 调试信息:")
    for key, value in debug_info.items():
        print(f"   {key}: {value}")
    print()
    
    # 验证格式
    import re
    mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    if re.match(mac_pattern, device_id):
        print("✅ 设备ID格式验证通过")
    else:
        print("❌ 设备ID格式无效")
    
    return device_id

def test_ota_with_new_device_id(device_id):
    """测试新设备ID的OTA功能"""
    print(f"\n🌐 测试OTA功能 - 设备ID: {device_id}")
    print("=" * 50)
    
    client_id = f"android-test-{int(time.time())}"
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    # 构建标准化的OTA请求
    request_payload = {
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": "2025-02-28T12:34:56Z"
        },
        "macAddress": device_id,  # 使用驼峰命名
        "board": {
            "type": "android",
            "manufacturer": "Samsung",
            "model": "Galaxy S21"
        },
        "chipModelName": "android",  # 使用驼峰命名
        "uuid": str(uuid.uuid4()),
        "build_time": int(time.time())
    }
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": client_id,
        "X-Language": "Chinese"
    }
    
    print(f"📤 发送OTA请求到: {ota_url}")
    print(f"📋 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"📋 请求体: {json.dumps(request_payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_payload,
            timeout=10
        )
        
        print(f"🔄 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📥 服务器响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 分析响应内容
            if "activation" in result:
                activation_code = result["activation"]["code"]
                message = result["activation"].get("message", "")
                print(f"\n🎯 需要设备绑定")
                print(f"   激活码: {activation_code}")
                print(f"   消息: {message}")
                return "needs_binding", activation_code
                
            elif "websocket" in result:
                websocket_url = result["websocket"]["url"]
                print(f"\n✅ 设备已绑定")
                print(f"   WebSocket URL: {websocket_url}")
                return "bound", websocket_url
                
            else:
                print("\n❓ 未知响应格式")
                return "unknown", None
                
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return "error", response.text
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return "network_error", str(e)

def test_consistency():
    """测试设备ID一致性"""
    print("\n🔄 测试设备ID一致性")
    print("=" * 50)
    
    # 生成多次，验证一致性
    device_ids = []
    for i in range(3):
        device_id, _ = generate_mock_android_device_id()
        device_ids.append(device_id)
        print(f"第{i+1}次生成: {device_id}")
    
    if len(set(device_ids)) == 1:
        print("✅ 设备ID生成一致性测试通过")
        return True
    else:
        print("❌ 设备ID生成不一致")
        return False

def main():
    """主测试函数"""
    print("🚀 小智Android设备ID升级测试")
    print("=" * 60)
    print("测试新的基于设备指纹的设备ID生成策略")
    print("验证与服务器的OTA接口兼容性")
    print()
    
    # 1. 测试设备ID生成
    device_id = test_device_id_generation()
    
    # 2. 测试一致性
    consistency_ok = test_consistency()
    
    # 3. 测试OTA功能
    if consistency_ok:
        ota_result, ota_data = test_ota_with_new_device_id(device_id)
        
        print(f"\n📊 测试结果总结")
        print("=" * 30)
        print(f"设备ID: {device_id}")
        print(f"一致性测试: {'✅ 通过' if consistency_ok else '❌ 失败'}")
        print(f"OTA测试: {ota_result}")
        
        if ota_result == "needs_binding":
            print(f"\n💡 下一步操作:")
            print(f"1. 使用激活码 {ota_data} 在管理面板进行设备绑定")
            print(f"2. 绑定完成后，应用将能够正常连接WebSocket服务")
            
        elif ota_result == "bound":
            print(f"\n✅ 设备已完成绑定，可以直接使用语音功能")
            
        else:
            print(f"\n⚠️  需要检查服务器配置或网络连接")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 