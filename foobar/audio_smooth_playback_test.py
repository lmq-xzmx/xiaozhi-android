#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频流畅播放测试脚本
专门测试修复后的Android端音频播放，检测断续卡顿问题
"""

import subprocess
import time
import threading
import queue
import re

def test_audio_smooth_playback():
    """测试音频流畅播放"""
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🎵 音频流畅播放测试")
    print("=" * 60)
    
    # 安装修复后的APK
    print("1. 安装最新修复的APK...")
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
    
    # 重启应用确保使用新版本
    print("2. 重启应用...")
    try:
        # 停止应用
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "force-stop", package_name
        ], timeout=5)
        time.sleep(2)
        
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
    
    # 开始音频播放测试
    print("4. 开始音频播放流畅性测试...")
    print("\n" + "🎯 测试步骤：")
    print("   1. 点击 '开始语音对话' 按钮")
    print("   2. 说一句话：'请详细介绍一下你自己的功能'")
    print("   3. 观察TTS音频播放是否流畅连续")
    print("   4. 重复几次对话，测试稳定性")
    print("   💡 重点观察：音频缓冲状态、播放连续性、无断续卡顿\n")
    
    # 创建音频播放分析器
    analyzer = AudioPlaybackAnalyzer()
    
    try:
        # 启动logcat监控，重点关注音频播放
        logcat_process = subprocess.Popen([
            "adb", "-s", device_id, "logcat", "-v", "time", 
            "OpusStreamPlayer:*", "ChatViewModel:*", "*:E"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # 启动分析线程
        analysis_thread = threading.Thread(
            target=analyzer.analyze_logs, 
            args=(logcat_process,),
            daemon=True
        )
        analysis_thread.start()
        
        print("🎵 开始监控音频播放流畅性...")
        print("   按 Ctrl+C 停止监控\n")
        
        # 主循环
        last_status_time = time.time()
        while True:
            time.sleep(1)
            
            # 每10秒输出一次状态
            if time.time() - last_status_time > 10:
                analyzer.print_status()
                last_status_time = time.time()
                
    except KeyboardInterrupt:
        print("\n🛑 监控停止")
        logcat_process.terminate()
        
        # 输出最终分析结果
        analyzer.print_final_analysis()

class AudioPlaybackAnalyzer:
    def __init__(self):
        # 播放质量相关
        self.buffer_events = []
        self.playback_events = []
        self.error_events = []
        self.performance_stats = []
        
        # 音频流程状态
        self.streaming_sessions = []
        self.current_session = None
        
        # 质量指标
        self.total_conversations = 0
        self.smooth_conversations = 0
        self.buffer_underruns = 0
        self.playback_errors = 0
        
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
        
        # 音频播放器相关日志
        if "OpusStreamPlayer" in line:
            self.process_audio_player_log(line, timestamp)
        
        # TTS播放流程日志
        elif "ChatViewModel" in line and any(keyword in line for keyword in [
            "TTS播放", "TTS开始", "TTS结束", "音频数据已缓冲"
        ]):
            self.process_tts_flow_log(line, timestamp)
        
        # 错误日志
        elif any(keyword in line for keyword in [
            "ERROR", "Exception", "失败", "错误", "异常"
        ]):
            self.process_error_log(line, timestamp)
    
    def extract_timestamp(self, line):
        """提取时间戳"""
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        return match.group(1) if match else "unknown"
    
    def process_audio_player_log(self, line, timestamp):
        """处理音频播放器日志"""
        
        # 流式播放启动
        if "启动流式音频播放" in line:
            self.current_session = {
                'start_time': timestamp,
                'buffer_events': [],
                'playback_events': [],
                'is_smooth': True
            }
            print(f"🎵 {timestamp} 开始新的音频播放会话")
        
        # 缓冲相关
        elif "音频数据入队" in line:
            buffer_size_match = re.search(r'队列大小: (\d+)', line)
            if buffer_size_match:
                buffer_size = int(buffer_size_match.group(1))
                event = {'timestamp': timestamp, 'type': 'buffer', 'size': buffer_size}
                self.buffer_events.append(event)
                if self.current_session:
                    self.current_session['buffer_events'].append(event)
                
                if buffer_size % 5 == 0:  # 每5个包打印一次
                    print(f"📊 {timestamp} 缓冲队列: {buffer_size} 包")
        
        elif "开始音频缓冲" in line:
            print(f"🔄 {timestamp} 开始音频缓冲过程")
        
        elif "已缓冲" in line and "开始播放" in line:
            buffer_count_match = re.search(r'已缓冲 (\d+) 个音频包', line)
            if buffer_count_match:
                buffer_count = int(buffer_count_match.group(1))
                print(f"▶️ {timestamp} 缓冲完成，开始播放 ({buffer_count} 包)")
        
        # 播放相关
        elif "开始流式播放" in line:
            print(f"🎶 {timestamp} 开始流式播放")
        
        elif "播放音频块" in line:
            written_match = re.search(r'播放音频块: (\d+)字节', line)
            remaining_match = re.search(r'PCM队列剩余: (\d+)字节', line)
            if written_match and remaining_match:
                written = int(written_match.group(1))
                remaining = int(remaining_match.group(1))
                event = {'timestamp': timestamp, 'type': 'playback', 'written': written, 'remaining': remaining}
                self.playback_events.append(event)
                if self.current_session:
                    self.current_session['playback_events'].append(event)
                
                # 每秒钟打印一次播放状态
                if len(self.playback_events) % 20 == 0:
                    print(f"🎵 {timestamp} 播放中... 写入:{written}字节 剩余:{remaining}字节")
        
        elif "流式播放结束" in line:
            print(f"🏁 {timestamp} 流式播放结束")
            if self.current_session:
                self.current_session['end_time'] = timestamp
                self.streaming_sessions.append(self.current_session)
                self.total_conversations += 1
                if self.current_session['is_smooth']:
                    self.smooth_conversations += 1
                self.current_session = None
        
        # 错误检测
        elif any(keyword in line for keyword in [
            "AudioTrack写入失败", "音频缓冲队列已满", "处理音频数据失败"
        ]):
            print(f"⚠️ {timestamp} 播放问题: {line}")
            if self.current_session:
                self.current_session['is_smooth'] = False
            
            if "缓冲队列已满" in line:
                self.buffer_underruns += 1
            elif "写入失败" in line:
                self.playback_errors += 1
    
    def process_tts_flow_log(self, line, timestamp):
        """处理TTS流程日志"""
        if "TTS开始播放" in line:
            print(f"📢 {timestamp} TTS开始播放")
        elif "TTS播放完成" in line:
            print(f"✅ {timestamp} TTS播放完成")
        elif "收到TTS音频数据" in line:
            size_match = re.search(r'(\d+) 字节', line)
            if size_match:
                size = int(size_match.group(1))
                if size > 0:
                    print(f"📡 {timestamp} 收到TTS音频: {size}字节")
    
    def process_error_log(self, line, timestamp):
        """处理错误日志"""
        self.error_events.append((timestamp, line))
        print(f"❌ {timestamp} 错误: {line}")
    
    def print_status(self):
        """输出当前状态"""
        print(f"\n📋 播放状态 (最近10秒):")
        print(f"   总对话数: {self.total_conversations}")
        print(f"   流畅对话: {self.smooth_conversations}")
        print(f"   缓冲队列大小: {len(self.buffer_events)}")
        print(f"   播放事件数: {len(self.playback_events)}")
        print(f"   缓冲不足: {self.buffer_underruns}")
        print(f"   播放错误: {self.playback_errors}")
        
        # 最近播放质量
        if self.current_session and self.current_session['playback_events']:
            recent_events = self.current_session['playback_events'][-5:]
            print(f"   最近播放: {len(recent_events)} 个音频块")
    
    def print_final_analysis(self):
        """输出最终分析结果"""
        print("\n" + "=" * 60)
        print("📊 音频播放流畅性最终分析")
        print("=" * 60)
        
        # 整体质量分析
        print(f"\n🎯 播放质量分析:")
        if self.total_conversations > 0:
            smooth_rate = (self.smooth_conversations / self.total_conversations) * 100
            print(f"   总对话数: {self.total_conversations}")
            print(f"   流畅对话: {self.smooth_conversations}")
            print(f"   流畅率: {smooth_rate:.1f}%")
        else:
            print("   未检测到完整的对话会话")
        
        # 缓冲分析
        print(f"\n📊 缓冲分析:")
        print(f"   缓冲事件: {len(self.buffer_events)}")
        print(f"   缓冲不足: {self.buffer_underruns}")
        if self.buffer_events:
            avg_buffer_size = sum(e['size'] for e in self.buffer_events[-10:]) / min(10, len(self.buffer_events))
            print(f"   平均缓冲队列: {avg_buffer_size:.1f} 包")
        
        # 播放性能分析
        print(f"\n🎵 播放性能:")
        print(f"   播放事件: {len(self.playback_events)}")
        print(f"   播放错误: {self.playback_errors}")
        if self.playback_events:
            avg_written = sum(e['written'] for e in self.playback_events[-10:]) / min(10, len(self.playback_events))
            print(f"   平均写入大小: {avg_written:.0f} 字节/块")
        
        # 错误分析
        if self.error_events:
            print(f"\n❌ 错误分析 ({len(self.error_events)} 条):")
            for timestamp, error in self.error_events[-3:]:
                print(f"   {timestamp}: {error}")
        
        # 会话详情
        if self.streaming_sessions:
            print(f"\n📈 播放会话详情:")
            for i, session in enumerate(self.streaming_sessions[-3:], 1):
                duration = "unknown"
                buffer_count = len(session.get('buffer_events', []))
                playback_count = len(session.get('playback_events', []))
                smoothness = "✅ 流畅" if session.get('is_smooth', False) else "❌ 卡顿"
                
                print(f"   会话{i}: {smoothness}, 缓冲:{buffer_count}, 播放:{playback_count}")
        
        # 修复效果评估
        print(f"\n💡 修复效果评估:")
        if self.total_conversations >= 2:
            if smooth_rate >= 80:
                print("   ✅ 音频播放流畅性显著改善")
                print("   ✅ 缓冲机制有效工作")
                print("   ✅ 断续卡顿问题基本解决")
            elif smooth_rate >= 50:
                print("   ⚠️ 音频播放有所改善，但仍需优化")
                print("   💡 建议调整缓冲参数")
            else:
                print("   ❌ 断续卡顿问题仍然存在")
                print("   💡 需要进一步分析缓冲策略")
        else:
            print("   📊 样本数据不足，建议进行更多测试")
        
        # 操作建议
        print(f"\n🔧 操作建议:")
        if self.buffer_underruns > 0:
            print(f"   - 增加缓冲区大小（当前有{self.buffer_underruns}次缓冲不足）")
        if self.playback_errors > 0:
            print(f"   - 检查AudioTrack配置（当前有{self.playback_errors}次播放错误）")
        if smooth_rate < 80:
            print(f"   - 优化音频数据预处理")
            print(f"   - 调整缓冲阈值参数")
        
        print(f"\n🎉 测试完成！音频播放流畅性修复测试结果已生成。")

if __name__ == "__main__":
    test_audio_smooth_playback() 