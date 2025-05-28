#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连续对话调试脚本
专门诊断第二句语音时应用退出的问题
"""

import subprocess
import time
import threading
import queue

def continuous_dialog_debug():
    """连续对话调试"""
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🔍 连续对话退出问题调试")
    print("=" * 50)
    
    # 安装最新APK
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
    
    # 启动应用
    print("2. 启动应用...")
    try:
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "start", "-n", 
            f"{package_name}/.MainActivity"
        ], timeout=10)
        time.sleep(3)
        print("   ✅ 应用启动成功")
    except Exception as e:
        print(f"   ❌ 应用启动失败: {e}")
        return False
    
    # 清除日志
    print("3. 清除旧日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"])
    print("   ✅ 日志已清除")
    
    # 开始连续对话测试
    print("4. 开始连续对话测试...")
    print("\n" + "🎯 测试步骤：")
    print("   1. 点击 '开始语音对话' 按钮")
    print("   2. 说第一句话：'你好小智'")
    print("   3. 等待小智回复完成")
    print("   4. 说第二句话：'请介绍一下你自己'")
    print("   5. 观察是否会退出\n")
    
    # 创建日志分析器
    log_analyzer = ContinuousDialogLogAnalyzer()
    
    try:
        # 启动logcat监控
        logcat_process = subprocess.Popen([
            "adb", "-s", device_id, "logcat", "-v", "time"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # 启动日志分析线程
        log_thread = threading.Thread(
            target=log_analyzer.analyze_logs, 
            args=(logcat_process,),
            daemon=True
        )
        log_thread.start()
        
        print("🎤 开始监控连续对话...")
        print("   按 Ctrl+C 停止监控\n")
        
        # 主循环
        start_time = time.time()
        while True:
            time.sleep(1)
            
            # 每10秒输出一次状态
            if time.time() - start_time > 10:
                log_analyzer.print_status()
                start_time = time.time()
                
    except KeyboardInterrupt:
        print("\n🛑 监控停止")
        logcat_process.terminate()
        
        # 输出最终分析结果
        log_analyzer.print_final_analysis()

class ContinuousDialogLogAnalyzer:
    def __init__(self):
        self.conversation_count = 0
        self.last_state = "UNKNOWN"
        self.state_transitions = []
        self.error_logs = []
        self.resource_logs = []
        self.audio_flow_logs = []
        
        self.first_dialog_complete = False
        self.second_dialog_started = False
        self.app_crashed = False
        
    def analyze_logs(self, logcat_process):
        """分析日志"""
        while True:
            try:
                line = logcat_process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line or "ChatViewModel" not in line:
                    continue
                
                self.process_log_line(line)
                
            except Exception as e:
                print(f"日志分析异常: {e}")
                break
    
    def process_log_line(self, line):
        """处理单行日志"""
        
        # 设备状态变化
        if "设备状态变更" in line:
            parts = line.split("设备状态变更:")
            if len(parts) > 1:
                transition = parts[1].strip()
                self.state_transitions.append((time.time(), transition))
                print(f"📊 状态变更: {transition}")
                
                # 检测对话阶段
                if "SPEAKING" in transition and not self.first_dialog_complete:
                    print("   🎯 第一轮对话开始 - TTS播放")
                elif "LISTENING" in transition and self.first_dialog_complete and not self.second_dialog_started:
                    self.second_dialog_started = True
                    print("   🎯 第二轮对话开始 - 准备接收语音")
        
        # TTS播放完成
        if "TTS播放完成" in line:
            if not self.first_dialog_complete:
                self.first_dialog_complete = True
                print("   ✅ 第一轮对话完成，准备第二轮")
        
        # 音频流程管理
        if any(keyword in line for keyword in [
            "启动ESP32兼容的持续音频流程", 
            "音频流程已在运行",
            "音频流程已结束",
            "音频流程停止标志检测到"
        ]):
            self.audio_flow_logs.append((time.time(), line))
            print(f"🎵 音频流程: {line.split('ChatViewModel:')[-1].strip()}")
        
        # 资源管理
        if any(keyword in line for keyword in [
            "正在清理资源",
            "资源清理完成", 
            "释放音频组件",
            "取消当前音频任务"
        ]):
            self.resource_logs.append((time.time(), line))
            print(f"🧹 资源管理: {line.split('ChatViewModel:')[-1].strip()}")
        
        # 错误和异常
        if any(keyword in line for keyword in [
            "ERROR", "Exception", "失败", "错误", "异常", "FATAL"
        ]):
            self.error_logs.append((time.time(), line))
            print(f"❌ 错误: {line}")
            
            # 检测应用崩溃
            if "FATAL" in line or "Process:" in line:
                self.app_crashed = True
                print("💥 检测到应用崩溃!")
    
    def print_status(self):
        """输出当前状态"""
        print(f"\n📋 当前状态:")
        print(f"   第一轮对话完成: {'✅' if self.first_dialog_complete else '❌'}")
        print(f"   第二轮对话开始: {'✅' if self.second_dialog_started else '❌'}")
        print(f"   应用崩溃: {'💥 是' if self.app_crashed else '✅ 否'}")
        print(f"   状态变更数: {len(self.state_transitions)}")
        print(f"   音频流程日志: {len(self.audio_flow_logs)}")
        print(f"   错误日志数: {len(self.error_logs)}")
    
    def print_final_analysis(self):
        """输出最终分析结果"""
        print("\n" + "=" * 50)
        print("📊 连续对话调试最终分析")
        print("=" * 50)
        
        # 对话阶段分析
        print("\n🎯 对话阶段分析:")
        print(f"   第一轮对话完成: {'✅ 成功' if self.first_dialog_complete else '❌ 未完成'}")
        print(f"   第二轮对话开始: {'✅ 成功' if self.second_dialog_started else '❌ 未开始'}")
        print(f"   应用状态: {'💥 崩溃' if self.app_crashed else '✅ 正常'}")
        
        # 状态转换分析
        print(f"\n📊 状态转换序列 ({len(self.state_transitions)} 次):")
        for timestamp, transition in self.state_transitions[-10:]:  # 显示最后10次
            print(f"   {transition}")
        
        # 音频流程分析
        print(f"\n🎵 音频流程分析 ({len(self.audio_flow_logs)} 条):")
        if self.audio_flow_logs:
            for timestamp, log in self.audio_flow_logs[-5:]:  # 显示最后5条
                content = log.split('ChatViewModel:')[-1].strip()
                print(f"   {content}")
        
        # 错误分析
        if self.error_logs:
            print(f"\n❌ 错误分析 ({len(self.error_logs)} 条):")
            for timestamp, log in self.error_logs[-3:]:  # 显示最后3条错误
                print(f"   {log}")
        
        # 问题诊断
        print(f"\n🔍 问题诊断:")
        if self.app_crashed:
            print("   💥 应用崩溃 - 需要检查崩溃日志")
        elif not self.first_dialog_complete:
            print("   🎯 第一轮对话未完成 - 检查TTS播放问题")
        elif not self.second_dialog_started:
            print("   🎯 第二轮对话未开始 - 检查监听恢复问题")
        elif len(self.error_logs) > 0:
            print("   ⚠️ 有错误日志 - 检查具体错误信息")
        else:
            print("   ✅ 连续对话流程正常")
        
        # 建议解决方案
        print(f"\n💡 建议解决方案:")
        if self.app_crashed:
            print("   1. 查看完整崩溃堆栈")
            print("   2. 检查资源释放和内存管理")
            print("   3. 检查音频组件状态冲突")
        else:
            print("   1. 继续测试多轮对话")
            print("   2. 监控资源使用情况")
            print("   3. 验证音频流程状态管理")

if __name__ == "__main__":
    continuous_dialog_debug() 