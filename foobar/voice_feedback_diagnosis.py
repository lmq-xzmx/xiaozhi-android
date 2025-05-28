#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音反馈诊断工具
检查语音识别和服务器响应问题
"""

import subprocess
import time
import datetime

def check_voice_feedback():
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("🎤 语音反馈诊断工具")
    print("=" * 50)
    
    # 1. 获取最近的所有日志
    print("1. 检查最近的语音相关日志...")
    result = subprocess.run(
        ["adb", "-s", device_id, "logcat", "-d"],
        capture_output=True,
        text=True
    )
    
    logs = result.stdout.split('\n')
    
    # 2. 分析关键时间点（最近20分钟）
    current_time = datetime.datetime.now()
    target_time = current_time - datetime.timedelta(minutes=20)
    
    print(f"检查时间范围: {target_time.strftime('%H:%M')} - {current_time.strftime('%H:%M')}")
    
    # 3. 查找关键日志模式
    voice_logs = []
    websocket_logs = []
    error_logs = []
    
    for line in logs:
        line_lower = line.lower()
        
        # 语音相关日志
        if any(keyword in line_lower for keyword in [
            'stt', 'speech', 'listen', 'audio', 'voice', 'microphone', 'record'
        ]):
            voice_logs.append(line)
        
        # WebSocket通信日志
        if any(keyword in line_lower for keyword in [
            'websocket', 'ws:', 'received text message', 'sending text'
        ]):
            websocket_logs.append(line)
        
        # 错误日志
        if any(keyword in line_lower for keyword in [
            'error', 'exception', 'failed', 'timeout', 'denied'
        ]):
            error_logs.append(line)
    
    # 4. 分析语音流程
    print(f"\n2. 语音相关日志分析 (找到 {len(voice_logs)} 条):")
    if voice_logs:
        print("   最近的语音日志:")
        for log in voice_logs[-10:]:  # 最后10条
            if log.strip():
                print(f"   📋 {log.strip()}")
    else:
        print("   ⚠️ 未找到语音相关日志")
    
    # 5. 分析WebSocket通信
    print(f"\n3. WebSocket通信分析 (找到 {len(websocket_logs)} 条):")
    if websocket_logs:
        print("   最近的WebSocket日志:")
        for log in websocket_logs[-10:]:  # 最后10条
            if log.strip():
                print(f"   🌐 {log.strip()}")
        
        # 检查是否有服务器响应
        server_responses = [log for log in websocket_logs if 'received text message' in log.lower()]
        if server_responses:
            print(f"\n   ✅ 发现 {len(server_responses)} 条服务器响应")
            for response in server_responses[-5:]:
                print(f"   📨 {response.strip()}")
        else:
            print("   ❌ 未发现服务器响应")
    else:
        print("   ⚠️ 未找到WebSocket通信日志")
    
    # 6. 分析错误情况
    print(f"\n4. 错误日志分析 (找到 {len(error_logs)} 条):")
    if error_logs:
        print("   最近的错误:")
        for log in error_logs[-5:]:  # 最后5条错误
            if log.strip():
                print(f"   ❌ {log.strip()}")
    else:
        print("   ✅ 未发现明显错误")
    
    # 7. 权限检查
    print("\n5. 权限状态检查:")
    
    # 检查录音权限
    perm_result = subprocess.run(
        ["adb", "-s", device_id, "shell", "dumpsys", "package", "info.dourok.voicebot", 
         "|", "grep", "-A", "10", "permissions"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    if "android.permission.RECORD_AUDIO" in perm_result.stdout:
        print("   🎤 录音权限: ✅ 已授予")
    else:
        print("   🎤 录音权限: ❌ 可能未授予")
    
    # 8. 实时监控建议
    print("\n6. 实时监控建议:")
    print("   如果需要实时查看语音反馈，请运行:")
    print(f"   adb -s {device_id} logcat | grep -E \"stt|STT|listen|speak|audio|WS.*Received\"")
    
    # 9. 诊断结论
    print("\n7. 诊断结论:")
    
    has_audio_logs = len(voice_logs) > 0
    has_websocket = len(websocket_logs) > 0
    has_responses = any('received text message' in log.lower() for log in websocket_logs)
    
    if has_responses:
        print("   ✅ 服务器有响应，语音功能正常")
    elif has_websocket and not has_responses:
        print("   ⚠️ WebSocket连接正常，但无服务器响应")
        print("   建议检查:")
        print("     - 是否点击了'开始监听'按钮")
        print("     - 是否对着麦克风说话")
        print("     - 麦克风是否工作正常")
    elif not has_websocket:
        print("   ❌ WebSocket连接可能有问题")
        print("   建议重新启动应用")
    else:
        print("   ❓ 需要更多信息进行诊断")
    
    # 10. 测试步骤
    print("\n8. 测试步骤建议:")
    print("   1. 确保应用显示 '✅ 就绪' 状态")
    print("   2. 点击 '开始监听' 按钮")
    print("   3. 观察状态变为 '🎤 监听中'")
    print("   4. 清晰地说话，如：'你好，小智'")
    print("   5. 等待3-5秒观察反馈")
    print("   6. 如无反馈，点击'停止监听'再重试")

def start_realtime_monitor():
    """启动实时监控"""
    device_id = "SOZ95PIFVS5H6PIZ"
    
    print("\n🔄 启动实时语音反馈监控...")
    print("按 Ctrl+C 停止监控")
    print("=" * 50)
    
    try:
        process = subprocess.Popen(
            ["adb", "-s", device_id, "logcat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if any(keyword in line.lower() for keyword in [
                'stt', 'speech', 'listen', 'audio', 'voice', 'received text message',
                'sending text', 'websocket', 'device state'
            ]):
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {line}")
                
    except KeyboardInterrupt:
        print("\n监控已停止")
        process.terminate()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        start_realtime_monitor()
    else:
        check_voice_feedback()
        print("\n💡 提示: 使用 --monitor 参数启动实时监控") 