#!/usr/bin/env python3
"""
小智Android应用闪退诊断脚本
用于分析和定位闪退问题的根本原因
"""

import subprocess
import time
import json
import re
from datetime import datetime

class CrashDiagnosisHelper:
    def __init__(self):
        self.package_name = "info.dourok.voicebot"
        self.main_activity = "info.dourok.voicebot.MainActivity"
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def run_adb_command(self, command):
        """执行ADB命令并返回结果"""
        try:
            result = subprocess.run(
                f"adb {command}".split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "命令超时", 1
        except Exception as e:
            return "", str(e), 1
    
    def check_device_connection(self):
        """检查设备连接状态"""
        self.print_header("检查设备连接")
        
        stdout, stderr, code = self.run_adb_command("devices")
        if code != 0:
            print("❌ ADB未安装或无法运行")
            return False
            
        devices = [line for line in stdout.split('\n') if '\tdevice' in line]
        if not devices:
            print("❌ 没有连接的Android设备")
            print("请确保：")
            print("1. 设备已连接并开启USB调试")
            print("2. 已授权此计算机进行调试")
            return False
            
        print(f"✅ 发现 {len(devices)} 个设备:")
        for device in devices:
            device_id = device.split('\t')[0]
            print(f"   📱 {device_id}")
        return True
    
    def check_app_installation(self):
        """检查应用安装状态"""
        self.print_header("检查应用安装状态")
        
        stdout, stderr, code = self.run_adb_command(f"shell pm list packages {self.package_name}")
        if self.package_name in stdout:
            print(f"✅ 应用已安装: {self.package_name}")
            
            # 获取应用版本信息
            stdout, stderr, code = self.run_adb_command(f"shell dumpsys package {self.package_name}")
            version_match = re.search(r'versionName=([^\s]+)', stdout)
            if version_match:
                print(f"📦 版本: {version_match.group(1)}")
            return True
        else:
            print(f"❌ 应用未安装: {self.package_name}")
            return False
    
    def install_apk(self, apk_path):
        """安装APK"""
        self.print_header("安装APK")
        
        print(f"📦 正在安装: {apk_path}")
        stdout, stderr, code = self.run_adb_command(f"install -r {apk_path}")
        
        if code == 0 and "Success" in stdout:
            print("✅ APK安装成功")
            return True
        else:
            print(f"❌ APK安装失败:")
            print(f"   错误: {stderr}")
            print(f"   输出: {stdout}")
            return False
    
    def clear_app_data(self):
        """清除应用数据"""
        self.print_header("清除应用数据")
        
        stdout, stderr, code = self.run_adb_command(f"shell pm clear {self.package_name}")
        if code == 0:
            print("✅ 应用数据已清除")
            return True
        else:
            print(f"❌ 清除数据失败: {stderr}")
            return False
    
    def start_logcat_monitoring(self):
        """启动logcat监控"""
        print("🔍 启动logcat监控...")
        
        # 清除旧日志
        self.run_adb_command("logcat -c")
        
        # 启动logcat进程
        try:
            process = subprocess.Popen(
                ["adb", "logcat", "-v", "time", "*:V"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            return process
        except Exception as e:
            print(f"❌ 启动logcat失败: {e}")
            return None
    
    def launch_app(self):
        """启动应用"""
        self.print_header("启动应用")
        
        print(f"🚀 启动应用: {self.main_activity}")
        stdout, stderr, code = self.run_adb_command(
            f"shell am start -n {self.package_name}/{self.main_activity}"
        )
        
        if code == 0:
            print("✅ 应用启动命令发送成功")
            return True
        else:
            print(f"❌ 应用启动失败:")
            print(f"   错误: {stderr}")
            return False
    
    def analyze_crash_logs(self, logcat_process, duration=30):
        """分析崩溃日志"""
        self.print_header(f"分析崩溃日志 (监控{duration}秒)")
        
        crash_indicators = [
            "FATAL EXCEPTION",
            "AndroidRuntime",
            "Process: " + self.package_name,
            "java.lang.RuntimeException",
            "java.lang.NullPointerException",
            "java.lang.IllegalStateException",
            "ChatViewModel",
            "DeviceConfigManager",
            "WebsocketProtocol"
        ]
        
        crash_logs = []
        app_logs = []
        start_time = time.time()
        
        print(f"⏱️ 监控开始，等待{duration}秒...")
        
        try:
            while time.time() - start_time < duration:
                line = logcat_process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否是我们的应用日志
                if self.package_name in line or "ChatViewModel" in line or "DeviceConfigManager" in line:
                    app_logs.append(line)
                    print(f"📱 {line}")
                
                # 检查崩溃指标
                for indicator in crash_indicators:
                    if indicator in line:
                        crash_logs.append(line)
                        print(f"💥 {line}")
                        
        except KeyboardInterrupt:
            print("\n⏹️ 监控被用户中断")
        
        # 分析结果
        print(f"\n📊 分析结果:")
        print(f"   应用日志条数: {len(app_logs)}")
        print(f"   崩溃相关日志: {len(crash_logs)}")
        
        if crash_logs:
            print("\n💥 发现崩溃日志:")
            for log in crash_logs[-10:]:  # 显示最后10条
                print(f"   {log}")
        
        if app_logs:
            print("\n📱 应用日志摘要:")
            for log in app_logs[-5:]:  # 显示最后5条
                print(f"   {log}")
        
        return crash_logs, app_logs
    
    def check_permissions(self):
        """检查应用权限"""
        self.print_header("检查应用权限")
        
        stdout, stderr, code = self.run_adb_command(f"shell dumpsys package {self.package_name}")
        
        required_permissions = [
            "android.permission.RECORD_AUDIO",
            "android.permission.INTERNET",
            "android.permission.ACCESS_NETWORK_STATE"
        ]
        
        granted_permissions = []
        for permission in required_permissions:
            if f"{permission}: granted=true" in stdout:
                granted_permissions.append(permission)
                print(f"✅ {permission}")
            else:
                print(f"❌ {permission}")
        
        return len(granted_permissions) == len(required_permissions)
    
    def run_full_diagnosis(self, apk_path=None):
        """运行完整诊断"""
        print("🔍 小智Android应用闪退诊断")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 检查设备连接
        if not self.check_device_connection():
            return False
        
        # 2. 安装APK（如果提供）
        if apk_path:
            if not self.install_apk(apk_path):
                return False
        
        # 3. 检查应用安装
        if not self.check_app_installation():
            print("请先安装APK文件")
            return False
        
        # 4. 清除应用数据
        self.clear_app_data()
        
        # 5. 检查权限
        self.check_permissions()
        
        # 6. 启动logcat监控
        logcat_process = self.start_logcat_monitoring()
        if not logcat_process:
            return False
        
        # 7. 启动应用
        if not self.launch_app():
            logcat_process.terminate()
            return False
        
        # 8. 分析崩溃日志
        crash_logs, app_logs = self.analyze_crash_logs(logcat_process, duration=30)
        
        # 9. 清理
        logcat_process.terminate()
        
        # 10. 生成报告
        self.generate_report(crash_logs, app_logs)
        
        return True
    
    def generate_report(self, crash_logs, app_logs):
        """生成诊断报告"""
        self.print_header("诊断报告")
        
        if crash_logs:
            print("🚨 发现应用崩溃!")
            print("\n可能的原因:")
            
            # 分析常见崩溃原因
            crash_text = '\n'.join(crash_logs)
            
            if "NullPointerException" in crash_text:
                print("   • 空指针异常 - 可能是依赖注入或初始化问题")
            
            if "IllegalStateException" in crash_text:
                print("   • 非法状态异常 - 可能是生命周期或状态管理问题")
            
            if "ChatViewModel" in crash_text:
                print("   • ChatViewModel相关问题 - 可能是协议初始化失败")
            
            if "DeviceConfigManager" in crash_text:
                print("   • 设备配置管理器问题 - 可能是DataStore或设备ID问题")
            
            if "WebsocketProtocol" in crash_text:
                print("   • WebSocket协议问题 - 可能是网络连接或协议初始化问题")
            
            print("\n建议解决方案:")
            print("   1. 检查网络连接")
            print("   2. 确保服务器地址正确")
            print("   3. 检查设备绑定状态")
            print("   4. 重新安装应用")
            
        elif app_logs:
            print("✅ 应用启动正常，未发现崩溃")
            print("如果仍有问题，可能是:")
            print("   • 延迟崩溃（需要更长监控时间）")
            print("   • 特定操作触发的崩溃")
            print("   • 网络相关问题")
        else:
            print("⚠️ 未收集到足够的日志信息")
            print("可能原因:")
            print("   • 应用启动过快")
            print("   • 日志级别过低")
            print("   • 设备连接问题")

def main():
    """主函数"""
    import sys
    
    diagnosis = CrashDiagnosisHelper()
    
    # 检查是否提供了APK路径
    apk_path = None
    if len(sys.argv) > 1:
        apk_path = sys.argv[1]
        print(f"将安装APK: {apk_path}")
    
    # 运行诊断
    success = diagnosis.run_full_diagnosis(apk_path)
    
    if success:
        print("\n🎉 诊断完成!")
    else:
        print("\n❌ 诊断失败，请检查设备连接和ADB配置")

if __name__ == "__main__":
    main() 