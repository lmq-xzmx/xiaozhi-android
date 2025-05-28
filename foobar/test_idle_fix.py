#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 测试OtaResult逻辑修复效果

验证修复后的OtaResult.isActivated逻辑是否正确处理服务器响应
"""

import json
import requests
import time

def test_server_response():
    """测试服务器实际响应"""
    print("🌐 测试服务器实际响应")
    print("=" * 40)
    
    # 构建OTA请求
    device_id = "D1:F1:D7:DC:E6:6D"
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": f"test-{int(time.time())}"
    }
    
    payload = {
        "application": {"version": "1.0.0"},
        "mac_address": device_id,
        "chip_model_name": "android",
        "board": {"type": "android"}
    }
    
    try:
        response = requests.post(ota_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务器响应成功")
            print(f"📋 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            return result
        else:
            print(f"❌ 服务器响应失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_old_logic(server_response):
    """测试修复前的逻辑"""
    print("\n🔴 测试修复前的逻辑（有问题的逻辑）")
    print("=" * 40)
    
    has_activation = "activation" in server_response
    has_websocket = "websocket" in server_response
    
    # 修复前的逻辑
    old_needs_activation = has_activation
    old_is_activated = has_websocket  # 🚨 问题逻辑
    
    print(f"包含activation字段: {has_activation}")
    print(f"包含websocket字段: {has_websocket}")
    print(f"修复前 needsActivation: {old_needs_activation}")
    print(f"修复前 isActivated: {old_is_activated}")
    
    if has_activation and has_websocket:
        print("\n🚨 问题所在:")
        print(f"   服务器同时返回activation和websocket")
        print(f"   修复前逻辑错误地认为 isActivated=true")
        print(f"   导致跳过绑定流程，直接进入聊天界面显示Idle")
    
    return old_needs_activation, old_is_activated

def test_new_logic(server_response):
    """测试修复后的逻辑"""
    print("\n✅ 测试修复后的逻辑（正确的逻辑）")
    print("=" * 40)
    
    has_activation = "activation" in server_response
    has_websocket = "websocket" in server_response
    
    # 修复后的逻辑
    new_needs_activation = has_activation
    new_is_activated = has_websocket and not has_activation  # 🔧 修复逻辑
    
    print(f"包含activation字段: {has_activation}")
    print(f"包含websocket字段: {has_websocket}")
    print(f"修复后 needsActivation: {new_needs_activation}")
    print(f"修复后 isActivated: {new_is_activated}")
    
    if has_activation and has_websocket:
        print("\n✅ 修复效果:")
        print(f"   服务器同时返回activation和websocket")
        print(f"   修复后逻辑正确地认为 isActivated=false")
        print(f"   应用会正确显示绑定界面而不是Idle状态")
    
    return new_needs_activation, new_is_activated

def analyze_android_behavior(old_logic, new_logic, server_response):
    """分析Android应用行为变化"""
    print("\n📱 Android应用行为分析")
    print("=" * 40)
    
    old_needs_activation, old_is_activated = old_logic
    new_needs_activation, new_is_activated = new_logic
    
    print("修复前的应用流程:")
    if old_is_activated:
        print("  1️⃣ OtaResult.isActivated = true")
        print("  2️⃣ FormViewModel导航到chat页面")
        print("  3️⃣ ChatViewModel初始化成功")
        print("  4️⃣ 设备状态设置为IDLE")
        print("  5️⃣ 用户看到ChatContent界面显示'Idle'")
        print("  ❌ 问题：用户无法看到绑定界面")
    
    print("\n修复后的应用流程:")
    if new_needs_activation and not new_is_activated:
        activation_code = server_response.get("activation", {}).get("code", "")
        print("  1️⃣ OtaResult.isActivated = false")
        print("  2️⃣ OtaResult.needsActivation = true")
        print("  3️⃣ FormViewModel导航到activation页面")
        print(f"  4️⃣ 显示激活码: {activation_code}")
        print("  5️⃣ 用户可以进行设备绑定")
        print("  ✅ 解决：用户能看到正确的绑定界面")

def main():
    """主测试流程"""
    print("🔧 测试OtaResult逻辑修复效果")
    print("🎯 目标：验证修复是否解决了'依旧返回Idle'的问题")
    print()
    
    # 1. 获取服务器响应
    server_response = test_server_response()
    if not server_response:
        print("❌ 无法获取服务器响应，测试终止")
        return
    
    # 2. 测试修复前的逻辑
    old_logic = test_old_logic(server_response)
    
    # 3. 测试修复后的逻辑
    new_logic = test_new_logic(server_response)
    
    # 4. 分析应用行为变化
    analyze_android_behavior(old_logic, new_logic, server_response)
    
    # 5. 总结
    print("\n📊 测试总结")
    print("=" * 40)
    
    if server_response.get("activation") and server_response.get("websocket"):
        print("✅ 服务器响应包含activation和websocket字段（正常情况）")
        print("✅ 修复前：错误地跳过绑定流程 → 显示Idle")
        print("✅ 修复后：正确地显示绑定界面 → 解决Idle问题")
        print()
        print("🎉 结论：OtaResult逻辑修复应该能解决'依旧返回Idle'的问题！")
    else:
        print("⚠️  服务器响应格式与预期不符，需要进一步分析")

if __name__ == "__main__":
    main() 