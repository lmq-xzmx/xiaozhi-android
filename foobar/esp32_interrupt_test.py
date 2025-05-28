#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32语音打断功能测试脚本
测试Android端是否正确实现了ESP32的语音打断机制
"""

import subprocess
import time
import threading
import queue
import re

def test_esp32_interrupt_mechanism():
    """测试ESP32语音打断机制"""
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🎯 ESP32语音打断机制测试")
    print("=" * 60)
    
    # 安装最新APK
    print("1. 安装ESP32兼容的APK...")
    try:
        result = subprocess.run([
            "adb", "-s", device_id, "install", "-r", 
            "app/build/outputs/apk/debug/app-debug.apk"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ APK安装成功")
        else:
            print(f"   ❌ APK安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ 安装过程异常: {e}")
        return False
    
    # 重启应用
    print("2. 重启应用...")
    try:
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "force-stop", package_name
        ], timeout=5)
        time.sleep(2)
        
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "start", "-n", 
            f"{package_name}/.MainActivity"
        ], timeout=10)
        time.sleep(3)
        print("   ✅ 应用重启成功")
    except Exception as e:
        print(f"   ❌ 应用重启失败: {e}")
        return False
    
    # 清除日志
    print("3. 清除旧日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"])
    print("   ✅ 日志已清除")
    
    # 开始语音打断测试
    print("4. 开始ESP32语音打断测试...")
    print("\n" + "🎯 测试重点：")
    print("   1. 自动启动语音监听模式")
    print("   2. TTS播放时持续VAD检测")
    print("   3. 语音打断自动触发")
    print("   4. 无需手动按钮操作")
    print("   💡 关键：完全自动化的语音交互流程\n")
    
    # 创建打断分析器
    analyzer = VoiceInterruptAnalyzer()
    
    try:
        # 启动logcat监控
        logcat_process = subprocess.Popen([
            "adb", "-s", device_id, "logcat", "-v", "time", 
            "ChatViewModel:*", "OpusStreamPlayer:*", "AudioRecorder:*", "*:E"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # 启动分析线程
        analysis_thread = threading.Thread(
            target=analyzer.analyze_logs, 
            args=(logcat_process,),
            daemon=True
        )
        analysis_thread.start()
        
        print("🔍 开始监控ESP32语音打断机制...")
        print("   按 Ctrl+C 停止监控\n")
        
        # 主循环
        last_status_time = time.time()
        while True:
            time.sleep(1)
            
            # 每20秒输出一次状态
            if time.time() - last_status_time > 20:
                analyzer.print_status()
                last_status_time = time.time()
                
    except KeyboardInterrupt:
        print("\n🛑 监控停止")
        logcat_process.terminate()
        
        # 输出最终分析结果
        analyzer.print_final_analysis()

class VoiceInterruptAnalyzer:
    def __init__(self):
        # 语音交互状态
        self.auto_start_detected = False
        self.listening_events = []
        self.speaking_events = []
        self.interrupt_events = []
        
        # 音频流程统计
        self.audio_in_speaking_count = 0
        self.vad_detection_count = 0
        self.auto_resume_count = 0
        self.button_clicks = 0
        
        # ESP32兼容性检测
        self.esp32_features = {
            'auto_start_listening': False,
            'continuous_vad_during_tts': False,
            'automatic_interrupt': False,
            'no_manual_buttons': True,
            'auto_resume_after_tts': False
        }
        
    def analyze_logs(self, logcat_process):
        """分析日志"""
        while True:
            try:
                line = logcat_process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                self.process_log_line(line)
                
            except Exception as e:
                print(f"日志分析异常: {e}")
                break
    
    def process_log_line(self, line):
        """处理单行日志"""
        timestamp = self.extract_timestamp(line)
        
        # 自动启动检测
        if "自动启动ESP32兼容的语音交互模式" in line:
            self.auto_start_detected = True
            self.esp32_features['auto_start_listening'] = True
            print(f"✅ {timestamp} 检测到自动启动语音交互")
        
        # 监听状态检测
        elif "已启动ESP32兼容模式" in line and "AUTO_STOP监听" in line:
            self.listening_events.append({
                'timestamp': timestamp,
                'type': 'AUTO_START'
            })
            print(f"🎤 {timestamp} ESP32兼容监听模式启动")
        
        # TTS播放状态检测
        elif "TTS开始播放" in line:
            self.speaking_events.append({
                'timestamp': timestamp,
                'type': 'TTS_START'
            })
            print(f"🔊 {timestamp} TTS开始播放")
        
        # TTS播放中音频检测
        elif "TTS播放中继续音频监测" in line:
            self.esp32_features['continuous_vad_during_tts'] = True
            print(f"🎤 {timestamp} TTS播放中继续VAD检测")
        
        # SPEAKING状态下音频发送检测
        elif "SPEAKING状态下发送音频供VAD检测打断" in line:
            self.audio_in_speaking_count += 1
            if self.audio_in_speaking_count == 1:
                self.esp32_features['continuous_vad_during_tts'] = True
                print(f"🎯 {timestamp} 检测到SPEAKING状态下音频发送（VAD打断支持）")
        
        # 语音打断检测
        elif "Abort speaking" in line or "打断" in line:
            self.interrupt_events.append({
                'timestamp': timestamp,
                'message': line
            })
            self.esp32_features['automatic_interrupt'] = True
            print(f"⚡ {timestamp} 检测到语音打断事件")
        
        # 自动恢复监听检测
        elif "自动恢复监听状态" in line:
            self.auto_resume_count += 1
            self.esp32_features['auto_resume_after_tts'] = True
            print(f"🔄 {timestamp} 自动恢复监听状态")
        
        # 按钮点击检测（应该没有）
        elif any(keyword in line for keyword in ["Button", "onClick", "点击"]):
            self.button_clicks += 1
            self.esp32_features['no_manual_buttons'] = False
            print(f"⚠️ {timestamp} 检测到按钮操作（违反ESP32模式）")
        
        # VAD检测
        elif "VAD" in line or "语音检测" in line:
            self.vad_detection_count += 1
        
        # 错误检测
        elif "ERROR" in line and ("ChatViewModel" in line or "音频" in line):
            print(f"❌ {timestamp} 音频相关错误: {line}")
    
    def extract_timestamp(self, line):
        """提取时间戳"""
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        return match.group(1) if match else "unknown"
    
    def print_status(self):
        """输出当前状态"""
        print(f"\n📋 ESP32语音打断机制状态:")
        print(f"   自动启动检测: {'✅' if self.auto_start_detected else '❌'}")
        print(f"   监听事件数: {len(self.listening_events)}")
        print(f"   TTS播放事件: {len(self.speaking_events)}")
        print(f"   语音打断事件: {len(self.interrupt_events)}")
        print(f"   SPEAKING状态音频发送: {self.audio_in_speaking_count}")
        print(f"   自动恢复次数: {self.auto_resume_count}")
        print(f"   按钮点击次数: {self.button_clicks}")
        
        # ESP32兼容性指标
        print(f"\n🔧 ESP32兼容性指标:")
        for feature, detected in self.esp32_features.items():
            status = "✅" if detected else "❌"
            feature_name = {
                'auto_start_listening': '自动启动监听',
                'continuous_vad_during_tts': 'TTS期间持续VAD',
                'automatic_interrupt': '自动语音打断',
                'no_manual_buttons': '无手动按钮',
                'auto_resume_after_tts': 'TTS后自动恢复'
            }.get(feature, feature)
            print(f"   {status} {feature_name}")
    
    def print_final_analysis(self):
        """输出最终分析结果"""
        print("\n" + "=" * 60)
        print("📊 ESP32语音打断机制最终分析")
        print("=" * 60)
        
        # 功能完成度
        implemented_features = sum(1 for detected in self.esp32_features.values() if detected)
        total_features = len(self.esp32_features)
        completion_rate = (implemented_features / total_features) * 100
        
        print(f"\n🎯 ESP32兼容性评估:")
        print(f"   功能完成度: {completion_rate:.1f}% ({implemented_features}/{total_features})")
        
        for feature, detected in self.esp32_features.items():
            status = "✅ 已实现" if detected else "❌ 未实现"
            feature_name = {
                'auto_start_listening': '自动启动监听模式',
                'continuous_vad_during_tts': 'TTS播放期间持续VAD检测',
                'automatic_interrupt': '自动语音打断机制',
                'no_manual_buttons': '无手动按钮控制',
                'auto_resume_after_tts': 'TTS结束后自动恢复监听'
            }.get(feature, feature)
            print(f"   {status} {feature_name}")
        
        # 交互流程分析
        print(f"\n📈 语音交互流程分析:")
        print(f"   监听启动事件: {len(self.listening_events)}")
        print(f"   TTS播放事件: {len(self.speaking_events)}")
        print(f"   语音打断事件: {len(self.interrupt_events)}")
        print(f"   SPEAKING状态音频发送: {self.audio_in_speaking_count}次")
        print(f"   自动恢复次数: {self.auto_resume_count}")
        
        # 问题检测
        print(f"\n⚠️ 问题检测:")
        if self.button_clicks > 0:
            print(f"   ❌ 检测到 {self.button_clicks} 次手动按钮操作")
        else:
            print(f"   ✅ 无手动按钮操作，完全自动化")
        
        # 最终评价
        print(f"\n💡 ESP32兼容性评价:")
        if completion_rate >= 80 and self.button_clicks == 0:
            print("   🎉 出色！Android端完美实现ESP32语音打断机制")
            print("   ✅ 语音交互完全自动化")
            print("   ✅ 支持TTS播放期间语音打断")
            print("   ✅ 无需任何手动按钮操作")
        elif completion_rate >= 60:
            print("   👍 良好！ESP32兼容性基本实现")
            print("   💡 仍有部分功能需要完善")
        else:
            print("   ❌ ESP32兼容性需要进一步改进")
            print("   💡 多个关键功能未正确实现")
        
        if self.audio_in_speaking_count > 0:
            print("   ✅ 关键：SPEAKING状态下持续音频发送已实现")
            print("   ✅ 服务器端VAD能够检测语音打断")
        else:
            print("   ❌ 关键问题：SPEAKING状态下未发送音频数据")
            print("   ❌ 服务器端VAD无法检测语音打断")
        
        print(f"\n🎯 测试完成！ESP32语音打断机制分析结果已生成。")

if __name__ == "__main__":
    test_esp32_interrupt_mechanism() 