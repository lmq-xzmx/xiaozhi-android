#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket地址诊断脚本
检查Android客户端连接的WebSocket服务器地址是否有效
"""

import asyncio
import websockets
import json
import time
import sys
import requests
from urllib.parse import urlparse

class WebSocketDiagnostics:
    def __init__(self):
        self.ws_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
        self.http_url = "http://47.122.144.73:8000/"
        
    def check_basic_connectivity(self):
        """检查基础网络连通性"""
        print("🌐 检查基础网络连通性")
        print("=" * 40)
        
        parsed = urlparse(self.ws_url)
        host = parsed.hostname
        port = parsed.port
        
        print(f"目标服务器: {host}:{port}")
        
        # 1. 检查HTTP端口连通性
        try:
            response = requests.get(self.http_url, timeout=10)
            print(f"✅ HTTP连通性正常 (状态码: {response.status_code})")
            print(f"   响应内容: {response.text[:100]}...")
            return True
        except requests.exceptions.ConnectionError:
            print(f"❌ HTTP连接失败 - 服务器不可达")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ HTTP连接超时 - 网络延迟过高")
            return False
        except Exception as e:
            print(f"❌ HTTP连接错误: {e}")
            return False
    
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        print(f"\n🔗 测试WebSocket连接")
        print("=" * 40)
        print(f"目标地址: {self.ws_url}")
        
        try:
            # 第一次尝试：不带认证参数
            print("\n🔍 尝试1: 基础WebSocket连接")
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                print("✅ WebSocket连接成功!")
                
                # 发送Hello握手消息
                hello_msg = {
                    "type": "hello",
                    "device_id": "test_android_device",
                    "device_name": "Android VoiceBot", 
                    "device_mac": "02:aa:bb:cc:dd:ee",
                    "token": "test_token_123",
                    "client_type": "android",
                    "app_version": "1.0.0",
                    "version": 1,
                    "transport": "websocket",
                    "audio_params": {
                        "format": "opus",
                        "sample_rate": 16000,
                        "channels": 1,
                        "frame_duration": 60
                    }
                }
                
                print(f"📤 发送Hello握手消息...")
                await websocket.send(json.dumps(hello_msg))
                
                # 等待服务器响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 收到服务器响应: {response}")
                    
                    # 解析响应
                    try:
                        response_data = json.loads(response)
                        if response_data.get("type") == "hello":
                            session_id = response_data.get("session_id")
                            print(f"🎉 Hello握手成功!")
                            print(f"🆔 Session ID: {session_id}")
                            print(f"✅ WebSocket地址配置正确!")
                            return True
                        else:
                            print(f"⚠️ 收到非Hello响应: {response_data}")
                    except json.JSONDecodeError:
                        print(f"⚠️ 服务器响应不是JSON格式: {response}")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ 5秒内未收到服务器Hello响应")
                    print(f"⚠️ 可能的问题:")
                    print(f"   - 服务器未启动Hello握手功能")
                    print(f"   - 认证参数不正确")
                    print(f"   - 服务器处理延迟")
                    return False
                    
        except websockets.exceptions.InvalidURI:
            print(f"❌ WebSocket地址格式错误: {self.ws_url}")
            return False
        except websockets.exceptions.ConnectionClosed:
            print(f"❌ WebSocket连接被服务器关闭")
            return False
        except OSError as e:
            print(f"❌ 网络连接错误: {e}")
            return False
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            return False
    
    async def test_with_url_params(self):
        """测试带URL参数的连接"""
        print(f"\n🔍 尝试2: 带URL参数的连接")
        
        auth_url = f"{self.ws_url}?device_id=test_android&device_mac=02:aa:bb:cc:dd:ee&token=test_token"
        print(f"目标地址: {auth_url}")
        
        try:
            async with websockets.connect(auth_url, timeout=10) as websocket:
                print("✅ 带参数的WebSocket连接成功!")
                
                # 等待服务器自动握手
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 收到自动握手响应: {response}")
                    return True
                except asyncio.TimeoutError:
                    print(f"⏰ 未收到自动握手响应，发送手动Hello...")
                    
                    # 发送简化的Hello消息
                    simple_hello = {"type": "hello", "version": 1, "transport": "websocket"}
                    await websocket.send(json.dumps(simple_hello))
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 手动Hello响应: {response}")
                    return True
                    
        except Exception as e:
            print(f"❌ 带参数连接失败: {e}")
            return False
    
    def analyze_android_logs(self):
        """分析Android端日志，诊断连接问题"""
        print(f"\n📊 Android端连接问题分析")
        print("=" * 40)
        
        print("基于您的日志 'WebSocket is null'，可能的原因:")
        print("1. ❌ WebSocket连接从未建立成功")
        print("2. ❌ onOpen回调未正确触发")
        print("3. ❌ onFailure导致websocket被置null")
        print("4. ❌ 网络问题导致连接中断")
        
        print(f"\n🔧 建议的解决方案:")
        print("1. 检查网络连通性")
        print("2. 确认服务器地址正确")
        print("3. 验证Hello握手流程")
        print("4. 增强连接重试机制")
    
    def check_server_endpoints(self):
        """检查服务器的多个端点"""
        print(f"\n🔍 检查服务器端点")
        print("=" * 40)
        
        endpoints = [
            "http://47.122.144.73:8000/",
            "http://47.122.144.73:8000/xiaozhi/",
            "http://47.122.144.73:8000/xiaozhi/v1/",
            "http://47.122.144.73:8002/xiaozhi/ota/",
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                print(f"✅ {endpoint} - HTTP {response.status_code}")
                if len(response.text) > 0:
                    print(f"   内容预览: {response.text[:80]}...")
            except Exception as e:
                print(f"❌ {endpoint} - {e}")

async def main():
    """主诊断流程"""
    print("🔍 WebSocket地址诊断开始")
    print("=" * 50)
    
    diagnostics = WebSocketDiagnostics()
    
    # 1. 基础连通性检查
    if not diagnostics.check_basic_connectivity():
        print(f"\n❌ 基础网络连通性检查失败，无法继续")
        return
    
    # 2. 检查多个服务器端点
    diagnostics.check_server_endpoints()
    
    # 3. WebSocket连接测试
    ws_success = await diagnostics.test_websocket_connection()
    
    # 4. 带参数连接测试
    if not ws_success:
        await diagnostics.test_with_url_params()
    
    # 5. Android日志分析
    diagnostics.analyze_android_logs()
    
    print(f"\n🎯 诊断总结")
    print("=" * 50)
    
    if ws_success:
        print("✅ WebSocket地址配置正确")
        print("✅ 服务器Hello握手正常")
        print("🔧 Android端问题可能在于:")
        print("   - 网络权限问题") 
        print("   - 连接重试逻辑")
        print("   - Hello握手超时设置")
    else:
        print("❌ WebSocket连接或握手失败")
        print("🔧 需要检查:")
        print("   - 服务器是否正常运行")
        print("   - 防火墙设置")
        print("   - WebSocket端点配置")

if __name__ == "__main__":
    asyncio.run(main()) 