#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32和Android端STT统一化测试工具
确保两端使用相同的服务器端STT方案
"""

import subprocess
import time
import json
import asyncio
import websockets
import opuslib_next
import wave
import io

def test_esp32_stt_compatibility():
    """测试Android端与ESP32端STT兼容性"""
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("🔄 ESP32和Android端STT统一化测试")
    print("=" * 60)
    
    # 1. 检查服务器STT配置
    print("1. 检查ESP32服务器STT配置...")
    print("   📍 ESP32端STT方案：")
    print("      - 位置：xiaozhi-server/core/providers/asr/")
    print("      - 模型：FunASR (本地/服务器)")
    print("      - 处理：服务器端STT")
    print("      - 响应格式：{\"type\": \"stt\", \"text\": \"结果\", \"session_id\": \"xxx\"}")
    
    # 2. 清除Android端日志
    print("\\n2. 清除Android端日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"], capture_output=True)
    
    # 3. 启动实时监控
    print("\\n3. 启动实时STT监控...")
    print("   请按以下步骤操作：")
    print("   👆 点击Android应用'开始监听'")
    print("   🗣️ 清晰地说：'你好小智，请介绍一下你自己'")
    print("   ⏱️ 等待15秒...")
    print("   📋 观察STT响应...")
    
    input("按Enter开始15秒监控...")
    
    # 开始监控
    start_time = time.time()
    collected_logs = []
    
    print("\\n🔄 监控中... (15秒)")
    process = subprocess.Popen(
        ["adb", "-s", device_id, "logcat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        while time.time() - start_time < 15:
            line = process.stdout.readline()
            if line:
                collected_logs.append(line.strip())
                # 实时显示关键信息
                if any(keyword in line.lower() for keyword in [
                    'stt', 'received text message', 'speech', 'text'
                ]):
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
    finally:
        process.terminate()
    
    # 4. 分析STT流程
    analyze_stt_flow(collected_logs)

def analyze_stt_flow(logs):
    """分析STT完整流程"""
    print("\\n📊 STT流程分析")
    print("=" * 40)
    
    # 分析各个环节
    audio_sent = False
    listen_command = False
    server_response = False
    stt_received = False
    ui_updated = False
    
    stt_responses = []
    server_responses = []
    
    for log in logs:
        # 检查监听命令
        if 'sending text' in log.lower() and 'listen' in log.lower():
            listen_command = True
            print(f"✅ 监听命令已发送: {log}")
        
        # 检查音频发送
        if 'sending audio' in log.lower() or 'audio data' in log.lower():
            audio_sent = True
        
        # 检查服务器响应
        if 'received text message' in log.lower():
            server_response = True
            server_responses.append(log)
            print(f"📨 服务器响应: {log}")
            
            # 尝试解析STT响应
            try:
                if '{' in log and '}' in log:
                    json_start = log.find('{')
                    json_str = log[json_start:]
                    response_data = json.loads(json_str)
                    if response_data.get('type') == 'stt':
                        stt_received = True
                        stt_text = response_data.get('text', '')
                        stt_responses.append(stt_text)
                        print(f"🎯 STT识别结果: '{stt_text}'")
            except:
                pass
        
        # 检查UI更新
        if 'chatmessage' in log.lower() or 'user' in log.lower():
            ui_updated = True
    
    # 输出诊断结果
    print("\\n🎯 STT流程诊断结果")
    print("-" * 30)
    print(f"📤 监听命令发送: {'✅' if listen_command else '❌'}")
    print(f"🎤 音频数据发送: {'✅' if audio_sent else '❌'}")
    print(f"📨 服务器响应接收: {'✅' if server_response else '❌'}")
    print(f"🎯 STT结果识别: {'✅' if stt_received else '❌'}")
    print(f"💬 UI界面更新: {'✅' if ui_updated else '❌'}")
    
    if stt_responses:
        print(f"\\n🎉 STT识别成功！识别结果：")
        for i, text in enumerate(stt_responses, 1):
            print(f"   {i}. '{text}'")
    else:
        print("\\n❌ 未收到STT识别结果")
        provide_stt_fix_suggestions(listen_command, audio_sent, server_response)

def provide_stt_fix_suggestions(listen_command, audio_sent, server_response):
    """提供STT修复建议"""
    print("\\n🔧 修复建议")
    print("-" * 20)
    
    if not listen_command:
        print("❌ 监听命令未发送")
        print("   解决：检查startListening()方法")
    elif not audio_sent:
        print("❌ 音频数据未发送")
        print("   解决：检查录音权限和音频编码")
    elif not server_response:
        print("❌ 服务器无响应")
        print("   解决：")
        print("      1. 检查服务器STT服务状态")
        print("      2. 确认FunASR模型正常运行")
        print("      3. 检查网络连接")
    else:
        print("❌ STT响应格式问题")
        print("   解决：")
        print("      1. 检查服务器STT响应格式")
        print("      2. 确认WebSocket消息解析")
        print("      3. 验证ChatViewModel STT处理逻辑")

async def test_websocket_stt_directly():
    """直接测试WebSocket STT通信"""
    uri = "ws://47.122.144.73:8000/xiaozhi/v1/"
    
    print("\\n🌐 直接测试WebSocket STT通信")
    print("=" * 40)
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送Hello消息
            hello_msg = {
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
            
            await websocket.send(json.dumps(hello_msg))
            print("✅ Hello消息已发送")
            
            # 等待服务器响应
            response = await websocket.recv()
            print(f"📨 服务器响应: {response}")
            
            # 发送监听命令
            listen_msg = {
                "type": "listen",
                "state": "start",
                "mode": "manual",
                "session_id": "test_session"
            }
            
            await websocket.send(json.dumps(listen_msg))
            print("✅ 监听命令已发送")
            
            # 这里可以发送测试音频数据
            # 暂时跳过，因为需要真实的Opus音频数据
            print("ℹ️ 音频数据发送已跳过（需要真实Opus数据）")
            
            # 等待可能的STT响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📨 可能的STT响应: {response}")
            except asyncio.TimeoutError:
                print("⏱️ 5秒内未收到STT响应（正常，因为没有发送音频）")
                
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--websocket":
        asyncio.run(test_websocket_stt_directly())
    else:
        test_esp32_stt_compatibility()

if __name__ == "__main__":
    main() 