#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK启动测试脚本
快速测试APK是否能正常启动
"""

import subprocess
import time
import os

def build_apk():
    """构建APK"""
    print("🏗️ 构建APK...")
    try:
        result = subprocess.run(
            ["./gradlew", "assembleDebug"],
            cwd="..",
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("  ✅ APK构建成功")
            return True
        else:
            print("  ❌ APK构建失败")
            print(f"  错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"  💥 构建异常: {e}")
        return False

def install_apk():
    """安装APK到设备"""
    print("📱 安装APK...")
    apk_path = "../app/build/outputs/apk/debug/app-debug.apk"
    
    if not os.path.exists(apk_path):
        print("  ❌ APK文件不存在")
        return False
    
    try:
        # 卸载旧版本
        subprocess.run(
            ["adb", "uninstall", "info.dourok.voicebot"],
            capture_output=True
        )
        
        # 安装新版本
        result = subprocess.run(
            ["adb", "install", apk_path],
            capture_output=True,
            text=True
        )
        
        if "Success" in result.stdout:
            print("  ✅ APK安装成功")
            return True
        else:
            print("  ❌ APK安装失败")
            print(f"  错误: {result.stdout}")
            return False
    except Exception as e:
        print(f"  💥 安装异常: {e}")
        return False

def test_app_startup():
    """测试应用启动"""
    print("🚀 测试应用启动...")
    
    try:
        # 启动应用
        subprocess.run(
            ["adb", "shell", "am", "start", "-n", "info.dourok.voicebot/.MainActivity"],
            capture_output=True
        )
        
        print("  📱 应用已启动，等待3秒...")
        time.sleep(3)
        
        # 检查应用是否在运行
        result = subprocess.run(
            ["adb", "shell", "ps", "|", "grep", "voicebot"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if "voicebot" in result.stdout:
            print("  ✅ 应用正在运行")
            return True
        else:
            print("  ❌ 应用未在运行（可能已崩溃）")
            return False
            
    except Exception as e:
        print(f"  💥 启动测试异常: {e}")
        return False

def get_crash_logs():
    """获取崩溃日志"""
    print("📋 获取崩溃日志...")
    
    try:
        # 清除旧日志
        subprocess.run(["adb", "logcat", "-c"], capture_output=True)
        
        # 启动应用
        subprocess.run(
            ["adb", "shell", "am", "start", "-n", "info.dourok.voicebot/.MainActivity"],
            capture_output=True
        )
        
        print("  等待5秒收集日志...")
        time.sleep(5)
        
        # 获取日志
        result = subprocess.run(
            ["adb", "logcat", "-d", "-s", "AndroidRuntime:E", "VApplication:*", "MainActivity:*"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("  📋 发现日志:")
            print(result.stdout)
        else:
            print("  ✅ 未发现错误日志")
            
    except Exception as e:
        print(f"  💥 日志获取异常: {e}")

def main():
    """主函数"""
    print("🧪 APK启动测试工具")
    print("=" * 40)
    
    # 检查ADB连接
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in result.stdout:
            print("❌ 未检测到Android设备，请确保:")
            print("   1. 设备已连接")
            print("   2. 已开启USB调试")
            print("   3. ADB已安装")
            return
        else:
            print("✅ 检测到Android设备")
    except:
        print("❌ ADB未安装或不在PATH中")
        return
    
    # 执行测试步骤
    if not build_apk():
        return
    
    if not install_apk():
        return
    
    if not test_app_startup():
        print("\n💥 应用启动失败，获取详细日志...")
        get_crash_logs()
    else:
        print("\n🎉 应用启动成功！")

if __name__ == "__main__":
    main() 