#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智Android应用配置检查工具
检查应用当前的配置状态，包括OTA URL、设备ID、绑定状态等
"""

import subprocess
import json
import time

class AppConfigChecker:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
    
    def check_app_running(self):
        """检查应用是否在运行"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "ps", "|", "grep", self.package_name],
                capture_output=True,
                text=True,
                shell=True
            )
            return self.package_name in result.stdout
        except Exception as e:
            print(f"检查应用运行状态失败: {e}")
            return False
    
    def get_app_data_info(self):
        """获取应用数据目录信息"""
        try:
            # 检查应用数据目录
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "ls", "-la", f"/data/data/{self.package_name}/"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return "无法访问应用数据目录（需要root权限）"
        except Exception as e:
            return f"获取应用数据失败: {e}"
    
    def check_shared_preferences(self):
        """检查SharedPreferences配置"""
        try:
            # 尝试读取SharedPreferences文件
            prefs_path = f"/data/data/{self.package_name}/shared_prefs/"
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "ls", "-la", prefs_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return "无法访问SharedPreferences（需要root权限）"
        except Exception as e:
            return f"检查SharedPreferences失败: {e}"
    
    def get_app_logs(self, lines=50):
        """获取应用相关日志"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time", 
                 f"{self.package_name}:*", "VApplication:*", "MainActivity:*",
                 "ChatViewModel:*", "ActivationManager:*", "Ota:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines_list = result.stdout.strip().split('\n')
                return '\n'.join(lines_list[-lines:]) if lines_list else "无日志"
            else:
                return "获取日志失败"
        except Exception as e:
            return f"获取日志异常: {e}"
    
    def check_network_connectivity(self):
        """检查网络连接"""
        test_urls = [
            "http://47.122.144.73:8002",
            "http://47.122.144.73:8000",
            "https://www.baidu.com"
        ]
        
        results = {}
        for url in test_urls:
            try:
                result = subprocess.run(
                    ["adb", "-s", self.device_id, "shell", "ping", "-c", "1", "-W", "3", 
                     url.replace("http://", "").replace("https://", "").split("/")[0]],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                results[url] = "✅ 可达" if result.returncode == 0 else "❌ 不可达"
            except subprocess.TimeoutExpired:
                results[url] = "⏰ 超时"
            except Exception as e:
                results[url] = f"❌ 错误: {e}"
        
        return results
    
    def trigger_ota_check(self):
        """尝试触发OTA检查（通过UI自动化）"""
        try:
            # 启动应用
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", f"{self.package_name}/.MainActivity"],
                capture_output=True
            )
            
            time.sleep(3)
            
            # 尝试点击设置按钮（如果存在）
            # 这需要根据实际UI布局调整
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "input", "tap", "50", "50"],
                capture_output=True
            )
            
            return "已尝试触发OTA检查，请查看应用界面"
        except Exception as e:
            return f"触发OTA检查失败: {e}"
    
    def run_comprehensive_check(self):
        """运行完整检查"""
        print("🔍 小智Android应用配置检查")
        print("=" * 60)
        
        # 1. 检查应用运行状态
        print("📱 应用运行状态:")
        is_running = self.check_app_running()
        if is_running:
            print("  ✅ 应用正在运行")
        else:
            print("  ❌ 应用未运行")
            print("  🚀 正在启动应用...")
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", f"{self.package_name}/.MainActivity"],
                capture_output=True
            )
            time.sleep(3)
        
        print()
        
        # 2. 检查网络连接
        print("🌐 网络连接检查:")
        connectivity = self.check_network_connectivity()
        for url, status in connectivity.items():
            print(f"  {url}: {status}")
        
        print()
        
        # 3. 检查应用数据
        print("📁 应用数据目录:")
        app_data = self.get_app_data_info()
        print(f"  {app_data}")
        
        print()
        
        # 4. 检查SharedPreferences
        print("⚙️ SharedPreferences:")
        prefs = self.check_shared_preferences()
        print(f"  {prefs}")
        
        print()
        
        # 5. 获取最近日志
        print("📋 最近应用日志:")
        logs = self.get_app_logs(20)
        if logs and logs != "无日志":
            print("  最近20条相关日志:")
            for line in logs.split('\n')[-10:]:  # 只显示最后10条
                if line.strip():
                    print(f"    {line}")
        else:
            print("  无相关日志")
        
        print()
        
        # 6. 建议下一步操作
        print("💡 建议操作:")
        print("  1. 在应用中查看设备配置界面")
        print("  2. 检查OTA URL设置是否为: http://47.122.144.73:8002/xiaozhi/ota/")
        print("  3. 手动点击'检查更新'按钮")
        print("  4. 观察是否显示激活码或错误信息")
        
        print()
        print("🔧 如需手动触发OTA检查，请运行:")
        print(f"  python3 {__file__} --trigger-ota")

def main():
    import sys
    
    checker = AppConfigChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--trigger-ota":
        print("🚀 触发OTA检查...")
        result = checker.trigger_ota_check()
        print(f"结果: {result}")
    else:
        checker.run_comprehensive_check()

if __name__ == "__main__":
    main() 