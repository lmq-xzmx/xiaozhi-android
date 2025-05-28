#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时APK闪退诊断工具
通过ADB实时监控应用启动和崩溃，提供详细的错误分析
"""

import subprocess
import time
import threading
import signal
import sys
from datetime import datetime

class RealTimeCrashDiagnosis:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
        self.activity_name = f"{self.package_name}/.MainActivity"
        self.logcat_process = None
        self.is_monitoring = False
        
    def setup_signal_handlers(self):
        """设置信号处理器，确保能够优雅退出"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🛑 收到信号 {signum}，正在停止监控...")
        self.stop_monitoring()
        sys.exit(0)
    
    def clear_app_data(self):
        """清除应用数据"""
        print("🧹 清除应用数据...")
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "pm", "clear", self.package_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  ✅ 应用数据已清除")
                return True
            else:
                print(f"  ❌ 清除失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"  💥 清除数据异常: {e}")
            return False
    
    def force_stop_app(self):
        """强制停止应用"""
        print("🛑 强制停止应用...")
        try:
            subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "force-stop", self.package_name],
                capture_output=True
            )
            print("  ✅ 应用已停止")
        except Exception as e:
            print(f"  💥 停止应用异常: {e}")
    
    def start_logcat_monitoring(self):
        """启动logcat监控"""
        print("📋 启动logcat监控...")
        
        # 清除旧日志
        subprocess.run(["adb", "-s", self.device_id, "logcat", "-c"], capture_output=True)
        
        # 启动logcat进程
        self.logcat_process = subprocess.Popen(
            ["adb", "-s", self.device_id, "logcat", "-v", "time", 
             "AndroidRuntime:E", "System.err:E", "*:F", 
             f"{self.package_name}:*", "VApplication:*", "MainActivity:*",
             "Hilt:*", "DataStore:*", "DeviceIdManager:*"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.is_monitoring = True
        
        # 在单独线程中处理日志
        log_thread = threading.Thread(target=self.process_logs, daemon=True)
        log_thread.start()
        
        print("  ✅ logcat监控已启动")
    
    def process_logs(self):
        """处理logcat日志"""
        crash_keywords = [
            "FATAL EXCEPTION",
            "AndroidRuntime",
            "java.lang.RuntimeException",
            "java.lang.NullPointerException",
            "java.lang.ClassNotFoundException",
            "NoClassDefFoundError",
            "OutOfMemoryError",
            "SecurityException",
            "UnsatisfiedLinkError",
            "ExceptionInInitializerError",
            "IllegalStateException",
            "Process.*crashed"
        ]
        
        hilt_keywords = [
            "Hilt",
            "DaggerGenerated",
            "@Inject",
            "SingletonComponent",
            "HiltAndroidApp"
        ]
        
        datastore_keywords = [
            "DataStore",
            "Preferences",
            "first()",
            "runBlocking"
        ]
        
        important_lines = []
        
        try:
            while self.is_monitoring and self.logcat_process:
                line = self.logcat_process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # 实时显示重要日志
                is_important = False
                
                # 检查崩溃关键词
                for keyword in crash_keywords:
                    if keyword.lower() in line.lower():
                        print(f"💥 CRASH: {line}")
                        important_lines.append(f"CRASH: {line}")
                        is_important = True
                        break
                
                # 检查Hilt相关问题
                if not is_important:
                    for keyword in hilt_keywords:
                        if keyword.lower() in line.lower():
                            print(f"🔧 HILT: {line}")
                            important_lines.append(f"HILT: {line}")
                            is_important = True
                            break
                
                # 检查DataStore相关问题
                if not is_important:
                    for keyword in datastore_keywords:
                        if keyword.lower() in line.lower():
                            print(f"💾 DATASTORE: {line}")
                            important_lines.append(f"DATASTORE: {line}")
                            is_important = True
                            break
                
                # 检查应用相关日志
                if not is_important and self.package_name in line:
                    print(f"📱 APP: {line}")
                    important_lines.append(f"APP: {line}")
                    is_important = True
                
                # 如果是重要日志，保存到列表中
                if is_important:
                    # 保持最近100条重要日志
                    if len(important_lines) > 100:
                        important_lines = important_lines[-100:]
        
        except Exception as e:
            print(f"💥 日志处理异常: {e}")
    
    def launch_app(self):
        """启动应用"""
        print("🚀 启动应用...")
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "am", "start", 
                 "-n", self.activity_name, "-W"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("  ✅ 启动命令执行成功")
                print(f"  📊 启动结果: {result.stdout.strip()}")
                return True
            else:
                print(f"  ❌ 启动命令失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ⏰ 启动超时")
            return False
        except Exception as e:
            print(f"  💥 启动异常: {e}")
            return False
    
    def check_app_running(self):
        """检查应用是否在运行"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "ps", "|", "grep", self.package_name],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if self.package_name in result.stdout:
                print(f"  ✅ 应用正在运行")
                return True
            else:
                print(f"  ❌ 应用未在运行（可能已崩溃）")
                return False
                
        except Exception as e:
            print(f"  💥 检查运行状态异常: {e}")
            return False
    
    def get_device_info(self):
        """获取设备信息"""
        print("📱 获取设备信息...")
        
        try:
            # Android版本
            android_version = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "getprop", "ro.build.version.release"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # API级别
            api_level = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "getprop", "ro.build.version.sdk"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # 设备型号
            device_model = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            print(f"  📱 Android版本: {android_version}")
            print(f"  🔢 API级别: {api_level}")
            print(f"  📱 设备型号: {device_model}")
            
            return {
                "android_version": android_version,
                "api_level": int(api_level) if api_level.isdigit() else 0,
                "device_model": device_model
            }
            
        except Exception as e:
            print(f"  💥 获取设备信息异常: {e}")
            return None
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.logcat_process:
            self.logcat_process.terminate()
            try:
                self.logcat_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logcat_process.kill()
            self.logcat_process = None
        print("📋 logcat监控已停止")
    
    def run_diagnosis(self):
        """运行完整诊断"""
        print("🚨 实时APK闪退诊断工具")
        print("=" * 60)
        print(f"📱 目标设备: {self.device_id}")
        print(f"📦 应用包名: {self.package_name}")
        print(f"🎯 启动Activity: {self.activity_name}")
        print("=" * 60)
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 获取设备信息
        device_info = self.get_device_info()
        if device_info and device_info["api_level"] < 24:
            print(f"⚠️ 警告: API级别 {device_info['api_level']} 可能过低")
        
        # 强制停止应用
        self.force_stop_app()
        
        # 清除应用数据
        self.clear_app_data()
        
        # 启动logcat监控
        self.start_logcat_monitoring()
        
        # 等待一下让监控启动
        time.sleep(2)
        
        print("\n🚀 准备启动应用...")
        print("📋 监控已开始，将显示实时日志...")
        print("按 Ctrl+C 停止监控")
        print("=" * 60)
        
        # 启动应用
        launch_success = self.launch_app()
        
        if launch_success:
            # 等待几秒钟观察应用状态
            print("\n⏱️ 等待5秒观察应用状态...")
            time.sleep(5)
            
            # 检查应用是否还在运行
            is_running = self.check_app_running()
            
            if is_running:
                print("\n🎉 应用启动成功且正在运行！")
                print("继续监控中，按 Ctrl+C 停止...")
            else:
                print("\n💥 应用已崩溃，请查看上方的日志分析")
        else:
            print("\n❌ 应用启动失败")
        
        # 继续监控直到用户停止
        try:
            while self.is_monitoring:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 用户停止监控")
        finally:
            self.stop_monitoring()
        
        print("\n🏁 诊断完成")

def main():
    """主函数"""
    # 检查设备连接
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "SOZ95PIFVS5H6PIZ" not in result.stdout:
            print("❌ 未检测到目标设备 SOZ95PIFVS5H6PIZ")
            print("请确保设备已连接并开启USB调试")
            return
    except Exception as e:
        print(f"❌ ADB检查失败: {e}")
        return
    
    # 运行诊断
    diagnosis = RealTimeCrashDiagnosis()
    diagnosis.run_diagnosis()

if __name__ == "__main__":
    main() 