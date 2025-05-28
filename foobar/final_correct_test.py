#!/usr/bin/env python3
"""
最终修复版本：使用正确的JsonProperty字段名
关键发现：DeviceReportReqDTO.java使用@JsonProperty注解
- mac_address (不是macAddress)
- chip_model_name (不是chipModelName) 
"""

import urllib.request
import json
import uuid
import time
import re
from datetime import datetime

def validate_mac_address(mac_address):
    """验证MAC地址格式"""
    if not mac_address:
        return False
    mac_pattern = r"^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$"
    return bool(re.match(mac_pattern, mac_address))

def generate_valid_mac():
    """生成有效MAC地址"""
    mac_bytes = []
    for i in range(6):
        mac_bytes.append(f"{(hash(str(time.time() + i)) % 256):02x}")
    return ":".join(mac_bytes).upper()

def test_final_correct_format():
    """使用正确的JsonProperty字段名测试"""
    print("🔧 最终修复测试：使用正确的JsonProperty字段名")
    print("=" * 70)
    
    # 生成测试数据
    device_mac = generate_valid_mac()
    client_id = f"android-app-{int(time.time())}"
    test_uuid = str(uuid.uuid4())
    
    print(f"📱 设备MAC: {device_mac}")
    print(f"🔑 客户端ID: {client_id}")
    print(f"🆔 UUID: {test_uuid}")
    print(f"✅ MAC格式验证: {'通过' if validate_mac_address(device_mac) else '失败'}")
    print()
    
    # 关键修复：使用@JsonProperty注解的字段名
    request_data = {
        # 关键1：使用JsonProperty字段名 mac_address
        "mac_address": device_mac,  # 不是macAddress！
        
        # 关键2：application必须存在
        "application": {
            "version": "1.0.0",
            "name": "xiaozhi-android",
            "compile_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        
        # 关键3：使用JsonProperty字段名 chip_model_name
        "chip_model_name": "android",  # 不是chipModelName！
        
        # 可选但建议的字段
        "board": {
            "type": "android",
            "manufacturer": "TestManufacturer", 
            "model": "TestModel"
        },
        
        "uuid": test_uuid,
        "version": 2,
        "flash_size": 8388608,
        "minimum_free_heap_size": 250000
    }
    
    # 请求头：Device-Id必须与mac_address一致
    headers = {
        'Content-Type': 'application/json',
        'Device-Id': device_mac,  # 必须与mac_address完全一致
        'Client-Id': client_id
    }
    
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    print(f"🌐 OTA服务地址: {ota_url}")
    print(f"🔧 关键修复点:")
    print(f"   ✓ 使用 mac_address 而不是 macAddress")
    print(f"   ✓ 使用 chip_model_name 而不是 chipModelName")
    print(f"   ✓ Device-Id 与 mac_address 一致: {device_mac}")
    print(f"   ✓ application 字段存在")
    print()
    
    print(f"📤 发送请求:")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求体: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        # 发送请求
        data = json.dumps(request_data).encode('utf-8')
        req = urllib.request.Request(ota_url, data=data, headers=headers, method='POST')
        
        print("🔄 发送OTA请求...")
        
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
                    
                    # 检查激活码（新设备）
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
                        return True
                        
                    # 检查WebSocket（已绑定设备）
                    elif "websocket" in result:
                        websocket = result["websocket"]
                        websocket_url = websocket.get("url", "未知")
                        
                        print(f"✅ 设备已绑定！")
                        print(f"   WebSocket URL: {websocket_url}")
                        return True
                        
                    # 检查错误
                    elif "error" in result:
                        error_msg = result["error"]
                        print(f"❌ 仍然失败: {error_msg}")
                        
                        if error_msg == "Invalid OTA request":
                            print(f"🔍 已修复的问题:")
                            print(f"   ✓ JsonProperty字段名 (mac_address, chip_model_name)")
                            print(f"   ✓ Device-Id与mac_address一致性")
                            print(f"   ✓ application字段存在")
                            print(f"   ✓ MAC地址格式正确")
                            print(f"   ❓ 可能还有其他未知验证要求")
                        return False
                        
                    else:
                        print(f"❓ 未知响应格式")
                        print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"❌ 响应不是有效JSON: {response_data}")
                    return False
            else:
                print(f"❌ HTTP错误 (状态码: {status_code})")
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 小智Android OTA最终修复测试")
    print("=" * 80)
    print("使用正确的JsonProperty字段名格式")
    print("基于DeviceReportReqDTO.java的@JsonProperty注解")
    print()
    
    success = test_final_correct_format()
    
    print(f"\n📊 最终结果")
    print("=" * 30)
    print(f"OTA测试: {'✅ 成功' if success else '❌ 失败'}")
    
    if success:
        print(f"\n🎉 问题已解决！")
        print(f"关键修复点:")
        print(f"• 使用正确的JsonProperty字段名")
        print(f"• mac_address (不是macAddress)")
        print(f"• chip_model_name (不是chipModelName)")
        print(f"• Device-Id头部与mac_address严格一致")
        print(f"• application字段必须存在")
    else:
        print(f"\n⚠️ 可能还需要进一步调试")
        print(f"建议检查服务器端日志或添加更多调试信息")
    
    print(f"\n🏁 测试完成")

if __name__ == "__main__":
    main() 