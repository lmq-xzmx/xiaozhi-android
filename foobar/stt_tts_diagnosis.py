#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT/TTS环节精确诊断工具
专门检查语音识别和TTS响应的每个环节
"""

import subprocess
import time
import json
import re
from datetime import datetime

def analyze_stt_tts_flow():
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("🔍 STT/TTS环节精确诊断")
    print("=" * 60)
    
    # 清除旧日志，开始新的测试
    print("1. 清除旧日志，准备新测试...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"], capture_output=True)
    
    print("2. 请按以下步骤操作:")
    print("   👆 点击'开始监听'按钮")
    print("   🗣️ 清晰地说：'你好小智'")
    print("   ⏱️ 等待10秒...")
    print("   📋 然后按Enter继续分析")
    
    input("按Enter开始监控...")
    
    # 开始实时监控
    print("\n🔄 开始15秒实时监控...")
    start_time = time.time()
    collected_logs = []
    
    process = subprocess.Popen(
        ["adb", "-s", device_id, "logcat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        while time.time() - start_time < 15:  # 监控15秒
            line = process.stdout.readline()
            if line:
                collected_logs.append(line.strip())
                # 实时显示关键信息
                if any(keyword in line.lower() for keyword in [
                    'listen', 'audio', 'recording', 'stt', 'tts', 'received text message'
                ]):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
    except:
        pass
    finally:
        process.terminate()
    
    print(f"\n📊 分析收集到的 {len(collected_logs)} 条日志...")
    
    # 分析每个关键环节
    analyze_audio_recording(collected_logs)
    analyze_websocket_transmission(collected_logs)
    analyze_server_responses(collected_logs)
    analyze_stt_results(collected_logs)
    analyze_tts_responses(collected_logs)
    
    # 给出诊断结论
    provide_diagnosis(collected_logs)

def analyze_audio_recording(logs):
    """分析音频录制环节"""
    print("\n🎤 环节1: 音频录制分析")
    print("-" * 30)
    
    recording_logs = [log for log in logs if any(keyword in log.lower() for keyword in [
        'audiorecord', 'recording', 'audio recording', 'microphone'
    ])]
    
    if recording_logs:
        print(f"   ✅ 发现 {len(recording_logs)} 条录音相关日志")
        for log in recording_logs[-3:]:  # 显示最后3条
            print(f"   📋 {log}")
    else:
        print("   ❌ 未发现录音相关日志")
        print("   🔧 可能问题: 录音组件未启动或权限问题")

def analyze_websocket_transmission(logs):
    """分析WebSocket音频传输环节"""
    print("\n🌐 环节2: WebSocket音频传输分析")
    print("-" * 40)
    
    # 查找音频数据发送
    audio_send_logs = [log for log in logs if any(keyword in log.lower() for keyword in [
        'sending audio', 'audio frame', 'opus data'
    ])]
    
    # 查找WebSocket发送日志
    ws_send_logs = [log for log in logs if 'sending text' in log.lower() and 'listen' in log.lower()]
    
    if ws_send_logs:
        print(f"   ✅ WebSocket监听命令已发送 ({len(ws_send_logs)} 次)")
        for log in ws_send_logs:
            print(f"   📤 {log}")
    else:
        print("   ❌ 未发现WebSocket监听命令")
    
    if audio_send_logs:
        print(f"   ✅ 音频数据传输正常 ({len(audio_send_logs)} 条)")
        print(f"   📤 {audio_send_logs[-1]}")  # 最后一条
    else:
        print("   ❌ 未发现音频数据传输日志")
        print("   🔧 可能问题: 音频编码失败或WebSocket断开")

def analyze_server_responses(logs):
    """分析服务器响应环节"""
    print("\n📨 环节3: 服务器响应分析")
    print("-" * 35)
    
    # 查找服务器响应
    server_response_logs = [log for log in logs if 'received text message' in log.lower()]
    
    if server_response_logs:
        print(f"   ✅ 收到 {len(server_response_logs)} 条服务器响应")
        
        for i, log in enumerate(server_response_logs):
            print(f"   📨 响应 {i+1}: {log}")
            
            # 尝试解析响应内容
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', log)
                if json_match:
                    json_str = json_match.group()
                    response_data = json.loads(json_str)
                    response_type = response_data.get('type', 'unknown')
                    print(f"      📋 响应类型: {response_type}")
                    
                    if response_type == 'stt':
                        text = response_data.get('text', '')
                        print(f"      🗣️ STT结果: '{text}'")
                    elif response_type == 'tts':
                        text = response_data.get('text', '')
                        print(f"      🔊 TTS文本: '{text}'")
            except:
                print(f"      ⚠️ 无法解析响应内容")
    else:
        print("   ❌ 未收到任何服务器响应")
        print("   🔧 可能问题: 服务器STT服务异常或网络问题")

def analyze_stt_results(logs):
    """分析STT识别结果"""
    print("\n🗣️ 环节4: STT识别结果分析")
    print("-" * 35)
    
    stt_logs = [log for log in logs if 'stt' in log.lower() and 'text' in log.lower()]
    
    if stt_logs:
        print(f"   ✅ 发现 {len(stt_logs)} 条STT结果")
        for log in stt_logs:
            print(f"   🎯 {log}")
    else:
        print("   ❌ 未发现STT识别结果")
        print("   🔧 可能问题:")
        print("      - 音频质量问题（噪音、音量太小）")
        print("      - 服务器STT服务异常")
        print("      - 音频格式不兼容")

def analyze_tts_responses(logs):
    """分析TTS响应"""
    print("\n🔊 环节5: TTS响应分析")
    print("-" * 30)
    
    tts_logs = [log for log in logs if 'tts' in log.lower()]
    
    if tts_logs:
        print(f"   ✅ 发现 {len(tts_logs)} 条TTS响应")
        for log in tts_logs:
            print(f"   🎵 {log}")
    else:
        print("   ❌ 未发现TTS响应")
        print("   🔧 可能问题:")
        print("      - LLM服务异常")
        print("      - TTS服务异常")
        print("      - STT识别失败导致无后续处理")

def analyze_chat_ui_updates(logs):
    """分析聊天界面更新"""
    print("\n💬 环节6: 聊天界面更新分析")
    print("-" * 35)
    
    chat_logs = [log for log in logs if any(keyword in log.lower() for keyword in [
        'chatviewmodel', 'message added', 'device state'
    ])]
    
    if chat_logs:
        print(f"   ✅ 发现 {len(chat_logs)} 条界面更新日志")
        for log in chat_logs[-5:]:  # 最后5条
            print(f"   💬 {log}")
    else:
        print("   ❌ 未发现界面更新日志")

def provide_diagnosis(logs):
    """提供诊断结论"""
    print("\n🎯 诊断结论")
    print("=" * 50)
    
    # 检查各个环节
    has_recording = any('recording' in log.lower() for log in logs)
    has_ws_listen = any('sending text' in log.lower() and 'listen' in log.lower() for log in logs)
    has_server_response = any('received text message' in log.lower() for log in logs)
    has_stt = any('stt' in log.lower() and 'text' in log.lower() for log in logs)
    has_tts = any('tts' in log.lower() for log in logs)
    
    print(f"📊 环节检查结果:")
    print(f"   🎤 音频录制: {'✅' if has_recording else '❌'}")
    print(f"   🌐 WebSocket监听: {'✅' if has_ws_listen else '❌'}")
    print(f"   📨 服务器响应: {'✅' if has_server_response else '❌'}")
    print(f"   🗣️ STT识别: {'✅' if has_stt else '❌'}")
    print(f"   🔊 TTS响应: {'✅' if has_tts else '❌'}")
    
    # 问题定位
    if not has_recording:
        print("\n❌ 问题定位: 音频录制环节")
        print("🔧 解决方案:")
        print("   - 检查麦克风权限")
        print("   - 重启应用")
        print("   - 检查设备麦克风硬件")
    elif not has_ws_listen:
        print("\n❌ 问题定位: WebSocket监听环节")
        print("🔧 解决方案:")
        print("   - 检查WebSocket连接状态")
        print("   - 重新建立连接")
    elif not has_server_response:
        print("\n❌ 问题定位: 服务器响应环节")
        print("🔧 解决方案:")
        print("   - 检查服务器状态")
        print("   - 检查网络连接")
        print("   - 确认音频数据传输")
    elif not has_stt:
        print("\n❌ 问题定位: STT识别环节")
        print("🔧 解决方案:")
        print("   - 提高说话音量和清晰度")
        print("   - 减少环境噪音")
        print("   - 检查服务器STT服务")
    elif not has_tts:
        print("\n❌ 问题定位: TTS响应环节")
        print("🔧 解决方案:")
        print("   - 检查服务器LLM服务")
        print("   - 检查服务器TTS服务")
    else:
        print("\n✅ 所有环节都有日志，可能是:")
        print("   - 响应延迟较大")
        print("   - 界面更新问题")
        print("   - 需要查看详细响应内容")

def check_current_status():
    """检查当前应用状态"""
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("📱 当前应用状态检查")
    print("-" * 30)
    
    # 检查应用是否运行
    result = subprocess.run(
        ["adb", "-s", device_id, "shell", "ps", "|", "grep", "voicebot"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    if "info.dourok.voicebot" in result.stdout:
        print("   ✅ 应用正在运行")
    else:
        print("   ❌ 应用未运行")
        return
    
    # 检查最新日志状态
    result = subprocess.run(
        ["adb", "-s", device_id, "logcat", "-d", "|", "tail", "-20"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    recent_logs = result.stdout
    if "websocket" in recent_logs.lower():
        print("   ✅ WebSocket连接活跃")
    else:
        print("   ⚠️ WebSocket连接可能不活跃")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        check_current_status()
    else:
        analyze_stt_tts_flow() 