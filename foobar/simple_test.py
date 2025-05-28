#!/usr/bin/env python3
"""
使用标准库测试OTA配置
不依赖requests库
"""

import urllib.request
import urllib.parse
import json
import uuid
import time
import hashlib
from datetime import datetime

def generate_test_device_id():
    """生成测试设备ID"""
    # 基于时间戳生成
    timestamp = str(int(time.time()))
    combined = f"android-test-{timestamp}"
    
    # 生成哈希并转换为MAC格式
    hash_obj = hashlib.sha256(combined.encode())
    hash_bytes = hash_obj.digest()[:6]
    mac_id = ':'.join(f'{b:02x}' for b in hash_bytes).upper()
    
    return mac_id

def test_ota_endpoint():
    """测试OTA端点"""
    print("🔧 测试OTA服务器配置")
    print("=" * 50)
    
    # 生成测试数据
    device_id = generate_test_device_id()
    client_id = f"android-test-{int(time.time())}"
    test_uuid = str(uuid.uuid4())
    
    print(f"📱 测试设备信息:")
    print(f"   设备ID: {device_id}")
    print(f"   客户端ID: {client_id}")
    print(f"   UUID: {test_uuid}")
    print()
    
    # 构建OTA请求
    request_data = {
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "macAddress": device_id,
        "chipModelName": "android",
        "board": {
            "type": "android",
            "manufacturer": "TestManufacturer",
            "model": "TestModel"
        },
        "uuid": test_uuid,
        "build_time": int(time.time())
    }
    
    # 服务器URL
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    print(f"🌐 测试URL: {ota_url}")
    print(f"📤 请求内容:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        # 准备请求
        data = json.dumps(request_data).encode('utf-8')
        
        req = urllib.request.Request(
            ota_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Device-Id': device_id,
                'Client-Id': client_id,
                'X-Language': 'Chinese'
            },
            method='POST'
        )
        
        print("🔄 发送请求...")
        
        # 发送请求
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')
            
            print(f"📥 服务器响应:")
            print(f"   状态码: {status_code}")
            print(f"   响应内容: {response_data}")
            print()
            
            if status_code == 200:
                try:
                    result = json.loads(response_data)
                    print(f"🔍 响应分析:")
                    
                    if "activation" in result:
                        activation = result["activation"]
                        activation_code = activation.get("code", "未知")
                        message = activation.get("message", "")
                        
                        print(f"✅ 服务器返回激活信息")
                        print(f"   激活码: {activation_code}")
                        print(f"   消息: {message}")
                        print()
                        print(f"📱 下一步操作:")
                        print(f"1. 访问管理面板: http://47.122.144.73:8002")
                        print(f"2. 使用激活码 {activation_code} 进行设备绑定")
                        return True
                        
                    elif "websocket" in result:
                        websocket = result["websocket"]
                        websocket_url = websocket.get("url", "未知")
                        
                        print(f"✅ 设备已绑定成功")
                        print(f"   WebSocket URL: {websocket_url}")
                        return True
                        
                    elif "message" in result:
                        message = result.get("message", "")
                        print(f"⚠️ 服务器消息: {message}")
                        
                        if "internal exception" in message.lower():
                            print(f"❌ 服务器内部错误，可能的原因:")
                            print(f"   1. 请求格式不正确")
                            print(f"   2. 必需字段缺失")
                            print(f"   3. 服务器配置问题")
                        return False
                        
                    else:
                        print(f"❓ 未知响应格式")
                        print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"❌ 响应不是有效的JSON格式")
                    print(f"   原始响应: {response_data}")
                    return False
            else:
                print(f"❌ HTTP请求失败 (状态码: {status_code})")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP错误: {e.code} - {e.reason}")
        try:
            error_data = e.read().decode('utf-8')
            print(f"   错误内容: {error_data}")
        except:
            pass
        return False
        
    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e.reason}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_websocket_connectivity():
    """测试WebSocket连接性"""
    print(f"\n🔗 测试WebSocket连接性")
    print("=" * 30)
    
    ws_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
    http_test_url = "http://47.122.144.73:8000/xiaozhi/v1/"
    
    print(f"WebSocket URL: {ws_url}")
    print(f"HTTP测试URL: {http_test_url}")
    
    try:
        req = urllib.request.Request(http_test_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            print(f"✅ WebSocket端点可达 (HTTP {status_code})")
            return True
    except Exception as e:
        print(f"❌ WebSocket端点不可达: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 小智Android绑定配置验证测试")
    print("=" * 60)
    print("验证修复后的OTA端点和配置")
    print()
    
    # 测试OTA端点
    ota_success = test_ota_endpoint()
    
    # 测试WebSocket
    ws_success = test_websocket_connectivity()
    
    # 总结
    print(f"\n📊 测试结果总结")
    print("=" * 30)
    print(f"OTA绑定测试: {'✅ 通过' if ota_success else '❌ 失败'}")
    print(f"WebSocket测试: {'✅ 通过' if ws_success else '❌ 失败'}")
    
    if ota_success and ws_success:
        print(f"\n🎉 配置验证成功！")
        print(f"修复要点:")
        print(f"1. ✅ OTA端点已修复为 /xiaozhi/ota/")
        print(f"2. ✅ 请求格式已标准化")
        print(f"3. ✅ 设备ID生成策略已优化")
        print(f"4. ✅ WebSocket连接可用")
    else:
        print(f"\n⚠️ 仍需要调试:")
        if not ota_success:
            print(f"- 检查OTA请求格式和服务器处理逻辑")
        if not ws_success:
            print(f"- 检查WebSocket服务状态")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 