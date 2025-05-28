#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试WebSocket连接修复效果
验证应用是否正确建立WebSocket连接
"""

import subprocess
import time
import json

class WebSocketFixTester:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
    
    def rebuild_and_install(self):
        """重新构建并安装APK"""
        print("🔧 重新构建APK...")
        
        try:
            # 构建APK
            result = subprocess.run(
                ["./gradlew", "assembleDebug"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode != 0:
                print(f"❌ 构建失败: {result.stderr}")
                return False
            
            print("✅ APK构建成功")
            
            # 安装APK
            install_result = subprocess.run(
                ["adb", "-s", self.device_id, "install", "-r", 
                 "app/build/outputs/apk/debug/app-debug.apk"],
                capture_output=True,
                text=True
            )
            
            if install_result.returncode != 0:
                print(f"❌ 安装失败: {install_result.stderr}")
                return False
            
            print("✅ APK安装成功")
            return True
            
        except Exception as e:
            print(f"❌ 构建安装过程失败: {e}")
            return False
    
    def clear_app_data(self):
        """清除应用数据"""
        print("🧹 清除应用数据...")
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "pm", "clear", self.package_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 应用数据已清除")
                return True
            else:
                print(f"❌ 清除失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 清除应用数据失败: {e}")
            return False
    
    def start_app_and_monitor(self):
        """启动应用并监控WebSocket连接"""
        print("🚀 启动应用并监控WebSocket连接...")
        
        try:
            # 清除日志
            subprocess.run(["adb", "-s", self.device_id, "logcat", "-c"], 
                         capture_output=True)
            
            # 启动应用
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", f"{self.package_name}/.MainActivity"],
                capture_output=True
            )
            
            print("⏳ 等待应用初始化...")
            time.sleep(5)
            
            # 获取WebSocket相关日志
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "WS:*", "ChatViewModel:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                self.analyze_websocket_logs(logs)
            else:
                print("❌ 获取日志失败")
                
        except Exception as e:
            print(f"❌ 启动监控失败: {e}")
    
    def analyze_websocket_logs(self, logs):
        """分析WebSocket日志"""
        print("\n📋 WebSocket连接日志分析:")
        print("=" * 60)
        
        if not logs:
            print("❌ 没有找到相关日志")
            return
        
        websocket_logs = []
        key_events = {
            "start_called": False,
            "connecting": False,
            "connected": False,
            "hello_sent": False,
            "hello_received": False,
            "connection_failed": False
        }
        
        for line in logs.split('\n'):
            if any(keyword in line for keyword in ["WS", "WebSocket", "protocol start", "连接"]):
                websocket_logs.append(line)
                
                # 检查关键事件
                if "WebSocket protocol start() called" in line:
                    key_events["start_called"] = True
                elif "正在建立WebSocket连接" in line:
                    key_events["connecting"] = True
                elif "WebSocket connected successfully" in line:
                    key_events["connected"] = True
                elif "Sending hello message" in line:
                    key_events["hello_sent"] = True
                elif "收到服务器hello" in line:
                    key_events["hello_received"] = True
                elif "WebSocket connection failed" in line:
                    key_events["connection_failed"] = True
        
        # 显示关键日志
        print("📄 相关日志:")
        for log in websocket_logs[-15:]:  # 最后15条
            print(f"   {log}")
        
        # 分析连接状态
        print(f"\n🔍 连接状态分析:")
        print(f"   协议start()调用: {'✅' if key_events['start_called'] else '❌'}")
        print(f"   开始建立连接: {'✅' if key_events['connecting'] else '❌'}")
        print(f"   WebSocket连接成功: {'✅' if key_events['connected'] else '❌'}")
        print(f"   发送Hello消息: {'✅' if key_events['hello_sent'] else '❌'}")
        print(f"   收到服务器Hello: {'✅' if key_events['hello_received'] else '❌'}")
        print(f"   连接失败: {'🔴' if key_events['connection_failed'] else '✅'}")
        
        # 总结
        if key_events["hello_received"]:
            print("\n🎉 **WebSocket连接修复成功！**")
            print("应用现在应该能正常工作，不再显示Idle状态")
        elif key_events["connected"] and key_events["hello_sent"]:
            print("\n⚠️ **WebSocket连接建立，但服务器握手未完成**")
            print("可能是服务器端配置问题")
        elif key_events["connecting"]:
            print("\n⚠️ **正在尝试连接WebSocket**")
            print("连接可能正在进行中或遇到网络问题")
        elif key_events["start_called"]:
            print("\n❌ **协议启动但连接失败**")
            print("修复已生效，但存在网络或配置问题")
        else:
            print("\n❌ **修复未生效**")
            print("协议可能未正确启动")
    
    def suggest_next_steps(self):
        """建议下一步操作"""
        print(f"\n💡 下一步建议:")
        print("=" * 30)
        
        print("1. 📱 检查应用界面")
        print("   - 观察是否还显示'Idle'状态")
        print("   - 尝试点击聊天按钮测试功能")
        
        print("\n2. 🔧 如果仍显示Idle")
        print("   - 检查设备配置中的OTA URL")
        print("   - 确认WebSocket URL: ws://47.122.144.73:8000/xiaozhi/v1/")
        print("   - 尝试重新配置绑定")
        
        print("\n3. 🌐 网络检查")
        print("   - 确认设备可以访问47.122.144.73:8000")
        print("   - 检查防火墙设置")
        
        print("\n4. 📋 如果连接成功但功能异常")
        print("   - 检查音频权限")
        print("   - 测试语音录制功能")
    
    def run_complete_test(self):
        """运行完整测试"""
        print("🔍 WebSocket连接修复测试")
        print("=" * 60)
        
        # 1. 重新构建安装（如果需要）
        # build_success = self.rebuild_and_install()
        # if not build_success:
        #     print("❌ 构建安装失败，无法继续测试")
        #     return
        
        # 2. 清除应用数据
        self.clear_app_data()
        
        # 3. 启动应用并监控
        self.start_app_and_monitor()
        
        # 4. 提供建议
        self.suggest_next_steps()

def main():
    tester = WebSocketFixTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 