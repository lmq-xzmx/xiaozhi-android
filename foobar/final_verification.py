#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证脚本 - 检查编译问题并提供解决方案
"""

import os
import subprocess
import sys

def check_kotlin_files():
    """检查关键的Kotlin文件是否存在并正确定义"""
    files_to_check = [
        "app/src/main/java/info/dourok/voicebot/data/model/MqttConfig.kt",
        "app/src/main/java/info/dourok/voicebot/data/model/TransportType.kt",
        "app/src/main/java/info/dourok/voicebot/data/SettingsRepository.kt",
        "app/src/main/java/info/dourok/voicebot/data/FormRepository.kt",
        "app/src/main/java/info/dourok/voicebot/domain/ValidateFormUseCase.kt",
        "app/src/main/java/info/dourok/voicebot/ui/ServerFormScreen.kt",
        "app/src/main/java/info/dourok/voicebot/Ota.kt"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            
    if missing_files:
        print("❌ 缺少关键文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ 所有关键文件存在")
        return True

def check_cmake_issue():
    """检查CMake问题"""
    print("\n🔧 检查CMake配置...")
    
    # 删除CMake缓存
    cmake_dirs = [
        "app/.cxx",
        ".gradle/8.10.2",
        ".gradle/8.11.1"
    ]
    
    for dir_path in cmake_dirs:
        if os.path.exists(dir_path):
            print(f"   删除 {dir_path}")
            subprocess.run(["rm", "-rf", dir_path], capture_output=True)
    
    print("✅ CMake缓存已清理")

def check_compilation():
    """检查编译状态"""
    print("\n📦 检查编译...")
    
    # 简单的语法检查
    try:
        result = subprocess.run(
            ["./gradlew", "compileDebugKotlin", "--stacktrace"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Kotlin编译成功")
            return True
        else:
            print("❌ Kotlin编译失败:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 编译超时")
        return False
    except Exception as e:
        print(f"❌ 编译检查失败: {e}")
        return False

def main():
    print("🎯 最终验证 - OTA配置升级完成检查")
    print("=" * 50)
    
    # 步骤1: 检查文件
    if not check_kotlin_files():
        print("\n❌ 请先确保所有必要文件存在")
        return
    
    # 步骤2: 清理CMake
    check_cmake_issue()
    
    # 步骤3: 检查编译
    compilation_ok = check_compilation()
    
    print("\n" + "=" * 50)
    print("📋 编译手动指令:")
    print()
    print("1. 清理项目:")
    print("   ./gradlew clean")
    print()
    print("2. 编译APK:")
    print("   ./gradlew assembleDebug")
    print()
    print("3. 安装APK:")
    print("   adb -s SOZ95PIFVS5H6PIZ install app/build/outputs/apk/debug/app-debug.apk")
    print()
    
    if compilation_ok:
        print("🎉 编译验证成功！可以直接安装APK。")
    else:
        print("⚠️ 存在编译问题，请手动执行上述命令进行编译。")
        
    print("\n💡 如果遇到CMake问题，可以:")
    print("   - 删除 .gradle 目录: rm -rf .gradle")
    print("   - 删除 app/.cxx 目录: rm -rf app/.cxx")
    print("   - 重新运行: ./gradlew clean && ./gradlew assembleDebug")

if __name__ == "__main__":
    main() 