#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智Android应用绑定状态调试工具
分析为什么应用跳过绑定流程直接进入聊天界面
"""

import subprocess
import json
import time
import requests

class BindingStateDebugger:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
        self.ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    def check_app_preferences(self):
        """检查应用的SharedPreferences和DataStore"""
        print("🔍 检查应用存储的配置...")
        
        try:
            # 尝试读取应用的私有数据（需要root权限）
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "run-as", self.package_name, "ls", "-la"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 应用数据目录内容:")
                print(result.stdout)
                
                # 检查DataStore文件
                datastore_result = subprocess.run(
                    ["adb", "-s", self.device_id, "shell", "run-as", self.package_name, 
                     "find", ".", "-name", "*device_config*"],
                    capture_output=True,
                    text=True
                )
                
                if datastore_result.returncode == 0 and datastore_result.stdout.strip():
                    print("📁 找到设备配置文件:")
                    print(datastore_result.stdout)
                else:
                    print("❌ 未找到设备配置文件")
            else:
                print("❌ 无法访问应用数据目录（需要root权限或调试版本）")
                
        except Exception as e:
            print(f"❌ 检查应用配置失败: {e}")
    
    def simulate_ota_request(self):
        """模拟应用的OTA请求"""
        print("\n🌐 模拟Android应用的OTA请求...")
        
        # 构建与Android应用相同的请求
        request_data = {
            "macAddress": "AA:BB:CC:DD:EE:FF",  # 模拟设备ID
            "chipModelName": "android",
            "application": {
                "version": "1.0.0",
                "name": "xiaozhi-android",
                "compile_time": "2025-01-27 12:00:00"
            },
            "board": {
                "type": "android",
                "manufacturer": "TestDevice",
                "model": "TestModel",
                "version": "14"
            },
            "uuid": "android-app-test-12345"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Device-Id": "AA:BB:CC:DD:EE:FF",
            "Client-Id": "android-app-test-12345"
        }
        
        try:
            print(f"📤 发送OTA请求到: {self.ota_url}")
            print(f"📋 请求数据: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                self.ota_url,
                json=request_data,
                headers=headers,
                timeout=10
            )
            
            print(f"\n📥 服务器响应:")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # 分析响应内容
                    self.analyze_ota_response(result)
                    
                except json.JSONDecodeError:
                    print(f"   响应文本: {response.text}")
            else:
                print(f"   错误响应: {response.text}")
                
        except Exception as e:
            print(f"❌ OTA请求失败: {e}")
    
    def analyze_ota_response(self, response):
        """分析OTA响应，找出问题所在"""
        print(f"\n🔍 分析OTA响应...")
        
        has_activation = "activation" in response
        has_websocket = "websocket" in response
        
        print(f"   包含激活码: {has_activation}")
        print(f"   包含WebSocket: {has_websocket}")
        
        if has_activation and has_websocket:
            print("\n⚠️ 关键发现：服务器同时返回了激活码和WebSocket配置！")
            print("这可能是问题的根源：")
            print("1. 服务器返回激活码表示设备需要绑定")
            print("2. 但同时返回WebSocket URL")
            print("3. Android应用的OtaResult.isActivated判断逻辑：")
            print("   val isActivated: Boolean get() = websocketConfig != null")
            print("4. 因为有websocketConfig，所以isActivated=true")
            print("5. 应用错误地认为设备已激活，跳过绑定流程")
            print("6. 直接进入聊天界面，但实际上设备未绑定")
            
            activation_code = response.get("activation", {}).get("code", "")
            websocket_url = response.get("websocket", {}).get("url", "")
            
            print(f"\n📋 详细信息:")
            print(f"   激活码: {activation_code}")
            print(f"   WebSocket URL: {websocket_url}")
            
            return "CONFLICTING_RESPONSE"
            
        elif has_activation:
            activation_code = response.get("activation", {}).get("code", "")
            print(f"\n✅ 正常：只有激活码，激活码: {activation_code}")
            return "NEEDS_ACTIVATION"
            
        elif has_websocket:
            websocket_url = response.get("websocket", {}).get("url", "")
            print(f"\n✅ 正常：只有WebSocket，URL: {websocket_url}")
            return "ALREADY_ACTIVATED"
            
        else:
            print(f"\n❌ 异常：既没有激活码也没有WebSocket配置")
            return "INVALID_RESPONSE"
    
    def check_app_logs(self):
        """检查应用日志中的关键信息"""
        print("\n📋 检查应用日志...")
        
        try:
            # 清除旧日志
            subprocess.run(["adb", "-s", self.device_id, "logcat", "-c"], capture_output=True)
            
            # 启动应用
            print("🚀 启动应用...")
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", f"{self.package_name}/.MainActivity"],
                capture_output=True
            )
            
            # 等待应用初始化
            time.sleep(5)
            
            # 获取相关日志
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "ActivationManager:*", "ChatViewModel:*", "OtaResult:*", 
                 "DeviceConfigManager:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                if logs:
                    print("📋 关键日志:")
                    for line in logs.split('\n')[-20:]:  # 最后20行
                        if any(keyword in line for keyword in ["激活", "绑定", "WebSocket", "OTA", "isActivated"]):
                            print(f"   {line}")
                else:
                    print("❌ 未找到相关日志")
            else:
                print("❌ 获取日志失败")
                
        except Exception as e:
            print(f"❌ 检查日志失败: {e}")
    
    def suggest_fixes(self):
        """建议修复方案"""
        print(f"\n💡 修复建议:")
        print("=" * 50)
        
        print("🎯 问题根源：")
        print("   OtaResult.isActivated的判断逻辑有问题")
        print("   当前逻辑：val isActivated: Boolean get() = websocketConfig != null")
        print("   问题：服务器可能同时返回activation和websocket字段")
        
        print("\n🔧 修复方案1：修改判断逻辑")
        print("   修改OtaResult.kt中的isActivated逻辑：")
        print("   val isActivated: Boolean get() = websocketConfig != null && activation == null")
        print("   或者：")
        print("   val isActivated: Boolean get() = websocketConfig != null && !needsActivation")
        
        print("\n🔧 修复方案2：修改ActivationManager逻辑")
        print("   在handleOtaResult方法中优先检查activation字段：")
        print("   if (otaResult.needsActivation) { // 优先处理需要激活的情况")
        print("       // 即使有websocket配置也要先完成激活")
        print("   }")
        
        print("\n🔧 修复方案3：清除本地状态")
        print("   清除应用的本地绑定状态，强制重新检查：")
        print("   1. 在设备配置界面点击'清除所有配置'")
        print("   2. 重启应用")
        print("   3. 观察是否正确显示绑定流程")
        
        print("\n🚀 立即测试方案：")
        print("   1. 修改OTA URL指向本地测试服务器")
        print("   2. 本地服务器只返回activation字段，不返回websocket")
        print("   3. 验证应用是否正确显示绑定界面")
    
    def run_complete_diagnosis(self):
        """运行完整诊断"""
        print("🔍 小智Android应用绑定状态诊断")
        print("=" * 60)
        
        # 1. 检查应用配置
        self.check_app_preferences()
        
        # 2. 模拟OTA请求
        self.simulate_ota_request()
        
        # 3. 检查应用日志
        self.check_app_logs()
        
        # 4. 提供修复建议
        self.suggest_fixes()

def main():
    debugger = BindingStateDebugger()
    debugger.run_complete_diagnosis()

if __name__ == "__main__":
    main() 