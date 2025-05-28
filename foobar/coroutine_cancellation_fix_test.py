#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协程取消修复测试脚本
专门测试"standalonecoroutine was cancelled"错误的修复
"""

import subprocess
import time
import threading
import queue
import re

def test_coroutine_cancellation_fix():
    """测试协程取消修复"""
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🔧 协程取消修复测试")
    print("=" * 60)
    
    # 安装修复后的APK
    print("1. 安装协程取消修复的APK...")
    try:
        result = subprocess.run([
            "adb", "-s", device_id, "install", "-r", 
            "app/build/outputs/apk/debug/app-debug.apk"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ 修复版APK安装成功")
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
    
    # 开始协程取消测试
    print("4. 开始协程取消修复测试...")
    print("\n" + "🎯 测试重点：")
    print("   1. 启动语音对话")
    print("   2. 在说话过程中多次快速切换状态")
    print("   3. 观察是否出现'standalonecoroutine was cancelled'错误")
    print("   4. 检查协程异常处理是否正常工作")
    print("   💡 关键：协程安全取消、异常处理、资源清理\n")
    
    # 创建协程分析器
    analyzer = CoroutineCancellationAnalyzer()
    
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
        
        print("🔍 开始监控协程取消和异常处理...")
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

class CoroutineCancellationAnalyzer:
    def __init__(self):
        # 协程取消相关
        self.cancellation_events = []
        self.exception_events = []
        self.audio_flow_events = []
        
        # 错误统计
        self.coroutine_cancelled_errors = 0
        self.handled_cancellations = 0
        self.unhandled_exceptions = 0
        self.audio_flow_failures = 0
        
        # 修复效果检测
        self.fix_indicators = {
            'supervisor_job_usage': False,
            'cancellation_exception_handling': False,
            'non_cancellable_cleanup': False,
            'ensure_active_checks': False,
            'safe_resource_cleanup': False
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
        
        # 协程取消事件
        if "standalonecoroutine was cancelled" in line.lower():
            self.coroutine_cancelled_errors += 1
            self.cancellation_events.append({
                'timestamp': timestamp,
                'message': line,
                'type': 'ERROR'
            })
            print(f"❌ {timestamp} 检测到协程取消错误: {line}")
        
        # 正常的协程取消处理
        elif any(keyword in line for keyword in [
            "被正常取消", "被取消", "音频流程被取消", "实时播放被取消"
        ]):
            self.handled_cancellations += 1
            self.cancellation_events.append({
                'timestamp': timestamp,
                'message': line,
                'type': 'HANDLED'
            })
            print(f"✅ {timestamp} 正常处理协程取消: {line}")
            self.fix_indicators['cancellation_exception_handling'] = True
        
        # SupervisorJob使用检测
        elif "SupervisorJob" in line or "使用SupervisorJob" in line:
            self.fix_indicators['supervisor_job_usage'] = True
            print(f"🔧 {timestamp} 检测到SupervisorJob使用")
        
        # NonCancellable清理检测
        elif "NonCancellable" in line or "安全清理资源" in line:
            self.fix_indicators['non_cancellable_cleanup'] = True
            print(f"🛡️ {timestamp} 检测到安全资源清理")
        
        # ensureActive检查检测
        elif "ensureActive" in line or "检查协程是否被取消" in line:
            self.fix_indicators['ensure_active_checks'] = True
            print(f"🔍 {timestamp} 检测到协程活跃性检查")
        
        # 音频流程事件
        elif any(keyword in line for keyword in [
            "启动ESP32兼容的持续音频流程", "音频流程已结束", "音频流程失败"
        ]):
            event_type = 'SUCCESS' if '已结束' in line else ('FAILURE' if '失败' in line else 'START')
            self.audio_flow_events.append({
                'timestamp': timestamp,
                'message': line,
                'type': event_type
            })
            
            if event_type == 'FAILURE':
                self.audio_flow_failures += 1
                print(f"⚠️ {timestamp} 音频流程失败: {line}")
            elif event_type == 'START':
                print(f"🎵 {timestamp} 音频流程启动")
        
        # 异常事件
        elif any(keyword in line for keyword in [
            "Exception", "异常", "失败", "错误"
        ]) and "ChatViewModel" in line or "OpusStreamPlayer" in line:
            # 过滤掉正常的取消信息
            if not any(normal_keyword in line for normal_keyword in [
                "被取消", "被正常取消", "取消恢复"
            ]):
                self.unhandled_exceptions += 1
                self.exception_events.append({
                    'timestamp': timestamp,
                    'message': line,
                    'component': 'ChatViewModel' if 'ChatViewModel' in line else 'OpusStreamPlayer'
                })
                print(f"❌ {timestamp} 未处理异常: {line}")
        
        # 资源清理检测
        elif any(keyword in line for keyword in [
            "资源清理完成", "清理录音资源", "播放器资源已释放"
        ]):
            self.fix_indicators['safe_resource_cleanup'] = True
            print(f"🧹 {timestamp} 安全资源清理")
    
    def extract_timestamp(self, line):
        """提取时间戳"""
        match = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        return match.group(1) if match else "unknown"
    
    def print_status(self):
        """输出当前状态"""
        print(f"\n📋 协程取消修复状态:")
        print(f"   协程取消错误: {self.coroutine_cancelled_errors}")
        print(f"   已处理取消: {self.handled_cancellations}")
        print(f"   未处理异常: {self.unhandled_exceptions}")
        print(f"   音频流程失败: {self.audio_flow_failures}")
        
        # 修复指标检测
        print(f"\n🔧 修复指标检测:")
        for indicator, detected in self.fix_indicators.items():
            status = "✅" if detected else "❌"
            indicator_name = {
                'supervisor_job_usage': 'SupervisorJob使用',
                'cancellation_exception_handling': '协程取消异常处理',
                'non_cancellable_cleanup': '不可取消清理',
                'ensure_active_checks': '协程活跃性检查',
                'safe_resource_cleanup': '安全资源清理'
            }.get(indicator, indicator)
            print(f"   {status} {indicator_name}")
    
    def print_final_analysis(self):
        """输出最终分析结果"""
        print("\n" + "=" * 60)
        print("📊 协程取消修复最终分析")
        print("=" * 60)
        
        # 错误统计
        print(f"\n❌ 错误统计:")
        print(f"   'standalonecoroutine was cancelled'错误: {self.coroutine_cancelled_errors}")
        print(f"   未处理异常: {self.unhandled_exceptions}")
        print(f"   音频流程失败: {self.audio_flow_failures}")
        
        # 修复效果统计
        print(f"\n✅ 修复效果:")
        print(f"   已处理的协程取消: {self.handled_cancellations}")
        print(f"   安全资源清理事件: {sum(1 for e in self.audio_flow_events if 'END' in e.get('type', ''))}")
        
        # 修复指标完成度
        implemented_fixes = sum(1 for detected in self.fix_indicators.values() if detected)
        total_fixes = len(self.fix_indicators)
        completion_rate = (implemented_fixes / total_fixes) * 100
        
        print(f"\n🔧 修复实施情况:")
        for indicator, detected in self.fix_indicators.items():
            status = "✅ 已实施" if detected else "❌ 未检测到"
            indicator_name = {
                'supervisor_job_usage': 'SupervisorJob使用',
                'cancellation_exception_handling': '协程取消异常处理',
                'non_cancellable_cleanup': '不可取消的安全清理',
                'ensure_active_checks': '协程活跃性检查',
                'safe_resource_cleanup': '安全资源清理'
            }.get(indicator, indicator)
            print(f"   {status} {indicator_name}")
        
        print(f"\n   修复完成度: {completion_rate:.1f}% ({implemented_fixes}/{total_fixes})")
        
        # 修复效果评估
        print(f"\n🎯 修复效果评估:")
        if self.coroutine_cancelled_errors == 0:
            print("   ✅ 出色！未检测到'standalonecoroutine was cancelled'错误")
            print("   ✅ 协程取消问题已完全解决")
        elif self.coroutine_cancelled_errors < 3:
            print("   ⚠️ 良好！协程取消错误显著减少")
            print("   💡 仍有少量错误，需要进一步优化")
        else:
            print("   ❌ 协程取消问题仍然存在")
            print("   💡 需要检查修复实施情况")
        
        # 异常处理改善
        if self.handled_cancellations > 0:
            print(f"   ✅ 检测到 {self.handled_cancellations} 次正常的协程取消处理")
        
        if completion_rate >= 80:
            print("   ✅ 修复措施实施充分")
        else:
            print("   ⚠️ 修复措施需要进一步完善")
        
        # 最近事件
        print(f"\n📈 最近协程事件:")
        recent_events = self.cancellation_events[-5:]
        for event in recent_events:
            event_type = event['type']
            icon = "✅" if event_type == 'HANDLED' else "❌"
            print(f"   {icon} {event['timestamp']}: {event_type}")
        
        if len(self.cancellation_events) == 0:
            print("   ✅ 未检测到协程取消相关事件")
        
        print(f"\n💡 总结:")
        if self.coroutine_cancelled_errors == 0 and completion_rate >= 80:
            print("   🎉 协程取消修复成功！")
            print("   ✅ 'standalonecoroutine was cancelled'错误已解决")
            print("   ✅ 音频流程异常处理已增强")
        else:
            print("   ⚠️ 协程取消修复需要进一步调整")
            print("   💡 建议检查修复实施的完整性")
        
        print(f"\n🎯 测试完成！协程取消修复分析结果已生成。")

if __name__ == "__main__":
    test_coroutine_cancellation_fix() 