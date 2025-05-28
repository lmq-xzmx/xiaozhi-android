#!/usr/bin/env python3
"""
严格按照OTAController.java验证逻辑的OTA测试
修复所有已知问题：
1. Device-Id头部必须与请求体中的macAddress完全一致
2. application字段必须存在且不为null  
3. MAC地址格式必须符合正则表达式：^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$
"""

import urllib.request
import urllib.parse
import json
import uuid
import time
import hashlib
import re
from datetime import datetime

def validate_mac_address(mac_address):
    """验证MAC地址格式（严格按照Java端逻辑）"""
    if not mac_address:
        return False
    
    # MAC地址正则：^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$
    mac_pattern = r"^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$"
    return bool(re.match(mac_pattern, mac_address))

def generate_valid_mac():
    """生成一个有效的MAC地址"""
    # 生成6个字节的随机数据
    mac_bytes = []
    for _ in range(6):
        mac_bytes.append(f"{hash(str(time.time() + _)) % 256:02x}")
    
    # 使用冒号分隔
    return ":".join(mac_bytes).upper()

def test_ota_correct_format():
    """测试修复后的OTA配置"""
    print("🔧 测试OTA正确格式（严格按照Java验证逻辑）")
    print("=" * 60)
    
    # 1. 生成有效的MAC地址
    device_mac = generate_valid_mac()
    print(f"📱 生成设备MAC: {device_mac}")
    
    # 2. 验证MAC地址格式
    is_valid_mac = validate_mac_address(device_mac)
    print(f"🔍 MAC地址格式验证: {'✅ 有效' if is_valid_mac else '❌ 无效'}")
    
    if not is_valid_mac:
        print("❌ MAC地址格式验证失败，退出测试")
        return False
    
    # 3. 生成客户端ID
    client_id = f"android-app-{int(time.time())}"
    test_uuid = str(uuid.uuid4())
    
    print(f"🔑 客户端ID: {client_id}")
    print(f"🆔 测试UUID: {test_uuid}")
    print()
    
    # 4. 构建严格符合要求的请求体
    request_data = {
        # 关键1：macAddress必须与Device-Id头部完全一致
        "macAddress": device_mac,  # 驼峰命名
        
        # 关键2：application字段必须存在且不为null
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        
        # 可选字段（但建议包含）
        "board": {
            "type": "android",
            "manufacturer": "TestManufacturer",
            "model": "TestModel"
        },
        
        "chipModelName": "android",  # 驼峰命名
        "uuid": test_uuid,
        "build_time": int(time.time())
    }
    
    # 5. 设置请求头（关键：Device-Id必须与macAddress一致）
    headers = {
        'Content-Type': 'application/json',
        'Device-Id': device_mac,  # 必须与请求体macAddress完全一致
        'Client-Id': client_id,
        'X-Language': 'Chinese'
    }
    
    # 6. 服务器地址（确保是正确的Java后端）
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    print(f"🌐 OTA服务地址: {ota_url}")
    print(f"📋 关键验证点:")
    print(f"   ✓ Device-Id: {device_mac}")
    print(f"   ✓ macAddress: {request_data['macAddress']}")
    print(f"   ✓ 两者是否一致: {'✅ 是' if device_mac == request_data['macAddress'] else '❌ 否'}")
    print(f"   ✓ application字段: {'✅ 存在' if request_data.get('application') else '❌ 缺失'}")
    print(f"   ✓ MAC格式验证: {'✅ 通过' if is_valid_mac else '❌ 失败'}")
    print()
    
    print(f"📤 发送请求:")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求体: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        # 7. 发送HTTP请求
        data = json.dumps(request_data).encode('utf-8')
        
        req = urllib.request.Request(
            ota_url,
            data=data,
            headers=headers,
            method='POST'
        )
        
        print("🔄 发送OTA请求...")
        
        # 8. 获取响应
        with urllib.request.urlopen(req, timeout=15) as response:
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
                    
                    # 检查激活码（需要绑定的新设备）
                    if "activation" in result:
                        activation = result["activation"]
                        activation_code = activation.get("code", "未知")
                        message = activation.get("message", "")
                        
                        print(f"🎉 成功获取激活码！")
                        print(f"   激活码: {activation_code}")
                        print(f"   消息: {message}")
                        print()
                        print(f"📱 下一步操作:")
                        print(f"1. 打开管理面板: http://47.122.144.73:8002")
                        print(f"2. 使用激活码 {activation_code} 进行设备绑定")
                        print(f"3. 绑定成功后，设备将获得WebSocket连接信息")
                        return True
                        
                    # 检查WebSocket（已绑定的设备）
                    elif "websocket" in result:
                        websocket = result["websocket"]
                        websocket_url = websocket.get("url", "未知")
                        
                        print(f"✅ 设备已绑定！")
                        print(f"   WebSocket URL: {websocket_url}")
                        print(f"   可以直接使用语音功能")
                        return True
                        
                    # 检查错误信息
                    elif "error" in result:
                        error_msg = result["error"]
                        print(f"❌ OTA请求被拒绝: {error_msg}")
                        
                        if error_msg == "Invalid OTA request":
                            print(f"📋 可能的原因（已检查）:")
                            print(f"   ✓ Device-Id与macAddress一致性")
                            print(f"   ✓ application字段存在")  
                            print(f"   ✓ MAC地址格式正确")
                            print(f"   ❓ 可能是服务器端其他验证失败")
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
    print("🚀 小智Android OTA配置修复验证")
    print("=" * 70)
    print("严格按照OTAController.java验证逻辑测试")
    print("确保满足所有Java后端验证要求")
    print()
    
    # 测试OTA
    ota_success = test_ota_correct_format()
    
    # 测试WebSocket
    ws_success = test_websocket_connectivity()
    
    # 总结
    print(f"\n📊 最终测试结果")
    print("=" * 30)
    print(f"OTA绑定测试: {'✅ 通过' if ota_success else '❌ 失败'}")
    print(f"WebSocket测试: {'✅ 通过' if ws_success else '❌ 失败'}")
    
    if ota_success and ws_success:
        print(f"\n🎉 OTA配置修复成功！")
        print(f"现在Android应用应该能够:")
        print(f"1. ✅ 正确生成和验证设备ID")
        print(f"2. ✅ 发送符合Java后端验证的OTA请求")
        print(f"3. ✅ 获取激活码或WebSocket连接信息")
        print(f"4. ✅ 成功建立与服务器的通信")
        
        print(f"\n📋 关键修复点总结:")
        print(f"• Device-Id头部与macAddress字段严格一致")
        print(f"• application字段必须存在且包含version")
        print(f"• MAC地址格式符合正则表达式验证")
        print(f"• 使用正确的OTA端点 /xiaozhi/ota/")
    else:
        print(f"\n⚠️ 仍需调试:")
        if not ota_success:
            print(f"- OTA请求格式或服务器验证有问题")
        if not ws_success:
            print(f"- WebSocket服务不可用")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 