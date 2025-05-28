#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智语音交互卡顿问题专用诊断脚本
针对"说着说着又开始卡了"的问题进行实时监控和诊断
"""

import time
import psutil
import subprocess
import json
import threading
from datetime import datetime
import os
import signal
import sys

class VoiceInterruptDiagnoser:
    def __init__(self):
        self.monitoring = False
        self.log_file = f"voice_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.audio_stats = {
            'audio_frames_processed': 0,
            'tts_packets_received': 0,
            'audio_buffer_overflows': 0,
            'memory_warnings': 0,
            'last_audio_time': None
        }
        
        print("🔍 小智语音交互卡顿诊断工具 v1.0")
        print("=" * 50)
        
    def log_message(self, level, message):
        """记录诊断日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def check_system_resources(self):
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # 检查是否有资源压力
            if cpu_percent > 80:
                self.log_message("WARNING", f"CPU使用率过高: {cpu_percent:.1f}%")
                return False
                
            if memory_percent > 85:
                self.log_message("WARNING", f"内存使用率过高: {memory_percent:.1f}% (可用: {memory_available:.1f}GB)")
                return False
                
            if memory_available < 0.5:
                self.log_message("WARNING", f"可用内存不足: {memory_available:.1f}GB")
                return False
                
            self.log_message("INFO", f"系统资源正常 - CPU: {cpu_percent:.1f}%, 内存: {memory_percent:.1f}%")
            return True
            
        except Exception as e:
            self.log_message("ERROR", f"检查系统资源失败: {e}")
            return False
    
    def check_android_process(self):
        """检查Android应用进程状态"""
        try:
            # 使用adb检查应用进程
            result = subprocess.run([
                'adb', 'shell', 'ps | grep voicebot'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                self.log_message("INFO", "Android应用进程运行正常")
                
                # 检查应用内存使用
                try:
                    mem_result = subprocess.run([
                        'adb', 'shell', 'dumpsys', 'meminfo', 'info.dourok.voicebot'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if mem_result.returncode == 0:
                        # 解析内存信息
                        lines = mem_result.stdout.split('\n')
                        for line in lines:
                            if 'TOTAL' in line and 'PSS' in line:
                                # 提取PSS内存使用量
                                parts = line.split()
                                if len(parts) >= 2:
                                    pss_kb = parts[1]
                                    pss_mb = int(pss_kb) / 1024
                                    self.log_message("INFO", f"应用内存使用: {pss_mb:.1f}MB")
                                    
                                    if pss_mb > 300:  # 超过300MB警告
                                        self.log_message("WARNING", f"应用内存使用偏高: {pss_mb:.1f}MB")
                                        self.audio_stats['memory_warnings'] += 1
                                        return False
                                break
                        
                except subprocess.TimeoutExpired:
                    self.log_message("WARNING", "获取应用内存信息超时")
                    
                return True
            else:
                self.log_message("ERROR", "Android应用进程未找到或异常")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("ERROR", "检查Android进程超时")
            return False
        except Exception as e:
            self.log_message("ERROR", f"检查Android进程失败: {e}")
            return False
    
    def monitor_audio_logs(self):
        """监控Android应用的音频相关日志"""
        try:
            # 清空logcat缓冲区
            subprocess.run(['adb', 'logcat', '-c'], timeout=5)
            
            # 开始监控特定标签的日志
            process = subprocess.Popen([
                'adb', 'logcat', '-s', 'ChatViewModel:*', 'OpusDecoder:*', 'OpusEncoder:*', 'AudioRecorder:*', 'OpusStreamPlayer:*'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            
            self.log_message("INFO", "开始监控Android音频日志...")
            
            audio_frame_count = 0
            last_frame_time = time.time()
            
            while self.monitoring:
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                    
                    current_time = time.time()
                    
                    # 分析关键日志模式
                    if "音频数据发送" in line or "TTS音频数据已缓冲" in line:
                        audio_frame_count += 1
                        self.audio_stats['audio_frames_processed'] = audio_frame_count
                        self.audio_stats['last_audio_time'] = current_time
                        
                        # 检查音频处理频率
                        time_diff = current_time - last_frame_time
                        if time_diff > 0.2:  # 超过200ms没有音频帧
                            self.log_message("WARNING", f"音频处理间隔过长: {time_diff:.3f}秒")
                        
                        last_frame_time = current_time
                        
                        # 每100帧统计一次
                        if audio_frame_count % 100 == 0:
                            self.log_message("INFO", f"已处理音频帧: {audio_frame_count}")
                    
                    elif "TTS音频缓冲区较大" in line:
                        self.log_message("WARNING", "检测到TTS音频缓冲区积累")
                        self.audio_stats['audio_buffer_overflows'] += 1
                        
                    elif "Opus解码失败" in line or "音频处理失败" in line:
                        self.log_message("ERROR", f"音频处理错误: {line}")
                        
                    elif "ESP32兼容模式：自动恢复监听状态" in line:
                        self.log_message("INFO", "检测到监听状态恢复")
                        
                    elif "TTS播放完成" in line:
                        self.log_message("INFO", "TTS播放周期完成")
                        
                    elif "设备状态变更" in line:
                        self.log_message("INFO", f"状态变更: {line}")
                        
                except Exception as e:
                    self.log_message("ERROR", f"日志监控异常: {e}")
                    break
            
            process.terminate()
            
        except Exception as e:
            self.log_message("ERROR", f"音频日志监控失败: {e}")
    
    def detect_stuttering_patterns(self):
        """检测卡顿模式"""
        current_time = time.time()
        
        # 检查音频流中断
        if self.audio_stats['last_audio_time']:
            time_since_last_audio = current_time - self.audio_stats['last_audio_time']
            if time_since_last_audio > 5.0:  # 超过5秒没有音频活动
                self.log_message("CRITICAL", f"检测到音频流中断: {time_since_last_audio:.1f}秒无音频活动")
                return True
        
        # 检查缓冲区溢出
        if self.audio_stats['audio_buffer_overflows'] > 3:
            self.log_message("CRITICAL", f"频繁的音频缓冲区溢出: {self.audio_stats['audio_buffer_overflows']}次")
            return True
        
        # 检查内存警告
        if self.audio_stats['memory_warnings'] > 2:
            self.log_message("CRITICAL", f"频繁的内存警告: {self.audio_stats['memory_warnings']}次")
            return True
        
        return False
    
    def generate_optimization_suggestions(self):
        """根据诊断结果生成优化建议"""
        suggestions = []
        
        if self.audio_stats['audio_buffer_overflows'] > 0:
            suggestions.append("🔧 优化音频缓冲区管理：减少缓冲区大小或增加处理频率")
            
        if self.audio_stats['memory_warnings'] > 0:
            suggestions.append("🧹 优化内存管理：增加垃圾回收频率，释放无用对象")
            
        if self.audio_stats['audio_frames_processed'] < 100:
            suggestions.append("🎤 检查音频录制：确保麦克风权限正常，音频设备工作正常")
            
        # 通用优化建议
        suggestions.extend([
            "📱 重启应用：重新初始化音频组件和内存状态",
            "🔄 检查网络：确保WebSocket连接稳定",
            "⚡ 降低音频质量：临时使用较低的采样率或比特率",
            "🚫 关闭后台应用：释放系统资源给语音应用",
            "🔊 检查音量设置：确保系统音量和应用音量适中"
        ])
        
        return suggestions
    
    def run_comprehensive_diagnosis(self):
        """运行完整诊断"""
        self.monitoring = True
        self.log_message("INFO", "开始语音交互卡顿诊断...")
        
        try:
            # 1. 系统资源检查
            self.log_message("INFO", "步骤1: 检查系统资源...")
            system_ok = self.check_system_resources()
            
            # 2. Android进程检查
            self.log_message("INFO", "步骤2: 检查Android应用状态...")
            process_ok = self.check_android_process()
            
            # 3. 启动日志监控（在后台线程中）
            self.log_message("INFO", "步骤3: 启动音频日志监控...")
            log_thread = threading.Thread(target=self.monitor_audio_logs, daemon=True)
            log_thread.start()
            
            # 4. 持续监控30秒
            self.log_message("INFO", "步骤4: 持续监控30秒...")
            for i in range(30):
                time.sleep(1)
                
                # 每5秒检查一次卡顿模式
                if (i + 1) % 5 == 0:
                    stuttering = self.detect_stuttering_patterns()
                    if stuttering:
                        self.log_message("CRITICAL", f"检测到卡顿模式！(监控{i+1}秒)")
                        break
                        
                    self.log_message("INFO", f"监控进度: {i+1}/30秒")
            
            # 5. 生成诊断报告
            self.log_message("INFO", "步骤5: 生成诊断报告...")
            self.generate_diagnosis_report()
            
        except KeyboardInterrupt:
            self.log_message("INFO", "用户中断诊断")
        except Exception as e:
            self.log_message("ERROR", f"诊断过程异常: {e}")
        finally:
            self.monitoring = False
    
    def generate_diagnosis_report(self):
        """生成最终诊断报告"""
        report_file = f"voice_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 小智语音交互卡顿诊断报告\n\n")
            f.write(f"**诊断时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 统计数据\n\n")
            f.write(f"- 音频帧处理数量: {self.audio_stats['audio_frames_processed']}\n")
            f.write(f"- TTS数据包接收: {self.audio_stats['tts_packets_received']}\n")
            f.write(f"- 音频缓冲区溢出次数: {self.audio_stats['audio_buffer_overflows']}\n")
            f.write(f"- 内存警告次数: {self.audio_stats['memory_warnings']}\n\n")
            
            # 问题分析
            f.write("## 🔍 问题分析\n\n")
            if self.audio_stats['audio_buffer_overflows'] > 0:
                f.write("⚠️ **检测到音频缓冲区积累问题**\n")
                f.write("- 原因：TTS音频数据处理不及时，导致缓冲区积累\n")
                f.write("- 影响：可能导致音频播放延迟和卡顿\n\n")
            
            if self.audio_stats['memory_warnings'] > 0:
                f.write("⚠️ **检测到内存使用异常**\n")
                f.write("- 原因：应用内存使用过高，可能存在内存泄漏\n")
                f.write("- 影响：系统资源紧张，影响音频处理性能\n\n")
            
            if self.audio_stats['audio_frames_processed'] < 50:
                f.write("⚠️ **音频处理活动较少**\n")
                f.write("- 原因：可能存在音频录制或处理问题\n")
                f.write("- 影响：语音识别效果差，交互不流畅\n\n")
            
            # 优化建议
            f.write("## 🔧 优化建议\n\n")
            suggestions = self.generate_optimization_suggestions()
            for i, suggestion in enumerate(suggestions, 1):
                f.write(f"{i}. {suggestion}\n")
            
            f.write("\n## 📋 详细日志\n\n")
            f.write(f"完整日志文件: `{self.log_file}`\n\n")
            
            f.write("## 🚀 立即执行的修复方案\n\n")
            f.write("### 快速修复（建议立即执行）\n")
            f.write("1. **重启应用**: 清理内存状态和音频组件\n")
            f.write("2. **检查网络**: 确保WebSocket连接稳定\n")
            f.write("3. **清理内存**: 关闭其他应用释放内存\n\n")
            
            f.write("### 深度优化（开发层面）\n")
            f.write("1. **音频缓冲区优化**: 调整缓冲区大小和清理频率\n")
            f.write("2. **内存管理改进**: 增强垃圾回收和资源释放\n")
            f.write("3. **异常处理完善**: 提高错误恢复能力\n")
        
        self.log_message("INFO", f"诊断报告已生成: {report_file}")
        print(f"\n📄 诊断报告已保存到: {report_file}")


def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\n\n🛑 诊断已中断")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    diagnoser = VoiceInterruptDiagnoser()
    
    print("🎯 开始诊断语音交互卡顿问题...")
    print("💡 请在应用中进行语音交互，以便收集诊断数据")
    print("⏹️  按 Ctrl+C 可随时停止诊断")
    print()
    
    diagnoser.run_comprehensive_diagnosis()
    
    print("\n✅ 诊断完成！请查看生成的报告文件。") 