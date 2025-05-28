#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能绑定流程测试脚本
验证完整的设备绑定体验，包括：
1. 设备初始化检查
2. 激活码获取
3. 绑定状态轮询
4. 绑定完成验证
"""

import requests
import json
import time
import random
import string
import uuid
from typing import Dict, Any, Optional

class SmartBindingTester:
    def __init__(self, base_url: str = "http://47.122.144.73:8002"):
        self.base_url = base_url
        self.ota_url = f"{base_url}/xiaozhi/ota/"
        self.device_id = self.generate_device_id()
        self.client_id = f"android-test-{int(time.time())}"
        self.session = requests.Session()
        
    def generate_device_id(self) -> str:
        """生成测试用的设备ID（MAC地址格式）"""
        mac_parts = []
        for _ in range(6):
            part = ''.join(random.choices('0123456789ABCDEF', k=2))
            mac_parts.append(part)
        return ':'.join(mac_parts)
    
    def create_ota_request(self) -> Dict[str, Any]:
        """创建Android标准OTA请求（使用下划线命名）"""
        return {
            # 使用下划线命名（与成功的请求格式一致）
            "mac_address": self.device_id,
            "chip_model_name": "android",
            
            # application对象结构
            "application": {
                "version": "1.0.0"
            },
            
            # 设备信息
            "board": {
                "type": "android"
            }
        }
    
    def send_ota_request(self) -> Optional[Dict[str, Any]]:
        """发送OTA请求"""
        headers = {
            "Content-Type": "application/json",
            "Device-Id": self.device_id,
            "Client-Id": self.client_id,
            "X-Language": "Chinese"
        }
        
        payload = self.create_ota_request()
        
        try:
            print(f"📡 发送OTA请求到: {self.ota_url}")
            print(f"🆔 设备ID: {self.device_id}")
            print(f"🔧 客户端ID: {self.client_id}")
            print(f"📦 请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = self.session.post(
                self.ota_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            print(f"📊 响应状态: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("❌ 响应不是有效的JSON格式")
                    return None
            else:
                print(f"❌ 请求失败: {response.status_code}")
                if response.text:
                    try:
                        error_data = response.json()
                        print(f"📄 错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"📄 错误内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"💥 请求异常: {e}")
            return None
    
    def test_device_initialization(self) -> bool:
        """测试设备初始化流程"""
        print("\n" + "="*60)
        print("🚀 测试1: 设备初始化检查")
        print("="*60)
        
        response = self.send_ota_request()
        if not response:
            print("❌ 设备初始化失败")
            return False
        
        # 检查是否获得激活码
        if "activation" in response and "code" in response["activation"]:
            activation_code = response["activation"]["code"]
            print(f"✅ 获得激活码: {activation_code}")
            print(f"📱 绑定消息: {response['activation'].get('message', '')}")
            self.activation_code = activation_code
            return True
        elif "websocket" in response and "url" in response["websocket"]:
            print(f"✅ 设备已绑定，WebSocket URL: {response['websocket']['url']}")
            return True
        else:
            print("❌ 响应格式异常")
            return False
    
    def simulate_user_binding(self, activation_code: str) -> bool:
        """模拟用户在管理面板完成绑定"""
        print(f"\n📱 模拟用户绑定流程:")
        print(f"   1. 用户打开管理面板: {self.base_url}/#/home")
        print(f"   2. 用户点击'新增设备'")
        print(f"   3. 用户输入激活码: {activation_code}")
        print(f"   4. 用户完成绑定操作")
        print(f"   ⏳ 等待用户操作完成...")
        
        # 这里可以添加实际的管理面板API调用来模拟绑定
        # 目前只是等待一段时间模拟用户操作
        time.sleep(5)
        return True
    
    def test_binding_polling(self, max_attempts: int = 10) -> bool:
        """测试绑定状态轮询"""
        print("\n" + "="*60)
        print("🔄 测试2: 绑定状态轮询检查")
        print("="*60)
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔍 轮询检查 {attempt}/{max_attempts}")
            
            response = self.send_ota_request()
            if not response:
                print(f"⚠️ 第{attempt}次检查失败，继续重试...")
                time.sleep(3)
                continue
            
            # 检查是否绑定成功
            if "websocket" in response and "url" in response["websocket"]:
                websocket_url = response["websocket"]["url"]
                print(f"🎉 绑定成功！WebSocket URL: {websocket_url}")
                return True
            elif "activation" in response:
                activation_code = response["activation"].get("code", "")
                print(f"⏳ 仍需绑定，激活码: {activation_code}")
                
                # 如果是第一次检查，模拟用户绑定
                if attempt == 1 and hasattr(self, 'activation_code'):
                    self.simulate_user_binding(self.activation_code)
            
            # 等待下次检查
            if attempt < max_attempts:
                print(f"⏰ 等待15秒后进行下次检查...")
                time.sleep(15)
        
        print(f"⏰ 轮询超时，未检测到绑定完成")
        return False
    
    def test_bound_device_behavior(self) -> bool:
        """测试已绑定设备的行为"""
        print("\n" + "="*60)
        print("✅ 测试3: 已绑定设备行为验证")
        print("="*60)
        
        response = self.send_ota_request()
        if not response:
            print("❌ 无法获取设备状态")
            return False
        
        if "websocket" in response and "url" in response["websocket"]:
            websocket_url = response["websocket"]["url"]
            print(f"✅ 设备已绑定，直接返回WebSocket连接")
            print(f"🔗 WebSocket URL: {websocket_url}")
            print(f"📊 服务器时间: {response.get('server_time', {})}")
            return True
        else:
            print("❌ 设备绑定状态异常")
            return False
    
    def run_complete_test(self) -> bool:
        """运行完整的智能绑定测试"""
        print("🎯 开始智能绑定流程完整测试")
        print(f"🆔 测试设备ID: {self.device_id}")
        
        # 测试1: 设备初始化
        if not self.test_device_initialization():
            return False
        
        # 如果设备已绑定，直接验证绑定行为
        if not hasattr(self, 'activation_code'):
            return self.test_bound_device_behavior()
        
        # 测试2: 绑定状态轮询
        if not self.test_binding_polling():
            print("❌ 绑定轮询测试失败")
            return False
        
        # 测试3: 验证绑定后的行为
        if not self.test_bound_device_behavior():
            print("❌ 绑定后行为验证失败")
            return False
        
        print("\n" + "="*60)
        print("🎉 智能绑定流程测试完成！")
        print("="*60)
        print("✅ 所有测试通过")
        print(f"🆔 设备ID: {self.device_id}")
        print(f"🔗 可以开始使用语音功能")
        
        return True

def main():
    """主函数"""
    print("🤖 小智Android智能绑定流程测试")
    print("=" * 60)
    
    tester = SmartBindingTester()
    
    try:
        success = tester.run_complete_test()
        if success:
            print("\n✅ 测试成功完成！")
            exit(0)
        else:
            print("\n❌ 测试失败！")
            exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        exit(1)

if __name__ == "__main__":
    main() 