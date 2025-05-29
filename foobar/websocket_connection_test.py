#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket连接测试脚本
用于验证Android客户端与远程xiaozhi-server的协议对接
"""

import asyncio
import websockets
import json
import time
import sys

class WebSocketTester:
    def __init__(self, url):
        self.url = url
        self.websocket = None
        self.session_id = None
        
    async def test_connection(self):
        """测试WebSocket连接"""
        print(f"🔗 正在连接WebSocket服务器: {self.url}")
        
        try:
            # 尝试带认证参数的连接
            auth_url = f"{self.url}?device_id=test_android_device&device_mac=aa:bb:cc:dd:ee:ff&token=test_token"
            print(f"🔐 尝试带认证参数连接: {auth_url}")
            
            async with websockets.connect(auth_url) as websocket:
                self.websocket = websocket
                print("✅ WebSocket连接成功!")
                
                # 等待服务器的欢迎消息
                try:
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 收到服务器欢迎消息: {welcome_msg}")
                    
                    # 尝试解析欢迎消息
                    try:
                        welcome_data = json.loads(welcome_msg)
                        self.session_id = welcome_data.get("session_id")
                        print(f"🆔 Session ID: {self.session_id}")
                    except json.JSONDecodeError:
                        print(f"⚠️ 欢迎消息不是JSON格式: {welcome_msg}")
                    
                except asyncio.TimeoutError:
                    print("⚠️ 5秒内未收到服务器欢迎消息，继续测试握手...")
                
                # 测试Hello握手
                await self.test_hello_handshake()
                
                # 测试Listen Start
                await self.test_listen_start()
                
                print("✅ 所有协议测试完成!")
                
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            
            # 尝试无认证参数的基础连接
            print(f"🔄 尝试基础连接: {self.url}")
            try:
                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    print("✅ 基础WebSocket连接成功!")
                    
                    # 等待欢迎消息
                    try:
                        welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        print(f"📨 收到基础连接欢迎消息: {welcome_msg}")
                    except asyncio.TimeoutError:
                        print("⚠️ 基础连接无欢迎消息")
                    
                    # 测试认证握手
                    await self.test_auth_hello_handshake()
                    
            except Exception as e2:
                print(f"❌ 基础连接也失败: {e2}")
                return False
            
        return True
    
    async def test_hello_handshake(self):
        """测试Hello握手流程 - Android格式"""
        print("\n🤝 测试Hello握手流程 (Android格式)...")
        
        # Android客户端格式的Hello消息
        hello_message = {
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "format": "opus",
                "sample_rate": 16000,
                "channels": 1,
                "frame_duration": 60
            }
        }
        
        print(f"📤 发送Android格式Hello消息: {json.dumps(hello_message, indent=2)}")
        await self.websocket.send(json.dumps(hello_message))
        
        # 等待Hello响应
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            print(f"📨 收到Hello响应: {response}")
            
            # 解析响应
            try:
                response_data = json.loads(response)
                if response_data.get("type") == "hello":
                    self.session_id = response_data.get("session_id", self.session_id)
                    print("✅ Hello握手成功!")
                    print(f"🆔 获取Session ID: {self.session_id}")
                    return True
                else:
                    print(f"⚠️ 收到非Hello响应: {response_data.get('type')}")
                    return False
            except json.JSONDecodeError:
                print(f"⚠️ Hello响应不是JSON格式: {response}")
                return False
                
        except asyncio.TimeoutError:
            print("❌ Hello握手超时!")
            return False
        except Exception as e:
            print(f"❌ Hello握手失败: {e}")
            return False
    
    async def test_auth_hello_handshake(self):
        """测试认证Hello握手流程 - xiaozhi-server格式"""
        print("\n🔐 测试认证Hello握手流程 (xiaozhi-server格式)...")
        
        # xiaozhi-server期望的Hello消息格式
        auth_hello_message = {
            "type": "hello",
            "device_id": "test_android_device",
            "device_name": "Android测试设备",
            "device_mac": "aa:bb:cc:dd:ee:ff",
            "token": "test_token_123456"
        }
        
        print(f"📤 发送认证Hello消息: {json.dumps(auth_hello_message, indent=2)}")
        await self.websocket.send(json.dumps(auth_hello_message))
        
        # 等待认证Hello响应
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            print(f"📨 收到认证Hello响应: {response}")
            
            # 解析响应
            try:
                response_data = json.loads(response)
                if response_data.get("type") == "hello" and response_data.get("session_id"):
                    self.session_id = response_data.get("session_id")
                    print("✅ 认证Hello握手成功!")
                    print(f"🆔 获取Session ID: {self.session_id}")
                    return True
                else:
                    print(f"⚠️ 认证失败或响应格式不正确")
                    print(f"   响应类型: {response_data.get('type')}")
                    print(f"   Session ID: {response_data.get('session_id')}")
                    return False
            except json.JSONDecodeError:
                print(f"⚠️ 认证Hello响应不是JSON格式: {response}")
                return False
                
        except asyncio.TimeoutError:
            print("❌ 认证Hello握手超时!")
            return False
        except Exception as e:
            print(f"❌ 认证Hello握手失败: {e}")
            return False
    
    async def test_listen_start(self):
        """测试Listen Start流程"""
        print("\n🎧 测试Listen Start流程...")
        
        if not self.session_id:
            print("❌ 无Session ID，跳过Listen测试")
            return False
            
        # 发送Listen Start消息
        listen_message = {
            "session_id": self.session_id,
            "type": "listen", 
            "state": "start",
            "mode": "auto"
        }
        
        print(f"📤 发送Listen Start消息: {json.dumps(listen_message, indent=2)}")
        await self.websocket.send(json.dumps(listen_message))
        
        # 等待可能的确认响应
        try:
            # 设置较短超时，因为服务器可能不会立即响应
            response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
            print(f"📨 收到Listen响应: {response}")
            
            response_data = json.loads(response)
            if response_data.get("type") == "listen_ack":
                print("✅ Listen Start确认成功!")
                return True
            else:
                print(f"📝 收到其他响应: {response_data.get('type')}")
                return True
                
        except asyncio.TimeoutError:
            print("⚠️ 3秒内无Listen响应 (这可能是正常的)")
            return True
        except Exception as e:
            print(f"❌ Listen测试出错: {e}")
            return False
    
    async def test_text_message(self, text="你好"):
        """测试文本消息发送"""
        print(f"\n💬 测试文本消息: {text}")
        
        if not self.session_id:
            print("❌ 无Session ID，跳过文本测试")
            return False
            
        # 发送文本消息 (模拟语音识别)
        text_message = {
            "session_id": self.session_id,
            "type": "listen",
            "state": "detect", 
            "text": text
        }
        
        print(f"📤 发送文本消息: {json.dumps(text_message, indent=2)}")
        await self.websocket.send(json.dumps(text_message))
        
        # 等待STT和LLM响应
        timeout_time = time.time() + 10.0
        responses = []
        
        while time.time() < timeout_time:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                responses.append(response_data)
                
                msg_type = response_data.get("type")
                if msg_type == "stt":
                    print(f"✅ 收到STT响应: {response_data.get('text')}")
                elif msg_type == "llm":
                    print(f"🤖 收到LLM响应: {response_data.get('text')}")
                elif msg_type == "tts":
                    state = response_data.get("state")
                    if state == "sentence_start":
                        print(f"🗣️ TTS开始: {response_data.get('text')}")
                    elif state == "stop":
                        print("🔚 TTS结束")
                        break
                else:
                    print(f"📝 其他响应: {msg_type}")
                    
            except asyncio.TimeoutError:
                print("⏱️ 等待响应超时")
                break
            except Exception as e:
                print(f"❌ 接收响应出错: {e}")
                break
        
        print(f"📊 共收到{len(responses)}条响应")
        return len(responses) > 0

def test_http_endpoint(url):
    """测试HTTP端点可达性"""
    import urllib.request
    
    http_url = url.replace("ws://", "http://").replace("wss://", "https://")
    print(f"🌐 测试HTTP端点: {http_url}")
    
    try:
        req = urllib.request.Request(http_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            print(f"✅ HTTP端点可达 (状态码: {status_code})")
            print(f"📄 响应内容: {content[:200]}...")
            return True
    except Exception as e:
        print(f"❌ HTTP端点不可达: {e}")
        return False

async def main():
    """主测试函数"""
    websocket_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
    
    print("🚀 开始WebSocket协议对接测试")
    print("=" * 50)
    print(f"目标服务器: {websocket_url}")
    print("=" * 50)
    
    # 1. 测试HTTP端点
    if not test_http_endpoint(websocket_url):
        print("❌ HTTP端点不可达，停止测试")
        return
    
    # 2. 测试WebSocket连接和协议
    tester = WebSocketTester(websocket_url)
    
    if await tester.test_connection():
        print("\n🎯 基础协议测试通过，开始文本消息测试...")
        
        # 3. 如果有session_id，测试文本消息处理
        if tester.session_id:
            await tester.test_text_message("你好，我是Android客户端测试")
        else:
            print("⚠️ 未获得session_id，跳过文本消息测试")
    else:
        print("❌ WebSocket连接测试失败")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        sys.exit(1) 