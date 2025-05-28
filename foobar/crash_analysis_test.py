#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK闪退问题分析测试脚本
分析激活码绑定后闪退的根本原因
"""

import requests
import json
import time

def test_binding_flow():
    """测试完整的绑定流程，模拟Android应用的行为"""
    print("🔍 APK闪退问题分析")
    print("=" * 50)
    
    # 模拟设备ID
    device_id = "92:EE:E9:01:7E:7B"  # 使用之前成功的设备ID
    ota_url = "http://47.122.144.73:8002/xiaozhi/ota/"
    
    print(f"📱 测试设备ID: {device_id}")
    print(f"🌐 OTA URL: {ota_url}")
    
    # 第一步：获取激活码（模拟首次启动）
    print("\n1️⃣ 第一步：模拟首次启动获取激活码")
    print("-" * 30)
    
    request_payload = {
        "application": {"version": "1.0.0"},
        "mac_address": device_id,
        "chip_model_name": "android",
        "board": {"type": "android"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": f"android-app-{int(time.time())}"
    }
    
    try:
        response = requests.post(ota_url, headers=headers, json=request_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 成功获取OTA响应")
            
            if "activation" in result:
                activation_code = result["activation"]["code"]
                print(f"🎯 激活码: {activation_code}")
                print("📋 完整响应:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 检查是否同时包含WebSocket URL
                if "websocket" in result:
                    websocket_url = result["websocket"]["url"]
                    print(f"\n⚠️ 关键发现：响应同时包含激活码和WebSocket URL!")
                    print(f"🔗 WebSocket URL: {websocket_url}")
                    print("\n🔍 这可能是闪退的原因：")
                    print("   1. 服务器返回了激活码，表示设备需要绑定")
                    print("   2. 但同时也返回了WebSocket URL")
                    print("   3. Android应用可能错误地认为设备已绑定")
                    print("   4. 尝试连接WebSocket但实际上设备未绑定")
                    print("   5. 导致连接失败和应用闪退")
                    
                    return analyze_websocket_connection(websocket_url, device_id)
                else:
                    print("✅ 正常：只有激活码，没有WebSocket URL")
                    return True
                    
            elif "websocket" in result:
                websocket_url = result["websocket"]["url"]
                print(f"✅ 设备已绑定，WebSocket URL: {websocket_url}")
                return analyze_websocket_connection(websocket_url, device_id)
            else:
                print("❌ 响应格式异常")
                return False
                
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def analyze_websocket_connection(websocket_url, device_id):
    """分析WebSocket连接问题"""
    print(f"\n2️⃣ 第二步：分析WebSocket连接")
    print("-" * 30)
    print(f"🔗 WebSocket URL: {websocket_url}")
    
    # 检查URL格式
    if not websocket_url.startswith("ws://") and not websocket_url.startswith("wss://"):
        print("❌ WebSocket URL格式错误：不是ws://或wss://开头")
        return False
    
    # 尝试HTTP连接测试（WebSocket握手前的HTTP请求）
    try:
        # 将ws://转换为http://进行连接测试
        http_url = websocket_url.replace("ws://", "http://").replace("wss://", "https://")
        print(f"🧪 测试HTTP连接: {http_url}")
        
        # 模拟WebSocket握手请求
        headers = {
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13",
            "Authorization": "Bearer test-token",
            "Protocol-Version": "1",
            "Device-Id": device_id,
            "Client-Id": f"android-test-{int(time.time())}"
        }
        
        response = requests.get(http_url, headers=headers, timeout=5)
        print(f"📥 HTTP响应码: {response.status_code}")
        
        if response.status_code == 101:
            print("✅ WebSocket握手成功")
            return True
        elif response.status_code == 401:
            print("❌ 认证失败：设备可能未正确绑定")
            print("🔍 这很可能是闪退的原因：")
            print("   1. 设备获得了WebSocket URL")
            print("   2. 但服务器端设备绑定状态不一致")
            print("   3. WebSocket连接被拒绝")
            print("   4. Android应用处理连接失败时出现异常")
            return False
        elif response.status_code == 404:
            print("❌ WebSocket端点不存在")
            return False
        else:
            print(f"⚠️ 意外的响应码: {response.status_code}")
            print(f"📝 响应内容: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket连接测试失败: {e}")
        print("🔍 可能的原因：")
        print("   1. 网络连接问题")
        print("   2. 服务器WebSocket服务未启动")
        print("   3. 防火墙阻止连接")
        return False

def suggest_fixes():
    """提供修复建议"""
    print(f"\n3️⃣ 第三步：修复建议")
    print("-" * 30)
    
    print("🔧 可能的修复方案：")
    print()
    
    print("1. 📱 Android应用端修复：")
    print("   - 在ChatViewModel初始化前检查WebSocket URL是否有效")
    print("   - 添加WebSocket连接失败的异常处理")
    print("   - 在连接失败时显示友好错误信息而不是闪退")
    print("   - 添加重试机制")
    print()
    
    print("2. 🔄 绑定状态同步修复：")
    print("   - 确保OTA接口返回的绑定状态与实际状态一致")
    print("   - 在绑定完成后立即验证WebSocket连接")
    print("   - 添加绑定状态缓存失效机制")
    print()
    
    print("3. 🛡️ 错误处理增强：")
    print("   - 在WebsocketProtocol中添加连接超时处理")
    print("   - 在ChatViewModel中添加try-catch包装")
    print("   - 提供降级方案（如返回配置界面）")
    print()
    
    print("4. 🧪 测试验证：")
    print("   - 测试绑定完成后立即启动应用的场景")
    print("   - 测试网络异常时的应用行为")
    print("   - 验证设备ID一致性")

def main():
    """主函数"""
    print("🚀 小智Android APK闪退问题分析")
    print("=" * 60)
    print("分析激活码绑定后应用闪退的根本原因")
    print()
    
    # 执行测试
    success = test_binding_flow()
    
    # 提供修复建议
    suggest_fixes()
    
    print(f"\n📊 分析结果")
    print("=" * 30)
    if success:
        print("✅ 绑定流程正常，闪退可能由其他原因引起")
    else:
        print("❌ 发现绑定流程问题，很可能是闪退的原因")
    
    print(f"\n🏁 分析完成")
    print("建议：根据上述分析结果修复Android应用的错误处理逻辑")

if __name__ == "__main__":
    main() 