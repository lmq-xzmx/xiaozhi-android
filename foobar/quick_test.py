#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证WebSocket修复效果
"""

import subprocess
import time

def test_websocket_fix():
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🔧 WebSocket修复验证测试")
    print("=" * 40)
    
    # 1. 清除应用数据
    print("1. 清除应用数据...")
    result = subprocess.run(
        ["adb", "-s", device_id, "shell", "pm", "clear", package_name],
        capture_output=True
    )
    if result.returncode == 0:
        print("   ✅ 应用数据已清除")
    else:
        print("   ❌ 清除失败")
    
    # 2. 清除日志
    print("2. 清除日志...")
    subprocess.run(["adb", "-s", device_id, "logcat", "-c"], capture_output=True)
    print("   ✅ 日志已清除")
    
    # 3. 启动应用
    print("3. 启动应用...")
    subprocess.run(
        ["adb", "-s", device_id, "shell", "am", "start", 
         "-n", f"{package_name}/.MainActivity"],
        capture_output=True
    )
    print("   ✅ 应用已启动")
    
    # 4. 等待初始化
    print("4. 等待应用初始化（10秒）...")
    time.sleep(10)
    
    # 5. 检查WebSocket日志
    print("5. 检查WebSocket连接日志...")
    result = subprocess.run(
        ["adb", "-s", device_id, "logcat", "-d", "WS:*", "*:S"],
        capture_output=True,
        text=True
    )
    
    logs = result.stdout
    if logs:
        lines = logs.split('\n')
        websocket_lines = [line for line in lines if 'WS' in line or 'WebSocket' in line]
        
        print(f"   📋 找到 {len(websocket_lines)} 条WebSocket日志:")
        for line in websocket_lines[-10:]:  # 最后10条
            if line.strip():
                print(f"   {line}")
        
        # 检查关键事件
        has_start = any("protocol start" in line for line in websocket_lines)
        has_connecting = any("正在建立" in line for line in websocket_lines)
        has_connected = any("connected successfully" in line for line in websocket_lines)
        has_hello = any("hello" in line.lower() for line in websocket_lines)
        
        print(f"\n   🔍 关键事件检查:")
        print(f"   协议启动: {'✅' if has_start else '❌'}")
        print(f"   开始连接: {'✅' if has_connecting else '❌'}")
        print(f"   连接成功: {'✅' if has_connected else '❌'}")
        print(f"   Hello消息: {'✅' if has_hello else '❌'}")
        
        if has_connected and has_hello:
            print(f"\n   🎉 修复成功！WebSocket连接已建立")
        elif has_start and has_connecting:
            print(f"\n   ⚠️ 修复生效，但连接可能有问题")
        else:
            print(f"\n   ❌ 修复未生效或应用未正常启动")
    else:
        print("   ❌ 未找到WebSocket相关日志")
    
    print(f"\n💡 请手动检查应用界面:")
    print(f"   - 应用是否还显示'Idle'状态？")
    print(f"   - 尝试点击聊天按钮测试功能")
    print(f"   - 观察状态变化")

if __name__ == "__main__":
    test_websocket_fix() 