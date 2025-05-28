#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二轮语音断续问题修复验证脚本
验证修复后的连续对话质量
"""

import subprocess
import time
import threading
import re
from datetime import datetime

class SecondVoiceStutterFixVerifier:
    def __init__(self):
        self.device_id = "SOZ95PIFVS5H6PIZ"
        self.package_name = "info.dourok.voicebot"
        
        # 验证统计
        self.conversation_rounds = 0
        self.max_test_rounds = 5
        
        # 问题检测计数
        self.audio_flow_restart_count = 0
        self.state_change_frequency = []
        self.recording_conflicts = 0
        
        # 修复效果验证
        self.fix_verification = {
            'no_audio_flow_restart': True,
            'stable_state_display': True,
            'smooth_second_round': True,
            'reduced_state_changes': True
        }
        
        self.monitoring = True
        self.start_time = time.time()
        
    def run_verification(self):
        """运行完整的修复验证"""
        print("🎯 第二轮语音断续问题修复验证开始")
        print("=" * 60)
        
        # 1. 安装修复后的APK
        if not self.install_fixed_apk():
            return False
        
        # 2. 启动应用和日志监控
        if not self.start_app_and_monitoring():
            return False
        
        # 3. 进行连续对话测试
        self.run_continuous_conversation_test()
        
        # 4. 分析验证结果
        self.analyze_verification_results()
        
        return True
    
    def install_fixed_apk(self):
        """安装修复后的APK"""
        print("📦 安装修复后的APK...")
        try:
            result = subprocess.run([
                "adb", "-s", self.device_id, "install", "-r",
                "app/build/outputs/apk/debug/app-debug.apk"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ✅ 修复APK安装成功")
                return True
            else:
                print(f"   ❌ APK安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ❌ 安装异常: {e}")
            return False
    
    def start_app_and_monitoring(self):
        """启动应用和日志监控"""
        print("🚀 启动应用和日志监控...")
        
        try:
            # 强制停止应用
            subprocess.run([
                "adb", "-s", self.device_id, "shell", "am", "force-stop", self.package_name
            ], timeout=5)
            time.sleep(2)
            
            # 清除日志
            subprocess.run(["adb", "-s", self.device_id, "logcat", "-c"])
            
            # 启动应用
            subprocess.run([
                "adb", "-s", self.device_id, "shell", "am", "start", "-n",
                f"{self.package_name}/.MainActivity"
            ], timeout=10)
            time.sleep(5)
            
            print("   ✅ 应用启动成功，开始监控...")
            return True
            
        except Exception as e:
            print(f"   ❌ 启动失败: {e}")
            return False
    
    def run_continuous_conversation_test(self):
        """运行连续对话测试"""
        print("🎤 开始连续对话质量测试...")
        print(f"   目标：完成{self.max_test_rounds}轮连续对话")
        print("   重点：验证第二轮及后续对话的流畅性")
        print()
        
        # 启动日志监控线程
        log_thread = threading.Thread(target=self.monitor_logs, daemon=True)
        log_thread.start()
        
        try:
            # 监控测试时间
            test_duration = 120  # 2分钟测试
            print(f"📊 开始{test_duration}秒连续对话质量监控...")
            
            for i in range(test_duration):
                time.sleep(1)
                
                # 每20秒输出一次进度
                if (i + 1) % 20 == 0:
                    self.print_progress_status(i + 1)
                
                # 检查是否有严重问题
                if self.detect_critical_issues():
                    print("   ⚠️ 检测到严重问题，停止测试")
                    break
            
            print(f"\n✅ 连续对话质量监控完成")
            
        except KeyboardInterrupt:
            print("\n🛑 用户中断测试")
        finally:
            self.monitoring = False
    
    def monitor_logs(self):
        """监控应用日志"""
        try:
            process = subprocess.Popen([
                "adb", "-s", self.device_id, "logcat", "-v", "time",
                "ChatViewModel:*", "AudioRecorder:*", "*:E"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            
            while self.monitoring:
                line = process.stdout.readline()
                if not line:
                    break
                
                self.analyze_log_line(line.strip())
                
        except Exception as e:
            print(f"日志监控异常: {e}")
    
    def analyze_log_line(self, line):
        """分析单行日志"""
        if not line:
            return
        
        timestamp = self.extract_timestamp(line)
        current_time = time.time()
        
        # 1. 检测音频流重复启动（修复重点）
        if "startContinuousAudioFlow" in line and "重新启动音频录制流程" in line:
            self.audio_flow_restart_count += 1
            self.fix_verification['no_audio_flow_restart'] = False
            print(f"❌ {timestamp} 检测到音频流重启（修复失败）: 第{self.audio_flow_restart_count}次")
        
        elif "音频流程已在运行，跳过重复启动" in line:
            print(f"⚠️ {timestamp} 检测到重复启动尝试（被正确阻止）")
        
        # 2. 检测录音资源冲突
        elif "Recording already in progress" in line:
            self.recording_conflicts += 1
            print(f"❌ {timestamp} 录音资源冲突: 第{self.recording_conflicts}次")
        
        # 3. 检测状态恢复逻辑
        elif "监听状态恢复成功（音频流保持连续运行）" in line:
            print(f"✅ {timestamp} 修复生效：状态恢复无音频流重启")
        
        # 4. 检测状态防抖动
        elif "设备状态变化被防抖延迟" in line:
            print(f"✅ {timestamp} 防抖动生效：状态变化被延迟")
        
        elif "设备状态变更" in line:
            self.state_change_frequency.append(current_time)
            self.check_state_change_frequency()
        
        # 5. 检测对话轮次
        elif "STT识别结果" in line:
            self.conversation_rounds += 1
            print(f"🎯 {timestamp} 第{self.conversation_rounds}轮对话开始")
            
            # 重点关注第二轮及后续对话
            if self.conversation_rounds >= 2:
                print(f"   🔍 重点验证：第{self.conversation_rounds}轮对话质量")
        
        # 6. 检测音频处理异常
        elif any(keyword in line for keyword in ["音频处理失败", "音频流异常", "Opus编码失败"]):
            print(f"❌ {timestamp} 音频处理异常: {line}")
            self.fix_verification['smooth_second_round'] = False
    
    def check_state_change_frequency(self):
        """检查状态变化频率"""
        current_time = time.time()
        
        # 统计最近10秒内的状态变化次数
        recent_changes = [t for t in self.state_change_frequency if current_time - t <= 10]
        
        if len(recent_changes) > 8:  # 10秒内超过8次状态变化认为异常
            self.fix_verification['stable_state_display'] = False
            self.fix_verification['reduced_state_changes'] = False
            print(f"⚠️ 状态变化过于频繁: 10秒内{len(recent_changes)}次")
    
    def detect_critical_issues(self):
        """检测严重问题"""
        # 音频流重复启动超过3次
        if self.audio_flow_restart_count > 3:
            print(f"🚨 严重问题：音频流重复启动{self.audio_flow_restart_count}次")
            return True
        
        # 录音冲突超过5次
        if self.recording_conflicts > 5:
            print(f"🚨 严重问题：录音资源冲突{self.recording_conflicts}次")
            return True
        
        return False
    
    def print_progress_status(self, elapsed_seconds):
        """输出进度状态"""
        print(f"\n📊 进度状态 ({elapsed_seconds}秒):")
        print(f"   对话轮次: {self.conversation_rounds}")
        print(f"   音频流重启: {self.audio_flow_restart_count}次")
        print(f"   录音冲突: {self.recording_conflicts}次")
        print(f"   状态变化: {len(self.state_change_frequency)}次")
        
        # 修复效果即时评估
        if self.conversation_rounds >= 2:
            if self.audio_flow_restart_count == 0:
                print("   ✅ 第二轮对话：无音频流重启")
            else:
                print("   ❌ 第二轮对话：存在音频流重启")
    
    def analyze_verification_results(self):
        """分析验证结果"""
        print("\n" + "=" * 60)
        print("📋 第二轮语音断续问题修复验证结果")
        print("=" * 60)
        
        # 基础统计
        print(f"🎯 测试统计:")
        print(f"   完成对话轮次: {self.conversation_rounds}")
        print(f"   音频流重启次数: {self.audio_flow_restart_count}")
        print(f"   录音资源冲突: {self.recording_conflicts}")
        print(f"   状态变化总数: {len(self.state_change_frequency)}")
        
        # 修复效果验证
        print(f"\n🔧 修复效果验证:")
        for fix_name, is_success in self.fix_verification.items():
            status = "✅ 通过" if is_success else "❌ 失败"
            fix_desc = {
                'no_audio_flow_restart': '音频流无重复启动',
                'stable_state_display': '状态显示稳定',
                'smooth_second_round': '第二轮对话流畅',
                'reduced_state_changes': '状态变化频率降低'
            }.get(fix_name, fix_name)
            print(f"   {status} {fix_desc}")
        
        # 总体评估
        success_count = sum(self.fix_verification.values())
        total_checks = len(self.fix_verification)
        success_rate = (success_count / total_checks) * 100
        
        print(f"\n🏆 总体修复成功率: {success_rate:.1f}% ({success_count}/{total_checks})")
        
        if success_rate >= 75:
            print("🎉 修复效果良好！第二轮语音断续问题已解决")
        elif success_rate >= 50:
            print("⚠️ 修复部分有效，仍需进一步优化")
        else:
            print("❌ 修复效果不佳，需要重新检查修复方案")
        
        # 具体建议
        print(f"\n💡 具体建议:")
        if not self.fix_verification['no_audio_flow_restart']:
            print("   - 检查restoreListeningStateSafely()是否正确移除了音频流重启")
        
        if not self.fix_verification['stable_state_display']:
            print("   - 检查状态防抖动机制是否正确实现")
        
        if not self.fix_verification['smooth_second_round']:
            print("   - 检查音频处理流程是否存在其他冲突")
        
        if self.conversation_rounds < 2:
            print("   - 延长测试时间，确保覆盖多轮对话")
    
    def extract_timestamp(self, line):
        """提取时间戳"""
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        return match.group(1) if match else "unknown"

def main():
    """主函数"""
    print("🎯 第二轮语音断续问题修复验证")
    print("🔧 验证重点：")
    print("   1. TTS结束后无音频流重复启动")
    print("   2. 状态显示防抖动生效")
    print("   3. 第二轮及后续对话流畅")
    print("   4. 资源使用优化")
    print()
    
    verifier = SecondVoiceStutterFixVerifier()
    
    try:
        success = verifier.run_verification()
        if success:
            print("\n✅ 验证流程完成")
        else:
            print("\n❌ 验证流程失败")
    except KeyboardInterrupt:
        print("\n🛑 用户中断验证")
    except Exception as e:
        print(f"\n❌ 验证过程异常: {e}")

if __name__ == "__main__":
    main() 