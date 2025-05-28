#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤1测试：验证OTA配置获取功能
测试新的OTA管理器是否能正确获取WebSocket配置
"""

import requests
import json
import uuid
import time
from datetime import datetime

class OtaConfigTest:
    def __init__(self):
        self.ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
        self.websocket_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
        
    def generate_device_id(self):
        """生成MAC地址格式的设备ID"""
        uuid_str = str(uuid.uuid4()).replace("-", "")
        mac_format = uuid_str[:12].upper()
        return f"{mac_format[0:2]}:{mac_format[2:4]}:{mac_format[4:6]}:{mac_format[6:8]}:{mac_format[8:10]}:{mac_format[10:12]}"
    
    def test_ota_config_fetch(self):
        """测试OTA配置获取"""
        print("🔧 步骤1测试：OTA配置获取功能")
        print("=" * 50)
        
        device_id = self.generate_device_id()
        client_id = str(uuid.uuid4())
        
        print(f"📱 测试设备ID: {device_id}")
        print(f"🆔 客户端ID: {client_id}")
        print(f"🌐 OTA URL: {self.ota_url}")
        
        # 构建请求数据（与Android端一致）
        request_data = {
            "application": {
                "version": "1.0.0",
                "name": "xiaozhi-android"
            },
            "macAddress": device_id,
            "board": {
                "type": "android"
            },
            "chipModelName": "android"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Device-Id": device_id,
            "Client-Id": client_id
        }
        
        try:
            print("\n📤 发送OTA配置请求...")
            print(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
            
            response = requests.post(
                self.ota_url,
                json=request_data,
                headers=headers,
                timeout=10
            )
            
            print(f"\n📥 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OTA配置获取成功")
                print(f"📋 响应内容:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 分析响应内容
                self.analyze_ota_response(result)
                return True
                
            else:
                print(f"❌ OTA配置获取失败: {response.status_code}")
                print(f"错误响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OTA配置获取异常: {e}")
            return False
    
    def analyze_ota_response(self, result):
        """分析OTA响应内容"""
        print("\n🔍 OTA响应分析:")
        print("-" * 30)
        
        # 检查WebSocket配置
        if "websocket" in result:
            websocket_config = result["websocket"]
            websocket_url = websocket_config.get("url")
            print(f"✅ 发现WebSocket配置")
            print(f"   URL: {websocket_url}")
            
            # 验证URL格式
            if websocket_url == self.websocket_url:
                print(f"✅ WebSocket URL匹配预期")
            else:
                print(f"⚠️ WebSocket URL不匹配预期")
                print(f"   预期: {self.websocket_url}")
                print(f"   实际: {websocket_url}")
                
        else:
            print("❌ 未找到WebSocket配置")
        
        # 检查激活信息
        if "activation" in result:
            activation = result["activation"]
            activation_code = activation.get("code")
            activation_message = activation.get("message")
            print(f"🔑 发现激活信息")
            print(f"   激活码: {activation_code}")
            print(f"   消息: {activation_message}")
            
            # 提取管理面板URL
            if activation_message:
                lines = activation_message.split('\n')
                for line in lines:
                    if line.startswith('http'):
                        print(f"🌐 管理面板: {line}")
                        
        else:
            print("ℹ️ 无激活信息（设备可能已绑定）")
        
        # 检查服务器时间
        if "server_time" in result:
            server_time = result["server_time"]
            timestamp = server_time.get("timestamp")
            if timestamp:
                readable_time = datetime.fromtimestamp(timestamp / 1000)
                print(f"⏰ 服务器时间: {readable_time}")
        
        # 检查固件信息
        if "firmware" in result:
            firmware = result["firmware"]
            version = firmware.get("version")
            print(f"💿 固件版本: {version}")
    
    def test_websocket_endpoint(self):
        """测试WebSocket端点可达性"""
        print("\n🌐 测试WebSocket端点可达性...")
        
        # 转换为HTTP URL进行基础测试
        http_url = self.websocket_url.replace("ws://", "http://")
        
        try:
            response = requests.get(http_url, timeout=5)
            print(f"✅ WebSocket端点可达 (HTTP {response.status_code})")
            if response.text:
                print(f"📝 响应内容: {response.text[:100]}...")
            return True
        except Exception as e:
            print(f"❌ WebSocket端点不可达: {e}")
            return False
    
    def generate_test_report(self, ota_success, ws_success):
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# 🔧 步骤1测试报告 - OTA配置获取

## 📊 测试结果
- **测试时间**: {timestamp}
- **OTA配置获取**: {'✅ 成功' if ota_success else '❌ 失败'}
- **WebSocket端点**: {'✅ 可达' if ws_success else '❌ 不可达'}

## 🎯 测试目标
验证新的OTA配置管理器能够：
1. 成功连接到 `{self.ota_url}`
2. 获取WebSocket配置 `{self.websocket_url}`
3. 处理设备激活流程
4. 缓存配置信息

## 📋 测试配置
- **OTA URL**: {self.ota_url}
- **WebSocket URL**: {self.websocket_url}
- **设备类型**: Android
- **应用版本**: 1.0.0

## 🔄 下一步
{'如果测试成功，可以进入步骤2：验证OTA配置正常工作' if ota_success and ws_success else '需要检查服务器连接或配置'}

## 📝 注意事项
- OTA配置获取不影响现有STT功能
- WebSocket URL将在步骤3中集成到STT启动流程
- 当前阶段仅测试配置获取机制
"""
        
        report_path = f"../Work_Framework/step1_ota_test_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📋 测试报告已生成: {report_path}")
        return report_path

def main():
    """主测试函数"""
    print("🎯 开始步骤1测试：OTA配置获取功能验证")
    print("=" * 60)
    
    tester = OtaConfigTest()
    
    # 测试OTA配置获取
    ota_success = tester.test_ota_config_fetch()
    
    # 测试WebSocket端点
    ws_success = tester.test_websocket_endpoint()
    
    # 生成测试报告
    report_path = tester.generate_test_report(ota_success, ws_success)
    
    print("\n🏁 步骤1测试完成")
    print("=" * 60)
    
    if ota_success and ws_success:
        print("✅ 步骤1测试全部成功！")
        print("🔄 准备进入步骤2：验证OTA配置正常工作")
    else:
        print("❌ 步骤1测试发现问题，需要检查配置")
    
    return ota_success and ws_success

if __name__ == "__main__":
    main() 