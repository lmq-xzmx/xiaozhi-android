#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智Android应用配置更新工具
将应用配置指向本地测试服务器
"""

import subprocess
import time
import json

class AppConfigUpdater:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
        self.local_ota_url = "http://10.0.2.2:8002/xiaozhi/ota/"  # Android模拟器访问主机的地址
        self.local_websocket_url = "ws://10.0.2.2:8000/xiaozhi/v1/"
    
    def get_device_ip(self):
        """获取设备IP地址"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "ip", "route", "get", "1"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # 解析输出获取网关IP
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'via' in line:
                        parts = line.split()
                        if 'via' in parts:
                            gateway_idx = parts.index('via') + 1
                            if gateway_idx < len(parts):
                                gateway_ip = parts[gateway_idx]
                                print(f"检测到网关IP: {gateway_ip}")
                                return gateway_ip
            
            # 如果无法获取，使用默认值
            print("无法获取网关IP，使用默认配置")
            return "10.0.2.2"  # Android模拟器默认主机地址
            
        except Exception as e:
            print(f"获取设备IP失败: {e}")
            return "10.0.2.2"
    
    def update_ota_url(self, new_url):
        """通过UI自动化更新OTA URL"""
        print(f"🔧 更新OTA URL为: {new_url}")
        
        try:
            # 1. 启动应用
            print("  1. 启动应用...")
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", f"{self.package_name}/.MainActivity"],
                capture_output=True
            )
            time.sleep(3)
            
            # 2. 尝试打开设置界面（这需要根据实际UI调整）
            print("  2. 尝试打开设置界面...")
            
            # 获取屏幕尺寸
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "wm", "size"],
                capture_output=True,
                text=True
            )
            
            if "Physical size:" in result.stdout:
                size_line = result.stdout.split("Physical size:")[1].strip()
                width, height = map(int, size_line.split('x'))
                print(f"  屏幕尺寸: {width}x{height}")
                
                # 尝试点击右上角的设置按钮（假设位置）
                settings_x = width - 100
                settings_y = 100
                
                subprocess.run(
                    ["adb", "-s", self.device_id, "shell", "input", "tap", str(settings_x), str(settings_y)],
                    capture_output=True
                )
                time.sleep(2)
                
                print("  3. 已尝试点击设置按钮")
                print("  💡 请手动在应用中:")
                print(f"     - 打开设备配置界面")
                print(f"     - 将OTA URL修改为: {new_url}")
                print(f"     - 点击保存")
                print(f"     - 点击'检查更新'测试连接")
                
                return True
            else:
                print("  ❌ 无法获取屏幕尺寸")
                return False
                
        except Exception as e:
            print(f"  ❌ 更新配置失败: {e}")
            return False
    
    def test_local_connection(self):
        """测试本地连接"""
        print("🔍 测试本地服务器连接...")
        
        # 从设备测试连接
        try:
            # 测试HTTP连接
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "curl", "-m", "5", "http://10.0.2.2:8002/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "小智本地测试服务器运行中" in result.stdout:
                print("  ✅ 设备可以访问本地服务器")
                return True
            else:
                print("  ❌ 设备无法访问本地服务器")
                print(f"  响应: {result.stdout}")
                print(f"  错误: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ 连接测试失败: {e}")
            return False
    
    def create_config_guide(self):
        """创建配置指南"""
        print("\n📋 配置指南:")
        print("=" * 50)
        
        device_ip = self.get_device_ip()
        ota_url = f"http://{device_ip}:8002/xiaozhi/ota/"
        websocket_url = f"ws://{device_ip}:8000/xiaozhi/v1/"
        
        print("1. **在Android应用中手动配置**:")
        print("   - 打开应用")
        print("   - 进入设备配置界面")
        print(f"   - 将OTA URL设置为: {ota_url}")
        print("   - 保存配置")
        print("   - 点击'检查更新'")
        
        print("\n2. **预期结果**:")
        print("   - 应该显示6位激活码")
        print("   - 激活码格式类似: 170793")
        print("   - 提示访问管理面板进行绑定")
        
        print("\n3. **如果连接失败**:")
        print("   - 检查本地服务器是否运行")
        print("   - 确认设备网络连接")
        print("   - 尝试使用其他IP地址")
        
        print(f"\n4. **替代IP地址**:")
        print(f"   - 模拟器: http://10.0.2.2:8002/xiaozhi/ota/")
        print(f"   - 真机(WiFi): http://192.168.1.x:8002/xiaozhi/ota/")
        print(f"   - 本地回环: http://127.0.0.1:8002/xiaozhi/ota/")
        
        return ota_url, websocket_url
    
    def run_update_process(self):
        """运行完整的更新流程"""
        print("🔧 小智Android应用配置更新工具")
        print("=" * 60)
        
        # 1. 测试本地服务器连接
        if not self.test_local_connection():
            print("\n⚠️ 警告: 设备无法访问本地服务器")
            print("请确保:")
            print("- 本地测试服务器正在运行")
            print("- 设备和电脑在同一网络")
            print("- 防火墙允许端口8002访问")
        
        # 2. 创建配置指南
        ota_url, websocket_url = self.create_config_guide()
        
        # 3. 尝试自动更新（可能需要手动操作）
        print("\n🚀 尝试自动打开应用...")
        self.update_ota_url(ota_url)
        
        print("\n" + "=" * 60)
        print("🎯 下一步:")
        print("1. 在应用中手动配置OTA URL")
        print("2. 测试OTA连接")
        print("3. 观察是否显示激活码")
        print("4. 如果成功，应用状态应该从'Idle'变为显示激活码")

def main():
    updater = AppConfigUpdater()
    updater.run_update_process()

if __name__ == "__main__":
    main() 