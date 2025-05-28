#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试紧急修复效果
"""

import subprocess
import time

def test_emergency_fix():
    """测试紧急修复效果"""
    print("🧪 测试紧急修复效果")
    
    # 重启应用
    subprocess.run(["adb", "shell", "am", "force-stop", "info.dourok.voicebot"])
    time.sleep(1)
    subprocess.run(["adb", "shell", "am", "start", "-n", "info.dourok.voicebot/.MainActivity"])
    
    print("监控关键日志...")
    
    # 监控关键日志
    process = subprocess.Popen([
        "adb", "logcat", "-v", "time", "-s", "SmartAppNavigation:D", "ChatScreen:D", "SmartBindingViewModel:D"
    ], stdout=subprocess.PIPE, text=True)
    
    try:
        for i in range(30):  # 监控30秒
            line = process.stdout.readline()
            if line:
                print(f"[{time.strftime('%H:%M:%S')}] {line.strip()}")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        process.terminate()

if __name__ == "__main__":
    test_emergency_fix()
