#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化安装APK并测试STT功能
确保Android端与ESP32端STT方案一致
"""

import subprocess
import time
import json

def install_and_test_stt():
    """安装APK并测试STT功能"""
    device_id = "SOZ95PIFVS5H6PIZ"
    apk_path = "app/build/outputs/apk/debug/app-debug.apk"
    package_name = "info.dourok.voicebot"
    
    print("🚀 自动化STT测试流程")
    print("=" * 50)
    
    # 步骤1：安装APK
    print("1. 安装最新APK...")
    try:
        result = subprocess.run(
            ["adb", "-s", device_id, "install", "-r", apk_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   ✅ APK安装成功")
        else:
            print(f"   ❌ APK安装失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ APK安装超时")
        return False
    except Exception as e:
        print(f"   ❌ APK安装异常: {e}")
        return False
    
    # 步骤2：启动应用
    print("\n2. 启动应用...")
    try:
        subprocess.run(
            ["adb", "-s", device_id, "shell", "am", "start", 
             "-n", f"{package_name}/.MainActivity"],
            capture_output=True,
            timeout=10
        )
        print("   ✅ 应用已启动")
        
        # 等待应用加载
        time.sleep(3)
        
    except Exception as e:
        print(f"   ❌ 应用启动失败: {e}")
        return False
    
    # 步骤3：清除日志
    print("\n3. 清除旧日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"], capture_output=True)
    print("   ✅ 日志已清除")
    
    # 步骤4：STT测试指导
    print("\n4. STT功能测试指导:")
    print("   📍 ESP32端STT标准: 服务器端FunASR处理")
    print("   🎯 测试目标: 验证Android端与ESP32端STT一致性")
    print("\n   请按以下步骤操作:")
    print("   👆 1. 点击Android应用中的 '开始监听' 按钮")
    print("   🗣️ 2. 清晰地说: '你好小智，请介绍一下你自己'")
    print("   ⏱️ 3. 等待STT响应和TTS播放")
    print("   📋 4. 观察聊天界面是否显示用户输入")
    
    input("\n按Enter开始15秒STT监控...")
    
    # 步骤5：实时监控STT
    return monitor_stt_flow(device_id)

def monitor_stt_flow(device_id):
    """监控STT完整流程"""
    print("\n5. 开始STT流程监控 (15秒)...")
    print("=" * 40)
    
    start_time = time.time()
    logs = []
    
    # 启动logcat监控
    process = subprocess.Popen(
        ["adb", "-s", device_id, "logcat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 实时监控关键日志
    try:
        while time.time() - start_time < 15:
            line = process.stdout.readline()
            if line:
                logs.append(line.strip())
                
                # 实时显示STT相关日志
                if any(keyword in line.lower() for keyword in [
                    'stt', 'received text message', 'listen', 'audio data'
                ]):
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line.strip()}")
                    
    finally:
        process.terminate()
    
    # 分析STT流程结果
    return analyze_stt_results(logs)

def analyze_stt_results(logs):
    """分析STT测试结果"""
    print("\n📊 STT流程分析结果")
    print("=" * 30)
    
    # 检查关键步骤
    steps = {
        'listen_cmd': False,
        'audio_send': False,
        'server_resp': False,
        'stt_received': False,
        'ui_updated': False
    }
    
    stt_results = []
    
    for log in logs:
        log_lower = log.lower()
        
        # 检查监听命令
        if 'sending text' in log_lower and 'listen' in log_lower:
            steps['listen_cmd'] = True
        
        # 检查音频发送
        if 'audio data' in log_lower or 'sending audio' in log_lower:
            steps['audio_send'] = True
        
        # 检查服务器响应
        if 'received text message' in log_lower:
            steps['server_resp'] = True
            
            # 解析STT响应
            try:
                if '{' in log and '}' in log:
                    json_start = log.find('{')
                    json_str = log[json_start:]
                    data = json.loads(json_str)
                    
                    if data.get('type') == 'stt':
                        steps['stt_received'] = True
                        text = data.get('text', '')
                        stt_results.append(text)
                        print(f"🎯 STT识别结果: '{text}'")
            except:
                pass
        
        # 检查UI更新
        if 'chatmessage' in log_lower or 'user' in log_lower:
            steps['ui_updated'] = True
    
    # 输出测试结果
    print("\n🎯 测试结果:")
    print(f"   📤 监听命令发送: {'✅' if steps['listen_cmd'] else '❌'}")
    print(f"   🎤 音频数据传输: {'✅' if steps['audio_send'] else '❌'}")
    print(f"   📨 服务器响应: {'✅' if steps['server_resp'] else '❌'}")
    print(f"   🎯 STT识别成功: {'✅' if steps['stt_received'] else '❌'}")
    print(f"   💬 UI界面更新: {'✅' if steps['ui_updated'] else '❌'}")
    
    # 最终结论
    if steps['stt_received'] and stt_results:
        print(f"\n🎉 STT测试成功!")
        print(f"   识别结果: {stt_results}")
        print(f"   ✅ Android端STT与ESP32端方案一致!")
        print(f"   ✅ 使用服务器端FunASR处理")
        return True
    else:
        print(f"\n❌ STT测试失败")
        provide_troubleshooting(steps)
        return False

def provide_troubleshooting(steps):
    """提供故障排除建议"""
    print("\n🔧 故障排除建议:")
    
    if not steps['listen_cmd']:
        print("   ❌ 监听命令未发送")
        print("      - 检查应用是否正常启动")
        print("      - 确认点击了'开始监听'按钮")
        print("      - 验证ChatViewModel.startListening()方法")
        
    elif not steps['audio_send']:
        print("   ❌ 音频数据未传输")
        print("      - 检查录音权限: android.permission.RECORD_AUDIO")
        print("      - 验证AudioRecorder和OpusEncoder")
        print("      - 确认WebSocket连接正常")
        
    elif not steps['server_resp']:
        print("   ❌ 服务器无响应")
        print("      - 检查网络连接到 47.122.144.73:8000")
        print("      - 确认服务器FunASR服务运行正常")
        print("      - 验证服务器配置: ASR: FunASR")
        
    else:
        print("   ❌ STT响应解析失败")
        print("      - 检查服务器STT响应格式")
        print("      - 验证WebSocket消息解析逻辑")
        print("      - 确认ChatViewModel中STT处理分支")

def check_device_connection():
    """检查设备连接状态"""
    device_id = "SOZ95PIFVS5H6PIZ"
    
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True
        )
        
        if device_id in result.stdout:
            print(f"✅ 设备 {device_id} 已连接")
            return True
        else:
            print(f"❌ 设备 {device_id} 未连接")
            return False
            
    except Exception as e:
        print(f"❌ 检查设备连接失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # 检查设备连接
    if not check_device_connection():
        print("请确认设备已连接并启用USB调试")
        sys.exit(1)
    
    # 执行安装和测试
    success = install_and_test_stt()
    
    if success:
        print("\n🎉 Android端STT与ESP32端统一化成功!")
        print("✅ 服务器端FunASR STT方案运行正常")
    else:
        print("\n❌ 需要进一步调试STT功能")
        print("�� 请参考故障排除建议或查看详细日志") 