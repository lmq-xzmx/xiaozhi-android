#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK立即闪退诊断工具
专门用于诊断应用启动时立即闪退的问题
"""

import subprocess
import time
import os
import re

def check_adb_connection():
    """检查ADB连接"""
    print("📱 检查ADB连接...")
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" in result.stdout and "List of devices attached" in result.stdout:
            devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
            if devices:
                print(f"  ✅ 检测到 {len(devices)} 个设备")
                return True
            else:
                print("  ❌ 未检测到设备")
                return False
        else:
            print("  ❌ ADB连接失败")
            return False
    except FileNotFoundError:
        print("  ❌ ADB未安装")
        return False
    except Exception as e:
        print(f"  💥 ADB检查异常: {e}")
        return False

def get_app_info():
    """获取应用信息"""
    print("📋 获取应用信息...")
    try:
        # 检查应用是否已安装
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "info.dourok.voicebot"],
            capture_output=True,
            text=True
        )
        
        if "info.dourok.voicebot" in result.stdout:
            print("  ✅ 应用已安装")
            
            # 获取应用版本信息
            version_result = subprocess.run(
                ["adb", "shell", "dumpsys", "package", "info.dourok.voicebot", "|", "grep", "versionName"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if version_result.stdout.strip():
                print(f"  📦 版本信息: {version_result.stdout.strip()}")
            
            return True
        else:
            print("  ❌ 应用未安装")
            return False
            
    except Exception as e:
        print(f"  💥 获取应用信息异常: {e}")
        return False

def clear_app_data():
    """清除应用数据"""
    print("🧹 清除应用数据...")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "clear", "info.dourok.voicebot"],
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

def start_app_with_logging():
    """启动应用并收集日志"""
    print("🚀 启动应用并收集日志...")
    
    try:
        # 清除旧日志
        subprocess.run(["adb", "logcat", "-c"], capture_output=True)
        print("  📋 已清除旧日志")
        
        # 启动logcat收集
        logcat_process = subprocess.Popen(
            ["adb", "logcat", "-v", "time", "*:E", "AndroidRuntime:*", "VApplication:*", "MainActivity:*", "System.err:*"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("  📱 启动应用...")
        # 启动应用
        start_result = subprocess.run(
            ["adb", "shell", "am", "start", "-n", "info.dourok.voicebot/.MainActivity"],
            capture_output=True,
            text=True
        )
        
        if start_result.returncode != 0:
            print(f"  ❌ 启动命令失败: {start_result.stderr}")
            logcat_process.terminate()
            return False
        
        print("  ⏱️ 等待5秒收集日志...")
        time.sleep(5)
        
        # 停止logcat
        logcat_process.terminate()
        stdout, stderr = logcat_process.communicate(timeout=2)
        
        return stdout
        
    except Exception as e:
        print(f"  💥 启动测试异常: {e}")
        return None

def analyze_crash_logs(logs):
    """分析崩溃日志"""
    print("🔍 分析崩溃日志...")
    
    if not logs or not logs.strip():
        print("  ❌ 未收集到日志")
        return
    
    print("  📋 原始日志:")
    print("=" * 60)
    print(logs)
    print("=" * 60)
    
    # 分析常见的崩溃模式
    crash_patterns = {
        "空指针异常": r"NullPointerException",
        "类找不到": r"ClassNotFoundException|NoClassDefFoundError",
        "方法找不到": r"NoSuchMethodError|MethodNotFoundException",
        "内存不足": r"OutOfMemoryError",
        "权限被拒绝": r"SecurityException|Permission denied",
        "Hilt异常": r"Hilt|DaggerGenerated|@Inject",
        "DataStore异常": r"DataStore|Preferences",
        "Compose异常": r"Compose|@Composable",
        "ViewModel异常": r"ViewModel|HiltViewModel",
        "应用启动异常": r"Application|onCreate",
        "Activity异常": r"MainActivity|Activity",
        "JNI异常": r"JNI|native",
        "资源异常": r"Resources\$NotFoundException|ResourcesNotFoundException"
    }
    
    found_issues = []
    
    for issue_name, pattern in crash_patterns.items():
        if re.search(pattern, logs, re.IGNORECASE):
            found_issues.append(issue_name)
    
    if found_issues:
        print(f"\n🚨 发现可能的问题:")
        for issue in found_issues:
            print(f"  ❌ {issue}")
    else:
        print("\n✅ 未发现明显的崩溃模式")
    
    # 查找具体的异常堆栈
    exception_lines = []
    for line in logs.split('\n'):
        if any(keyword in line.lower() for keyword in ['exception', 'error', 'crash', 'fatal']):
            exception_lines.append(line.strip())
    
    if exception_lines:
        print(f"\n💥 关键异常信息:")
        for line in exception_lines[:10]:  # 只显示前10行
            print(f"  {line}")

def check_app_running():
    """检查应用是否在运行"""
    print("🔍 检查应用运行状态...")
    
    try:
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
            print("  ❌ 应用未在运行（已崩溃）")
            return False
            
    except Exception as e:
        print(f"  💥 检查运行状态异常: {e}")
        return False

def get_system_info():
    """获取系统信息"""
    print("📱 获取系统信息...")
    
    try:
        # Android版本
        android_version = subprocess.run(
            ["adb", "shell", "getprop", "ro.build.version.release"],
            capture_output=True,
            text=True
        )
        
        # API级别
        api_level = subprocess.run(
            ["adb", "shell", "getprop", "ro.build.version.sdk"],
            capture_output=True,
            text=True
        )
        
        # 设备型号
        device_model = subprocess.run(
            ["adb", "shell", "getprop", "ro.product.model"],
            capture_output=True,
            text=True
        )
        
        print(f"  📱 Android版本: {android_version.stdout.strip()}")
        print(f"  🔢 API级别: {api_level.stdout.strip()}")
        print(f"  📱 设备型号: {device_model.stdout.strip()}")
        
        # 检查API兼容性
        api = int(api_level.stdout.strip()) if api_level.stdout.strip().isdigit() else 0
        if api < 24:
            print(f"  ⚠️ API级别过低 (最低要求: 24)")
            return False
        else:
            print(f"  ✅ API级别兼容")
            return True
            
    except Exception as e:
        print(f"  💥 获取系统信息异常: {e}")
        return False

def suggest_fixes(found_issues):
    """根据发现的问题建议修复方案"""
    print("\n🔧 修复建议:")
    
    fix_suggestions = {
        "空指针异常": [
            "检查Application和MainActivity的onCreate方法",
            "确保所有@Inject字段都正确初始化",
            "检查DataStore和ViewModel的初始化顺序"
        ],
        "类找不到": [
            "检查Hilt配置是否正确",
            "确保所有依赖都在build.gradle中声明",
            "检查ProGuard规则是否正确"
        ],
        "Hilt异常": [
            "检查@HiltAndroidApp注解是否在Application类上",
            "检查@AndroidEntryPoint注解是否在Activity上",
            "检查@Module和@InstallIn注解是否正确"
        ],
        "DataStore异常": [
            "检查DataStore是否在主线程使用",
            "确保DataStore初始化在suspend函数中",
            "检查DataStore的依赖注入配置"
        ],
        "ViewModel异常": [
            "检查ViewModel构造函数是否过于复杂",
            "确保ViewModel不在init块中启动协程",
            "检查@HiltViewModel注解是否正确"
        ],
        "权限被拒绝": [
            "检查AndroidManifest.xml中的权限声明",
            "确保运行时权限请求正确",
            "检查目标SDK版本的权限要求"
        ]
    }
    
    if not found_issues:
        print("  📋 通用建议:")
        print("    1. 重新构建APK")
        print("    2. 清除应用数据后重试")
        print("    3. 检查设备兼容性")
        print("    4. 查看完整的logcat日志")
        return
    
    for issue in found_issues:
        if issue in fix_suggestions:
            print(f"\n  🚨 {issue}:")
            for suggestion in fix_suggestions[issue]:
                print(f"    • {suggestion}")

def main():
    """主函数"""
    print("🚨 APK立即闪退诊断工具")
    print("=" * 50)
    
    # 1. 检查基础环境
    if not check_adb_connection():
        return
    
    if not get_system_info():
        print("⚠️ 系统兼容性可能有问题")
    
    # 2. 检查应用状态
    if not get_app_info():
        print("❌ 请先安装APK")
        return
    
    # 3. 清除应用数据（避免旧数据干扰）
    clear_app_data()
    
    # 4. 启动应用并收集日志
    logs = start_app_with_logging()
    
    # 5. 检查应用是否还在运行
    is_running = check_app_running()
    
    # 6. 分析日志
    if logs:
        found_issues = []
        analyze_crash_logs(logs)
        
        # 从日志中提取问题类型
        crash_patterns = {
            "空指针异常": r"NullPointerException",
            "类找不到": r"ClassNotFoundException|NoClassDefFoundError",
            "Hilt异常": r"Hilt|DaggerGenerated|@Inject",
            "DataStore异常": r"DataStore|Preferences",
            "ViewModel异常": r"ViewModel|HiltViewModel",
            "权限被拒绝": r"SecurityException|Permission denied"
        }
        
        for issue_name, pattern in crash_patterns.items():
            if re.search(pattern, logs, re.IGNORECASE):
                found_issues.append(issue_name)
        
        suggest_fixes(found_issues)
    else:
        print("❌ 未能收集到有效日志")
    
    # 7. 总结
    print(f"\n📊 诊断结果:")
    print(f"  应用是否运行: {'✅ 是' if is_running else '❌ 否'}")
    print(f"  日志收集: {'✅ 成功' if logs else '❌ 失败'}")
    
    if not is_running and not logs:
        print("\n🆘 建议:")
        print("  1. 检查APK是否正确构建")
        print("  2. 尝试在模拟器上测试")
        print("  3. 检查设备的开发者选项设置")

if __name__ == "__main__":
    main() 