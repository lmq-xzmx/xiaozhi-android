#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果
验证Android应用是否正确显示绑定流程
"""

import subprocess
import time
import requests
import json

def test_fixed_server():
    """测试修复后的服务器"""
    print("🧪 测试修复后的服务器...")
    
    url = "http://192.168.0.129:8003/xiaozhi/ota/"
    data = {
        "macAddress": "AA:BB:CC:DD:EE:FF",
        "chipModelName": "android",
        "application": {"version": "1.0.0", "name": "xiaozhi-android"},
        "board": {"type": "android"},
        "uuid": "test-uuid"
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务器响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            has_activation = "activation" in result
            has_websocket = "websocket" in result
            
            print(f"包含激活码: {has_activation}")
            print(f"包含WebSocket: {has_websocket}")
            
            if has_activation and not has_websocket:
                print("✅ 完美！只有激活码，没有WebSocket配置")
                return True
            else:
                print("❌ 配置错误")
                return False
        else:
            print(f"❌ 服务器错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_android_app():
    """测试Android应用"""
    print("\n📱 测试Android应用...")
    
    device_id = "SOZ95PIFVS5H6PIZ"
    package_name = "info.dourok.voicebot"
    
    try:
        # 清除应用数据
        print("🧹 清除应用数据...")
        subprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "clear", package_name],
            capture_output=True
        )
        
        # 启动应用
        print("🚀 启动应用...")
        subprocess.run(
            ["adb", "-s", device_id, "shell", "am", "start", 
             "-n", f"{package_name}/.MainActivity"],
            capture_output=True
        )
        
        # 等待应用初始化
        time.sleep(3)
        
        print("📋 应用应该显示设备配置界面")
        print("💡 请手动操作：")
        print("1. 在设备配置界面修改OTA URL为: http://192.168.0.129:8003/xiaozhi/ota/")
        print("2. 点击保存")
        print("3. 点击'检查绑定状态'")
        print("4. 观察是否显示激活码和绑定引导界面")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("🔧 小智Android绑定流程修复测试")
    print("=" * 50)
    
    # 1. 测试修复后的服务器
    server_ok = test_fixed_server()
    
    if server_ok:
        # 2. 测试Android应用
        test_android_app()
        
        print("\n🎯 预期结果:")
        print("✅ 应用不再直接进入聊天界面")
        print("✅ 显示设备配置界面")
        print("✅ OTA检查后显示激活码")
        print("✅ 出现绑定引导界面")
        print("✅ 状态从'Idle'变为'需要绑定'")
    else:
        print("❌ 服务器测试失败，请检查服务器是否运行")

if __name__ == "__main__":
    main() 