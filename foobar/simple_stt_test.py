#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版STT测试工具
检查Android端STT流程，确保与ESP32端一致
"""

import subprocess
import time
import json

def test_android_stt_flow():
    """测试Android端STT完整流程"""
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("🎯 Android端STT流程测试")
    print("=" * 50)
    
    # 1. 显示ESP32端STT方案信息
    print("1. ESP32端STT方案（参考标准）:")
    print("   📍 位置: xiaozhi-server/core/providers/asr/")
    print("   🤖 模型: FunASR (本地/服务器)")
    print("   ⚙️ 处理: 服务器端STT")
    print("   📨 响应: {\"type\": \"stt\", \"text\": \"识别结果\"}")
    
    # 2. 清除旧日志
    print("\n2. 清除Android端日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"], capture_output=True)
    
    # 3. 测试指导
    print("\n3. 测试步骤:")
    print("   👆 打开Android应用")
    print("   🔘 点击'开始监听'按钮")
    print("   🗣️ 清晰地说: '你好小智'")
    print("   ⏱️ 等待响应...")
    
    input("\n按Enter开始监控 (监控15秒)...")
    
    # 4. 实时监控
    start_time = time.time()
    logs = []
    
    print("\n🔄 开始监控...")
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
                logs.append(line.strip())
                
                # 实时显示重要日志
                if any(keyword in line.lower() for keyword in [
                    'stt', 'text message', 'speech', 'listen', 'audio'
                ]):
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
                    
    finally:
        process.terminate()
    
    # 5. 分析结果
    analyze_logs(logs)

def analyze_logs(logs):
    """分析日志，检查STT流程"""
    print("\n📊 STT流程分析")
    print("=" * 30)
    
    # 检查各个关键步骤
    steps = {
        'listen_command': False,
        'audio_recording': False,
        'audio_sending': False,
        'server_response': False,
        'stt_result': False,
        'ui_update': False
    }
    
    stt_texts = []
    server_messages = []
    
    for log in logs:
        log_lower = log.lower()
        
        # 检查监听命令
        if 'sending text' in log_lower and 'listen' in log_lower:
            steps['listen_command'] = True
            print(f"✅ 监听命令: {log}")
        
        # 检查音频录制
        if 'audio record' in log_lower or 'recording' in log_lower:
            steps['audio_recording'] = True
        
        # 检查音频发送
        if 'sending audio' in log_lower or 'audio data' in log_lower:
            steps['audio_sending'] = True
        
        # 检查服务器响应
        if 'received text message' in log_lower:
            steps['server_response'] = True
            server_messages.append(log)
            print(f"📨 服务器消息: {log}")
            
            # 尝试解析STT结果
            try:
                if '{' in log and '}' in log:
                    json_start = log.find('{')
                    json_str = log[json_start:]
                    data = json.loads(json_str)
                    
                    if data.get('type') == 'stt':
                        steps['stt_result'] = True
                        text = data.get('text', '')
                        stt_texts.append(text)
                        print(f"🎯 STT结果: '{text}'")
            except:
                pass
        
        # 检查UI更新
        if 'chatmessage' in log_lower or ('user' in log_lower and 'message' in log_lower):
            steps['ui_update'] = True
    
    # 输出诊断结果
    print("\n🎯 流程检查结果:")
    print(f"   📤 发送监听命令: {'✅' if steps['listen_command'] else '❌'}")
    print(f"   🎤 开始音频录制: {'✅' if steps['audio_recording'] else '❌'}")
    print(f"   📡 发送音频数据: {'✅' if steps['audio_sending'] else '❌'}")
    print(f"   📨 接收服务器响应: {'✅' if steps['server_response'] else '❌'}")
    print(f"   🎯 收到STT结果: {'✅' if steps['stt_result'] else '❌'}")
    print(f"   💬 更新UI界面: {'✅' if steps['ui_update'] else '❌'}")
    
    # 显示STT结果
    if stt_texts:
        print(f"\n🎉 STT识别成功! 识别到 {len(stt_texts)} 个结果:")
        for i, text in enumerate(stt_texts, 1):
            print(f"   {i}. '{text}'")
        print("\n✅ Android端STT与ESP32端方案一致!")
    else:
        print("\n❌ 未收到STT识别结果")
        diagnose_stt_problem(steps, server_messages)

def diagnose_stt_problem(steps, server_messages):
    """诊断STT问题"""
    print("\n🔧 问题诊断:")
    
    if not steps['listen_command']:
        print("❌ 监听命令未发送")
        print("   原因: startListening()方法可能有问题")
        print("   解决: 检查ChatViewModel.startListening()实现")
        
    elif not steps['audio_recording']:
        print("❌ 音频录制未启动")
        print("   原因: 录音权限或音频组件初始化问题")
        print("   解决: 检查麦克风权限和AudioRecorder")
        
    elif not steps['audio_sending']:
        print("❌ 音频数据未发送")
        print("   原因: Opus编码失败或WebSocket断开")
        print("   解决: 检查OpusEncoder和WebSocket连接")
        
    elif not steps['server_response']:
        print("❌ 服务器无响应")
        print("   原因: 服务器STT服务异常或网络问题")
        print("   解决:")
        print("      1. 检查FunASR服务状态")
        print("      2. 确认服务器配置: ASR: FunASR")
        print("      3. 检查网络连接到47.122.144.73:8000")
        
    elif not steps['stt_result']:
        print("❌ STT结果解析失败")
        print("   原因: 响应格式不符合ESP32标准")
        print("   解决:")
        print("      1. 检查服务器STT响应格式")
        print("      2. 确认发送{\"type\": \"stt\", \"text\": \"...\"}")
        print("      3. 验证WebSocket消息解析逻辑")
        
        if server_messages:
            print("   📋 检测到的服务器消息:")
            for msg in server_messages[-3:]:  # 显示最后3条
                print(f"      {msg}")
    
    else:
        print("❌ UI更新失败")
        print("   原因: ChatViewModel中STT处理逻辑问题")
        print("   解决: 检查observeProtocolMessages()中STT分支")

def check_server_stt_config():
    """检查服务器STT配置"""
    print("\n📋 ESP32服务器STT配置信息:")
    print("   配置文件: xiaozhi-server/config.yaml")
    print("   选择模块: selected_module.ASR: FunASR")
    print("   提供者: core/providers/asr/fun_local.py")
    print("   响应格式: {\"type\": \"stt\", \"text\": \"识别文本\", \"session_id\": \"xxx\"}")
    print("   工作原理:")
    print("      1. 接收Opus音频数据")
    print("      2. 使用FunASR模型进行STT")
    print("      3. 返回标准格式的STT响应")
    print("      4. Android端解析并显示结果")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        check_server_stt_config()
    else:
        test_android_stt_flow() 