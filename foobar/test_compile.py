#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试编译脚本
"""

import subprocess
import sys

def test_compile():
    """测试编译"""
    print("🔧 测试Kotlin编译...")
    
    try:
        result = subprocess.run(
            ["./gradlew", "compileDebugKotlin"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            print("✅ Kotlin编译成功！")
            print("🚀 开始完整APK编译...")
            
            # 完整编译
            result2 = subprocess.run(
                ["./gradlew", "assembleDebug"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result2.returncode == 0:
                print("🎉 APK编译成功！")
                return True
            else:
                print("❌ APK编译失败:")
                print(result2.stderr[-1000:])  # 显示最后1000个字符
                return False
                
        else:
            print("❌ Kotlin编译失败:")
            print(result.stderr[-1000:])  # 显示最后1000个字符
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 编译超时")
        return False
    except Exception as e:
        print(f"❌ 编译异常: {e}")
        return False

if __name__ == "__main__":
    success = test_compile()
    if success:
        print("\n🎯 编译成功！现在可以安装APK：")
        print("adb -s SOZ95PIFVS5H6PIZ install app/build/outputs/apk/debug/app-debug.apk")
    else:
        print("\n❌ 编译失败，请检查错误信息") 