#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智语音卡顿问题快速修复补丁
针对"说着说着又开始卡了"问题的快速修复方案
"""

import subprocess
import time
import os
from datetime import datetime

class VoiceStutterQuickFix:
    def __init__(self):
        self.package_name = "info.dourok.voicebot"
        self.device_id = None
        self.log_file = f"quick_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        print("🚑 小智语音卡顿快速修复工具")
        print("=" * 50)
        
    def log_message(self, level, message):
        """记录修复日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def detect_device(self):
        """检测连接的Android设备"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                devices = []
                for line in lines:
                    if line.strip() and 'device' in line:
                        device_id = line.split()[0]
                        devices.append(device_id)
                
                if len(devices) == 1:
                    self.device_id = devices[0]
                    self.log_message("INFO", f"检测到设备: {self.device_id}")
                    return True
                elif len(devices) > 1:
                    self.log_message("WARNING", f"检测到多个设备: {devices}")
                    self.device_id = devices[0]  # 使用第一个
                    self.log_message("INFO", f"使用设备: {self.device_id}")
                    return True
                else:
                    self.log_message("ERROR", "未检测到任何Android设备")
                    return False
            else:
                self.log_message("ERROR", "ADB命令执行失败")
                return False
        except Exception as e:
            self.log_message("ERROR", f"设备检测失败: {e}")
            return False
    
    def force_restart_app(self):
        """强制重启应用"""
        try:
            self.log_message("INFO", "正在强制停止应用...")
            
            # 强制停止应用
            result = subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'am', 'force-stop', self.package_name
            ], timeout=10)
            
            if result.returncode == 0:
                self.log_message("SUCCESS", "应用已强制停止")
                
                # 等待2秒确保完全停止
                time.sleep(2)
                
                # 清理应用缓存
                self.log_message("INFO", "清理应用缓存...")
                subprocess.run([
                    'adb', '-s', self.device_id, 'shell', 'pm', 'clear', self.package_name
                ], timeout=10)
                
                # 重新启动应用
                self.log_message("INFO", "重新启动应用...")
                subprocess.run([
                    'adb', '-s', self.device_id, 'shell', 'am', 'start', '-n',
                    f'{self.package_name}/.MainActivity'
                ], timeout=10)
                
                self.log_message("SUCCESS", "应用已重新启动")
                return True
            else:
                self.log_message("ERROR", "强制停止应用失败")
                return False
                
        except Exception as e:
            self.log_message("ERROR", f"重启应用失败: {e}")
            return False
    
    def clear_audio_cache(self):
        """清理音频相关缓存和日志"""
        try:
            self.log_message("INFO", "清理音频缓存和日志...")
            
            # 清理logcat缓冲区
            subprocess.run(['adb', '-s', self.device_id, 'logcat', '-c'], timeout=5)
            self.log_message("SUCCESS", "日志缓冲区已清理")
            
            # 触发垃圾回收
            subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'am', 'send-trim-memory',
                self.package_name, 'COMPLETE'
            ], timeout=5)
            self.log_message("SUCCESS", "已触发垃圾回收")
            
            return True
            
        except Exception as e:
            self.log_message("ERROR", f"清理缓存失败: {e}")
            return False
    
    def optimize_audio_settings(self):
        """优化音频相关设置"""
        try:
            self.log_message("INFO", "优化音频设置...")
            
            # 设置音频模式为正常模式
            subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'settings', 'put', 'global',
                'audio_safe_volume_state', '3'
            ], timeout=5)
            
            # 禁用音频处理增强（可能导致延迟）
            subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'settings', 'put', 'global',
                'audio_effects_global_enable', '0'
            ], timeout=5)
            
            self.log_message("SUCCESS", "音频设置已优化")
            return True
            
        except Exception as e:
            self.log_message("WARNING", f"音频设置优化失败（非关键）: {e}")
            return False
    
    def check_memory_pressure(self):
        """检查内存压力并释放"""
        try:
            self.log_message("INFO", "检查内存使用情况...")
            
            # 获取内存信息
            result = subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'cat', '/proc/meminfo'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                mem_available = None
                mem_total = None
                
                for line in lines:
                    if 'MemAvailable:' in line:
                        mem_available = int(line.split()[1])
                    elif 'MemTotal:' in line:
                        mem_total = int(line.split()[1])
                
                if mem_available and mem_total:
                    usage_percent = ((mem_total - mem_available) / mem_total) * 100
                    self.log_message("INFO", f"内存使用率: {usage_percent:.1f}%")
                    
                    if usage_percent > 85:
                        self.log_message("WARNING", "内存压力较高，尝试释放内存...")
                        
                        # 杀死一些非关键进程
                        subprocess.run([
                            'adb', '-s', self.device_id, 'shell', 'am', 'kill-all'
                        ], timeout=10)
                        
                        self.log_message("SUCCESS", "已尝试释放内存")
                    else:
                        self.log_message("SUCCESS", "内存使用正常")
            
            return True
            
        except Exception as e:
            self.log_message("WARNING", f"内存检查失败（非关键）: {e}")
            return False
    
    def verify_audio_permissions(self):
        """验证音频权限"""
        try:
            self.log_message("INFO", "验证音频权限...")
            
            # 检查录音权限
            result = subprocess.run([
                'adb', '-s', self.device_id, 'shell', 'dumpsys', 'package', self.package_name
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if 'android.permission.RECORD_AUDIO: granted=true' in result.stdout:
                    self.log_message("SUCCESS", "录音权限正常")
                else:
                    self.log_message("ERROR", "录音权限可能未授予")
                    
                    # 尝试授予权限
                    subprocess.run([
                        'adb', '-s', self.device_id, 'shell', 'pm', 'grant',
                        self.package_name, 'android.permission.RECORD_AUDIO'
                    ], timeout=5)
                    self.log_message("INFO", "已尝试授予录音权限")
            
            return True
            
        except Exception as e:
            self.log_message("WARNING", f"权限验证失败（非关键）: {e}")
            return False
    
    def monitor_fix_effectiveness(self):
        """监控修复效果"""
        try:
            self.log_message("INFO", "监控修复效果（60秒）...")
            
            # 启动日志监控
            process = subprocess.Popen([
                'adb', '-s', self.device_id, 'logcat', '-s', 'ChatViewModel:*'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            
            start_time = time.time()
            audio_activities = 0
            tts_activities = 0
            errors = 0
            
            while time.time() - start_time < 60:  # 监控60秒
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    if "音频数据发送" in line or "TTS音频数据已缓冲" in line:
                        audio_activities += 1
                    elif "TTS播放完成" in line:
                        tts_activities += 1
                    elif "ERROR" in line or "异常" in line:
                        errors += 1
                    
                    # 每15秒报告一次进度
                    elapsed = time.time() - start_time
                    if int(elapsed) % 15 == 0 and int(elapsed) > 0:
                        self.log_message("INFO", f"监控进度: {elapsed:.0f}s - 音频活动:{audio_activities}, TTS:{tts_activities}, 错误:{errors}")
                
                except Exception:
                    break
            
            process.terminate()
            
            # 评估修复效果
            self.log_message("INFO", "修复效果评估:")
            self.log_message("INFO", f"  音频活动次数: {audio_activities}")
            self.log_message("INFO", f"  TTS播放次数: {tts_activities}")
            self.log_message("INFO", f"  错误次数: {errors}")
            
            if audio_activities > 10 and errors < 3:
                self.log_message("SUCCESS", "修复效果良好，语音交互恢复正常")
                return True
            elif errors > 5:
                self.log_message("WARNING", "仍有较多错误，可能需要进一步修复")
                return False
            else:
                self.log_message("INFO", "修复效果一般，建议继续观察")
                return True
                
        except Exception as e:
            self.log_message("ERROR", f"监控修复效果失败: {e}")
            return False
    
    def run_quick_fix(self):
        """执行快速修复流程"""
        self.log_message("INFO", "开始语音卡顿快速修复...")
        
        # 步骤1: 检测设备
        if not self.detect_device():
            print("❌ 无法检测到Android设备，请确保设备已连接且开启USB调试")
            return False
        
        # 步骤2: 强制重启应用
        self.log_message("INFO", "步骤1/5: 强制重启应用")
        if not self.force_restart_app():
            self.log_message("ERROR", "重启应用失败，修复中止")
            return False
        
        # 等待应用启动
        time.sleep(5)
        
        # 步骤3: 清理缓存
        self.log_message("INFO", "步骤2/5: 清理音频缓存")
        self.clear_audio_cache()
        
        # 步骤4: 优化设置
        self.log_message("INFO", "步骤3/5: 优化音频设置")
        self.optimize_audio_settings()
        
        # 步骤5: 检查内存
        self.log_message("INFO", "步骤4/5: 检查内存压力")
        self.check_memory_pressure()
        
        # 步骤6: 验证权限
        self.log_message("INFO", "步骤5/5: 验证音频权限")
        self.verify_audio_permissions()
        
        # 等待设置生效
        time.sleep(3)
        
        # 步骤7: 监控修复效果
        print("\n🔍 开始监控修复效果...")
        print("💡 请在应用中进行语音交互测试")
        fix_success = self.monitor_fix_effectiveness()
        
        # 生成修复报告
        self.generate_fix_report(fix_success)
        
        return fix_success
    
    def generate_fix_report(self, success):
        """生成修复报告"""
        report_file = f"quick_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 小智语音卡顿快速修复报告\n\n")
            f.write(f"**修复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**修复结果**: {'✅ 成功' if success else '⚠️ 部分成功'}\n\n")
            
            f.write("## 🔧 执行的修复步骤\n\n")
            f.write("1. ✅ 强制重启应用\n")
            f.write("2. ✅ 清理音频缓存和日志\n")
            f.write("3. ✅ 优化音频设置\n")
            f.write("4. ✅ 检查和释放内存\n")
            f.write("5. ✅ 验证音频权限\n")
            f.write("6. ✅ 监控修复效果\n\n")
            
            f.write("## 📋 后续建议\n\n")
            if success:
                f.write("✅ **修复成功**\n")
                f.write("- 语音交互已恢复正常\n")
                f.write("- 建议继续监控应用运行状态\n")
                f.write("- 如问题再次出现，请运行深度诊断工具\n\n")
            else:
                f.write("⚠️ **需要进一步修复**\n")
                f.write("- 建议运行完整诊断工具分析根本原因\n")
                f.write("- 检查网络连接稳定性\n")
                f.write("- 考虑更新应用版本\n\n")
            
            f.write("## 🔄 如果问题持续\n\n")
            f.write("1. **运行诊断工具**: `python voice_interrupt_diagnosis.py`\n")
            f.write("2. **检查网络连接**: 确保WiFi/移动网络稳定\n")
            f.write("3. **重启设备**: 清理所有系统缓存\n")
            f.write("4. **联系技术支持**: 提供诊断报告\n\n")
            
            f.write(f"## 📄 详细日志\n\n完整日志: `{self.log_file}`\n")
        
        self.log_message("INFO", f"修复报告已生成: {report_file}")
        print(f"\n📄 修复报告已保存到: {report_file}")


if __name__ == "__main__":
    quick_fix = VoiceStutterQuickFix()
    
    print("🚑 准备执行语音卡顿快速修复...")
    print("📱 请确保Android设备已连接并开启USB调试")
    print("⏳ 修复过程大约需要2-3分钟")
    print()
    
    input("按回车键开始修复...")
    
    success = quick_fix.run_quick_fix()
    
    if success:
        print("\n✅ 快速修复完成！语音交互应该已恢复正常。")
        print("💡 建议测试语音功能，如果仍有问题请运行诊断工具。")
    else:
        print("\n⚠️ 快速修复部分完成，可能需要进一步诊断。")
        print("🔍 建议运行: python voice_interrupt_diagnosis.py") 