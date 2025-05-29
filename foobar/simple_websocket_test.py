import requests
import json

def test_server():
    print("=== WebSocket服务器连通性测试 ===")
    
    # 测试HTTP端点
    try:
        print("1. 测试HTTP连通性...")
        response = requests.get("http://47.122.144.73:8000/", timeout=10)
        print(f"   ✅ HTTP状态: {response.status_code}")
        print(f"   📄 响应: {response.text[:100]}...")
    except Exception as e:
        print(f"   ❌ HTTP连接失败: {e}")
        return False
    
    # 测试OTA端点
    try:
        print("2. 测试OTA端点...")
        response = requests.get("http://47.122.144.73:8002/xiaozhi/ota/", timeout=10)
        print(f"   ✅ OTA状态: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ OTA连接: {e}")
    
    # 分析WebSocket地址
    print("3. 分析WebSocket配置...")
    ws_url = "ws://47.122.144.73:8000/xiaozhi/v1/"
    print(f"   WebSocket URL: {ws_url}")
    print(f"   服务器: 47.122.144.73")
    print(f"   端口: 8000")
    print(f"   路径: /xiaozhi/v1/")
    
    # 诊断Android连接问题
    print("4. Android连接问题诊断...")
    print("   基于日志'WebSocket is null'，可能原因:")
    print("   - ❌ onOpen回调未触发")
    print("   - ❌ 连接建立失败")
    print("   - ❌ 网络权限问题") 
    print("   - ❌ Hello握手超时")
    
    return True

if __name__ == "__main__":
    test_server() 