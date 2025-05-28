#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绑定后诊断工具
分析为什么绑定成功后应用仍显示Idle状态
"""

import subprocess
import json
import time
import requests

class PostBindingDiagnostics:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
    
    def check_websocket_connection(self):
        """检查WebSocket连接状态"""
        print("🔗 检查WebSocket连接状态...")
        
        # 从应用日志中查找WebSocket相关信息
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "WebsocketProtocol:*", "ChatViewModel:*", "Protocol:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                websocket_logs = []
                
                for line in logs.split('\n'):
                    if any(keyword in line.lower() for keyword in 
                          ["websocket", "connection", "连接", "protocol", "idle"]):
                        websocket_logs.append(line)
                
                if websocket_logs:
                    print("📋 WebSocket相关日志:")
                    for log in websocket_logs[-15:]:  # 最后15条
                        print(f"   {log}")
                else:
                    print("❌ 未找到WebSocket相关日志")
                    
                return websocket_logs
            else:
                print("❌ 获取日志失败")
                return []
                
        except Exception as e:
            print(f"❌ 检查WebSocket连接失败: {e}")
            return []
    
    def check_device_state(self):
        """检查设备状态"""
        print("\n📱 检查设备状态...")
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "ChatViewModel:*", "DeviceState:*", "ActivationManager:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                state_logs = []
                
                for line in logs.split('\n'):
                    if any(keyword in line for keyword in 
                          ["DeviceState", "设备状态", "IDLE", "LISTENING", "初始化"]):
                        state_logs.append(line)
                
                if state_logs:
                    print("📋 设备状态日志:")
                    for log in state_logs[-10:]:  # 最后10条
                        print(f"   {log}")
                        
                    # 分析最后的状态
                    last_state = None
                    for log in reversed(state_logs):
                        if "DeviceState" in log or "设备状态" in log:
                            last_state = log
                            break
                    
                    if last_state:
                        print(f"\n🎯 最后记录的设备状态: {last_state}")
                else:
                    print("❌ 未找到设备状态日志")
                    
                return state_logs
            else:
                print("❌ 获取设备状态日志失败")
                return []
                
        except Exception as e:
            print(f"❌ 检查设备状态失败: {e}")
            return []
    
    def test_websocket_endpoint(self):
        """测试WebSocket端点是否可达"""
        print("\n🌐 测试WebSocket端点连通性...")
        
        # 常见的WebSocket URL
        websocket_urls = [
            "ws://47.122.144.73:8000/xiaozhi/v1/",
            "ws://192.168.0.129:8000/xiaozhi/v1/",
            "ws://localhost:8000/xiaozhi/v1/"
        ]
        
        for ws_url in websocket_urls:
            http_url = ws_url.replace("ws://", "http://").replace("wss://", "https://")
            
            try:
                print(f"🔍 测试: {http_url}")
                response = requests.get(http_url, timeout=5)
                print(f"   ✅ HTTP状态: {response.status_code}")
                print(f"   📄 响应: {response.text[:100]}...")
            except requests.exceptions.ConnectionError:
                print(f"   ❌ 连接失败: 无法连接到服务器")
            except requests.exceptions.Timeout:
                print(f"   ⏰ 连接超时")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
    
    def check_audio_components(self):
        """检查音频组件初始化"""
        print("\n🎵 检查音频组件状态...")
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "OpusEncoder:*", "OpusDecoder:*", "AudioRecorder:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                audio_logs = []
                
                for line in logs.split('\n'):
                    if any(keyword in line for keyword in 
                          ["Opus", "Audio", "initialized", "初始化", "failed", "失败"]):
                        audio_logs.append(line)
                
                if audio_logs:
                    print("📋 音频组件日志:")
                    for log in audio_logs[-10:]:
                        print(f"   {log}")
                        
                    # 检查是否有初始化失败
                    failed_logs = [log for log in audio_logs if "failed" in log.lower() or "失败" in log]
                    if failed_logs:
                        print(f"\n⚠️  发现音频组件初始化失败:")
                        for log in failed_logs:
                            print(f"   🔴 {log}")
                else:
                    print("❌ 未找到音频组件日志")
                    
                return audio_logs
            else:
                print("❌ 获取音频日志失败")
                return []
                
        except Exception as e:
            print(f"❌ 检查音频组件失败: {e}")
            return []
    
    def check_protocol_initialization(self):
        """检查协议初始化"""
        print("\n🔧 检查协议初始化状态...")
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "logcat", "-d", "-v", "time",
                 "Protocol:*", "WebsocketProtocol:*", "*:S"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                protocol_logs = []
                
                for line in logs.split('\n'):
                    if any(keyword in line for keyword in 
                          ["Protocol", "start", "启动", "dispose", "释放", "connected", "连接"]):
                        protocol_logs.append(line)
                
                if protocol_logs:
                    print("📋 协议初始化日志:")
                    for log in protocol_logs[-10:]:
                        print(f"   {log}")
                else:
                    print("❌ 未找到协议初始化日志")
                    
                return protocol_logs
            else:
                print("❌ 获取协议日志失败")
                return []
                
        except Exception as e:
            print(f"❌ 检查协议初始化失败: {e}")
            return []
    
    def analyze_idle_cause(self):
        """分析Idle状态的可能原因"""
        print("\n🔍 分析Idle状态的可能原因...")
        
        possible_causes = [
            {
                "原因": "WebSocket连接失败",
                "检查方法": "查看WebSocket连接日志是否有错误",
                "解决方案": "检查网络连接，确认WebSocket URL正确"
            },
            {
                "原因": "音频组件初始化失败", 
                "检查方法": "查看OpusEncoder/Decoder初始化日志",
                "解决方案": "检查原生库是否正确加载"
            },
            {
                "原因": "协议未正确启动",
                "检查方法": "查看Protocol.start()调用日志",
                "解决方案": "确认协议初始化流程完整"
            },
            {
                "原因": "服务器端问题",
                "检查方法": "测试WebSocket端点连通性",
                "解决方案": "检查服务器状态，确认WebSocket服务运行"
            },
            {
                "原因": "设备状态机错误",
                "检查方法": "查看DeviceState变化日志",
                "解决方案": "重新初始化设备状态"
            }
        ]
        
        print("📋 可能的原因和解决方案:")
        for i, cause in enumerate(possible_causes, 1):
            print(f"\n{i}. {cause['原因']}")
            print(f"   🔍 检查方法: {cause['检查方法']}")
            print(f"   💡 解决方案: {cause['解决方案']}")
    
    def suggest_immediate_fixes(self):
        """建议立即修复方案"""
        print(f"\n🚀 立即修复建议:")
        print("=" * 50)
        
        print("1. 🔄 重新启动应用")
        print("   - 完全关闭应用")
        print("   - 重新启动")
        print("   - 观察初始化流程")
        
        print("\n2. 🧹 清除应用缓存")
        print("   - adb shell pm clear info.dourok.voicebot")
        print("   - 重新配置OTA URL")
        print("   - 重新检查绑定状态")
        
        print("\n3. 🌐 检查网络连接")
        print("   - 确认设备可以访问WebSocket服务器")
        print("   - 测试WebSocket端点连通性")
        print("   - 检查防火墙设置")
        
        print("\n4. 📱 检查应用权限")
        print("   - 确认应用有网络权限")
        print("   - 确认应用有录音权限")
        print("   - 检查其他必要权限")
        
        print("\n5. 🔧 强制触发状态变化")
        print("   - 尝试点击聊天界面的按钮")
        print("   - 观察是否有状态变化")
        print("   - 检查错误提示")
    
    def run_full_diagnosis(self):
        """运行完整诊断"""
        print("🔍 绑定后Idle状态诊断")
        print("=" * 60)
        
        # 1. 检查WebSocket连接
        self.check_websocket_connection()
        
        # 2. 检查设备状态
        self.check_device_state()
        
        # 3. 测试WebSocket端点
        self.test_websocket_endpoint()
        
        # 4. 检查音频组件
        self.check_audio_components()
        
        # 5. 检查协议初始化
        self.check_protocol_initialization()
        
        # 6. 分析可能原因
        self.analyze_idle_cause()
        
        # 7. 提供修复建议
        self.suggest_immediate_fixes()

def main():
    diagnostics = PostBindingDiagnostics()
    diagnostics.run_full_diagnosis()

if __name__ == "__main__":
    main() 