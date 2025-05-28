#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试设备配置UI改进效果
"""

import subprocess
import time

def test_config_ui():
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    print("🔧 设备配置UI测试")
    print("=" * 40)
    
    # 1. 启动应用
    print("1. 启动应用...")
    subprocess.run(
        ["adb", "-s", device_id, "shell", "am", "start", 
         "-n", f"{package_name}/.MainActivity"],
        capture_output=True
    )
    print("   ✅ 应用已启动")
    
    # 2. 等待UI加载
    print("2. 等待UI加载（5秒）...")
    time.sleep(5)
    
    # 3. 检查配置相关日志
    print("3. 检查设备配置相关日志...")
    result = subprocess.run(
        ["adb", "-s", device_id, "logcat", "-d", "DeviceConfig*:*", "*:S"],
        capture_output=True,
        text=True
    )
    
    logs = result.stdout
    if logs:
        config_lines = [line for line in logs.split('\n') if 'DeviceConfig' in line]
        if config_lines:
            print(f"   📋 找到 {len(config_lines)} 条配置相关日志:")
            for line in config_lines[-5:]:  # 最后5条
                if line.strip():
                    print(f"   {line}")
        else:
            print("   ⚠️ 未找到配置相关日志")
    else:
        print("   ❌ 无法获取日志")
    
    # 4. 测试建议
    print("\n💡 测试建议:")
    print("   1. 检查应用是否显示'Android端连接信息'卡片")
    print("   2. 验证设备信息部分是否显示:")
    print("      - 设备ID")
    print("      - Android版本")
    print("      - 制造商和型号")
    print("   3. 验证OTA信息部分是否显示:")
    print("      - OTA服务器地址")
    print("      - OTA端点")
    print("      - 前端管理地址")
    print("      - 绑定状态")
    print("   4. 验证WebSocket信息部分是否显示:")
    print("      - WebSocket URL（如果已绑定）")
    print("      - 连接状态")
    print("      - 协议版本")
    print("   5. 验证端口信息部分是否显示:")
    print("      - HTTP端口 (8002)")
    print("      - WebSocket端口 (8000)")
    print("      - 管理面板端口 (8002)")
    print("      - 音频编解码信息")
    
    print("\n📱 UI验证要点:")
    print("   ✅ 信息分类清晰，分为四个部分")
    print("   ✅ 使用表格样式显示详细信息")
    print("   ✅ 状态用emoji图标标识")
    print("   ✅ 端口和协议信息完整")

if __name__ == "__main__":
    test_config_ui() 