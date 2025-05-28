#!/usr/bin/env python3
"""
测试修复后的绑定配置
验证OTA端点和请求格式是否正确
"""

import requests
import json
import time
import hashlib
import uuid
from datetime import datetime

def generate_android_device_id():
    """生成Android设备ID"""
    # 模拟Android ID和设备指纹
    android_id = f"android_{int(time.time())}"
    manufacturer = "Samsung"
    model = "Galaxy_Test"
    fingerprint = f"{manufacturer}-{model}-test_fingerprint"
    
    # 组合并生成哈希
    combined = f"{android_id}-{fingerprint}"
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()[:6]
    
    # 转换为MAC格式
    mac_id = ':'.join(f'{b:02x}' for b in hash_bytes).upper()
    
    return mac_id, {
        "android_id": android_id,
        "manufacturer": manufacturer,
        "model": model,
        "fingerprint": fingerprint
    }

def test_ota_binding_fix():
    """测试修复后的OTA绑定配置"""
    print("🔧 测试修复后的OTA绑定配置")
    print("=" * 50)
    
    # 生成测试设备信息
    device_id, device_info = generate_android_device_id()
    client_id = f"android-app-{int(time.time())}"
    
    print(f"📱 测试设备信息:")
    print(f"   设备ID: {device_id}")
    print(f"   客户端ID: {client_id}")
    print(f"   设备详情: {json.dumps(device_info, indent=2, ensure_ascii=False)}")
    print()
    
    # 服务器配置
    ota_base_url = "http://47.122.144.73:8002"
    ota_endpoint = "/xiaozhi/ota/"  # 修复后的正确端点
    ota_full_url = f"{ota_base_url}{ota_endpoint}"
    
    print(f"🌐 服务器配置:")
    print(f"   OTA URL: {ota_full_url}")
    print()
    
    # 构建标准化的OTA请求（与Android代码一致）
    request_payload = {
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "macAddress": device_id,  # 驼峰命名
        "chipModelName": "android",  # 驼峰命名
        "board": {
            "type": "android",
            "manufacturer": device_info["manufacturer"],
            "model": device_info["model"]
        },
        "uuid": str(uuid.uuid4()),
        "build_time": int(time.time())
    }
    
    # 设置请求头（与Android代码一致）
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": client_id,
        "X-Language": "Chinese"
    }
    
    print(f"📤 发送OTA绑定检查请求:")
    print(f"   请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"   请求体: {json.dumps(request_payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        # 发送请求
        print("🔄 正在发送请求...")
        response = requests.post(
            ota_full_url,
            headers=headers,
            json=request_payload,
            timeout=10
        )
        
        print(f"📥 服务器响应:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 分析响应内容
                print(f"\n🔍 响应分析:")
                
                if "activation" in result:
                    activation = result["activation"]
                    activation_code = activation.get("code", "未知")
                    message = activation.get("message", "")
                    
                    print(f"✅ 服务器返回激活码，需要绑定设备")
                    print(f"   激活码: {activation_code}")
                    print(f"   消息: {message}")
                    print()
                    print(f"📱 下一步操作:")
                    print(f"1. 访问管理面板: http://47.122.144.73:8002")
                    print(f"2. 使用激活码 {activation_code} 进行设备绑定")
                    print(f"3. 绑定成功后，设备将收到WebSocket连接信息")
                    
                elif "websocket" in result:
                    websocket = result["websocket"]
                    websocket_url = websocket.get("url", "未知")
                    
                    print(f"✅ 设备已绑定成功")
                    print(f"   WebSocket URL: {websocket_url}")
                    print(f"   可以直接使用语音功能")
                    
                    # 检查其他信息
                    if "server_time" in result:
                        server_time = result["server_time"]
                        timestamp = server_time.get("timestamp", 0)
                        timezone_offset = server_time.get("timezone_offset", 0)
                        print(f"   服务器时间: {timestamp}")
                        print(f"   时区偏移: {timezone_offset}")
                        
                    if "firmware" in result:
                        firmware = result["firmware"]
                        version = firmware.get("version", "未知")
                        url = firmware.get("url", "")
                        print(f"   固件版本: {version}")
                        if url:
                            print(f"   更新URL: {url}")
                else:
                    print(f"❓ 未知响应格式，缺少activation或websocket字段")
                    
            except json.JSONDecodeError:
                print(f"❌ 响应不是有效的JSON格式")
                print(f"   原始响应: {response.text}")
                
        else:
            print(f"❌ HTTP请求失败")
            print(f"   错误内容: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求异常: {e}")
        return False

def test_websocket_url():
    """测试WebSocket URL的可达性"""
    print(f"\n🔗 测试WebSocket URL可达性")
    print("=" * 30)
    
    ws_base_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
    
    # 将ws://转换为http://进行基础连接测试
    http_test_url = ws_base_url.replace("ws://", "http://")
    
    print(f"WebSocket URL: {ws_base_url}")
    print(f"HTTP测试URL: {http_test_url}")
    
    try:
        response = requests.get(http_test_url, timeout=5)
        print(f"✅ WebSocket端点可达 (HTTP {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ WebSocket端点不可达: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 绑定配置修复验证测试")
    print("=" * 60)
    print("测试修复后的OTA端点和请求格式")
    print("验证与服务器的正确通信")
    print()
    
    # 1. 测试OTA绑定修复
    ota_success = test_ota_binding_fix()
    
    # 2. 测试WebSocket连接
    ws_success = test_websocket_url()
    
    # 3. 总结测试结果
    print(f"\n📊 测试结果总结")
    print("=" * 30)
    print(f"OTA绑定测试: {'✅ 通过' if ota_success else '❌ 失败'}")
    print(f"WebSocket测试: {'✅ 通过' if ws_success else '❌ 失败'}")
    
    if ota_success and ws_success:
        print(f"\n🎉 绑定配置修复成功！")
        print(f"应用现在应该能够:")
        print(f"1. 正确连接OTA服务进行设备检查")
        print(f"2. 获取激活码或WebSocket连接信息")
        print(f"3. 成功建立语音通信连接")
    else:
        print(f"\n⚠️ 仍存在问题，需要进一步检查:")
        if not ota_success:
            print(f"- OTA端点或请求格式可能仍有问题")
        if not ws_success:
            print(f"- WebSocket服务可能不可用")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 