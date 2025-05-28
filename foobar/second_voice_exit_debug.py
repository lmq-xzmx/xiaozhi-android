#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二句语音退出问题专门调试脚本
详细分析音频流程和资源管理问题
"""

import subprocess
import time
import threading
import queue
import re

def debug_second_voice_exit():
    """调试第二句语音退出问题"""
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🔍 第二句语音退出问题专门调试")
    print("=" * 60)
    
    # 安装修复后的APK
    print("1. 安装修复后的APK...")
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
    
    # 重启应用确保干净状态
    print("2. 重启应用...")
    try:
        # 停止应用
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "force-stop", package_name
        ], timeout=5)
        time.sleep(1)
        
        # 启动应用
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
    
    # 开始详细监控
    print("4. 开始详细监控...")
    print("\n" + "🎯 测试流程：")
    print("   📱 第一轮对话：")
    print("     1. 点击 '开始语音对话' 按钮")
    print("     2. 说第一句话：'你好小智'")
    print("     3. 等待TTS播放完成，自动恢复监听")
    print("   📱 第二轮对话：")
    print("     4. 说第二句话：'请介绍一下你自己'")
    print("     5. 观察是否会退出或崩溃")
    print("   📱 第三轮对话（如果成功）：")
    print("     6. 说第三句话：'今天天气怎么样'")
    print("     7. 验证连续对话稳定性\n")
    
    # 创建专门的分析器
    analyzer = SecondVoiceExitAnalyzer()
    
    try:
        # 启动logcat监控
        logcat_process = subprocess.Popen([
            "adb", "-s", device_id, "logcat", "-v", "time", 
            "*:W", "ChatViewModel:*", "AudioRecorder:*", "AndroidRuntime:*"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # 启动分析线程
        analysis_thread = threading.Thread(
            target=analyzer.analyze_logs, 
            args=(logcat_process,),
            daemon=True
        )
        analysis_thread.start()
        
        print("🎤 开始监控第二句语音问题...")
        print("   按 Ctrl+C 停止监控\n")
        
        # 主循环
        last_status_time = time.time()
        while True:
            time.sleep(1)
            
            # 每5秒输出一次状态
            if time.time() - last_status_time > 5:
                analyzer.print_status()
                last_status_time = time.time()
                
    except KeyboardInterrupt:
        print("\n🛑 监控停止")
        logcat_process.terminate()
        
        # 输出最终分析结果
        analyzer.print_final_analysis()

class SecondVoiceExitAnalyzer:
    def __init__(self):
        # 对话轮次追踪
        self.current_round = 0
        self.max_rounds = 3
        
        # 状态追踪
        self.device_states = []
        self.audio_flow_events = []
        self.resource_events = []
        self.error_events = []
        self.crash_events = []
        
        # 轮次状态
        self.round_status = {
            1: {"started": False, "tts_played": False, "auto_resumed": False, "completed": False},
            2: {"started": False, "tts_played": False, "auto_resumed": False, "completed": False},
            3: {"started": False, "tts_played": False, "auto_resumed": False, "completed": False}
        }
        
        # 问题检测
        self.app_crashed = False
        self.second_voice_failed = False
        self.audio_resource_conflict = False
        
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
        
        # 设备状态变化分析
        if "ChatViewModel" in line and "设备状态变更" in line:
            self.process_device_state_change(line, timestamp)
        
        # 音频流程分析
        elif "AudioRecorder" in line or ("ChatViewModel" in line and any(keyword in line for keyword in [
            "音频流程", "录音", "音频数据", "Opus编码"
        ])):
            self.process_audio_flow_event(line, timestamp)
        
        # 资源管理分析
        elif any(keyword in line for keyword in [
            "资源", "释放", "初始化", "停止", "创建", "release", "stop", "start"
        ]) and ("ChatViewModel" in line or "AudioRecorder" in line):
            self.process_resource_event(line, timestamp)
        
        # TTS播放分析
        elif "ChatViewModel" in line and any(keyword in line for keyword in [
            "TTS播放", "TTS开始", "TTS结束", "自动恢复监听"
        ]):
            self.process_tts_event(line, timestamp)
        
        # 错误和崩溃分析
        elif any(keyword in line for keyword in [
            "ERROR", "Exception", "FATAL", "AndroidRuntime", "失败", "错误", "异常"
        ]):
            self.process_error_event(line, timestamp)
    
    def extract_timestamp(self, line):
        """提取时间戳"""
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        return match.group(1) if match else "unknown"
    
    def process_device_state_change(self, line, timestamp):
        """处理设备状态变化"""
        if "->" in line:
            state_change = line.split("设备状态变更:")[-1].strip()
            self.device_states.append((timestamp, state_change))
            
            print(f"📊 {timestamp} 状态变更: {state_change}")
            
            # 判断对话轮次
            if "LISTENING" in state_change and "IDLE -> LISTENING" in state_change:
                self.current_round += 1
                if self.current_round <= self.max_rounds:
                    self.round_status[self.current_round]["started"] = True
                    print(f"   🎯 第{self.current_round}轮对话开始")
            
            elif "SPEAKING" in state_change:
                if self.current_round <= self.max_rounds:
                    self.round_status[self.current_round]["tts_played"] = True
                    print(f"   🔊 第{self.current_round}轮TTS播放")
    
    def process_audio_flow_event(self, line, timestamp):
        """处理音频流程事件"""
        self.audio_flow_events.append((timestamp, line))
        
        if "启动ESP32兼容的持续音频流程" in line:
            print(f"🎵 {timestamp} 音频流程启动")
        elif "音频流程已结束" in line:
            print(f"🎵 {timestamp} 音频流程结束")
        elif "音频流程已在运行" in line:
            print(f"⚠️ {timestamp} 音频流程冲突 - 重复启动")
            self.audio_resource_conflict = True
        elif "Recording already in progress" in line:
            print(f"⚠️ {timestamp} 录音资源冲突")
            self.audio_resource_conflict = True
    
    def process_resource_event(self, line, timestamp):
        """处理资源管理事件"""
        self.resource_events.append((timestamp, line))
        
        if "AudioRecord released" in line:
            print(f"🧹 {timestamp} AudioRecord已释放")
        elif "Audio channel closed" in line:
            print(f"🧹 {timestamp} 音频通道已关闭")
    
    def process_tts_event(self, line, timestamp):
        """处理TTS事件"""
        if "TTS播放完成" in line and self.current_round <= self.max_rounds:
            self.round_status[self.current_round]["completed"] = True
            print(f"✅ {timestamp} 第{self.current_round}轮TTS播放完成")
        
        elif "自动恢复监听状态" in line and self.current_round <= self.max_rounds:
            self.round_status[self.current_round]["auto_resumed"] = True
            print(f"🔄 {timestamp} 第{self.current_round}轮自动恢复监听")
    
    def process_error_event(self, line, timestamp):
        """处理错误事件"""
        self.error_events.append((timestamp, line))
        
        if "FATAL" in line or "AndroidRuntime" in line:
            self.app_crashed = True
            self.crash_events.append((timestamp, line))
            print(f"💥 {timestamp} 应用崩溃: {line}")
        elif "Exception" in line and "ChatViewModel" in line:
            print(f"❌ {timestamp} ChatViewModel异常: {line}")
        elif "失败" in line or "错误" in line:
            print(f"⚠️ {timestamp} 错误: {line}")
    
    def print_status(self):
        """输出当前状态"""
        print(f"\n📋 当前状态 (第{self.current_round}轮):")
        
        for round_num in range(1, self.max_rounds + 1):
            status = self.round_status[round_num]
            if round_num <= self.current_round:
                print(f"   第{round_num}轮: 开始{'✅' if status['started'] else '❌'} "
                      f"TTS{'✅' if status['tts_played'] else '❌'} "
                      f"恢复{'✅' if status['auto_resumed'] else '❌'} "
                      f"完成{'✅' if status['completed'] else '❌'}")
            else:
                print(f"   第{round_num}轮: 未开始")
        
        print(f"   应用状态: {'💥 崩溃' if self.app_crashed else '✅ 正常'}")
        print(f"   资源冲突: {'⚠️ 发现' if self.audio_resource_conflict else '✅ 无'}")
        print(f"   状态变更: {len(self.device_states)} 次")
        print(f"   音频事件: {len(self.audio_flow_events)} 次")
        print(f"   错误事件: {len(self.error_events)} 次")
    
    def print_final_analysis(self):
        """输出最终分析结果"""
        print("\n" + "=" * 60)
        print("📊 第二句语音退出问题最终分析")
        print("=" * 60)
        
        # 对话完成度分析
        print("\n🎯 对话完成度分析:")
        for round_num in range(1, self.max_rounds + 1):
            status = self.round_status[round_num]
            if round_num <= self.current_round:
                completion = sum([
                    status['started'], status['tts_played'], 
                    status['auto_resumed'], status['completed']
                ])
                print(f"   第{round_num}轮: {completion}/4 步骤完成 ({'✅ 成功' if completion == 4 else '❌ 未完成'})")
        
        # 问题诊断
        print(f"\n🔍 问题诊断:")
        if self.app_crashed:
            print("   💥 发现应用崩溃")
            if self.crash_events:
                print("   崩溃详情:")
                for timestamp, event in self.crash_events[-3:]:
                    print(f"     {timestamp}: {event}")
        
        if self.audio_resource_conflict:
            print("   ⚠️ 发现音频资源冲突")
        
        if self.current_round < 2:
            print("   🎯 第二轮对话未开始 - 可能第一轮就有问题")
        elif not self.round_status[2]["started"]:
            print("   🎯 第二轮对话启动失败")
        elif not self.round_status[2]["auto_resumed"]:
            print("   🎯 第二轮对话自动恢复失败")
        
        # 修复建议
        print(f"\n💡 修复建议:")
        if self.app_crashed:
            print("   1. 查看完整崩溃堆栈追踪")
            print("   2. 检查内存泄漏和资源管理")
        if self.audio_resource_conflict:
            print("   3. 优化音频资源释放时序")
            print("   4. 添加资源状态检查")
        if self.current_round >= 2:
            print("   5. 连续对话功能基本正常，继续优化细节")
        else:
            print("   5. 修复基础对话流程问题")

if __name__ == "__main__":
    debug_second_voice_exit() 