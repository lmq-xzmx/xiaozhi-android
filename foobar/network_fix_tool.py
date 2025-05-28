#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智Android网络连接修复工具
诊断和修复WebSocket连接问题
"""

import subprocess
import time
import json
import requests
from urllib.parse import urlparse

class NetworkFixTool:
    def __init__(self, device_id="SOZ95PIFVS5H6PIZ"):
        self.device_id = device_id
        self.package_name = "info.dourok.voicebot"
        self.target_server = "47.122.144.73"
        self.ota_port = 8002
        self.websocket_port = 8000
    
    def test_server_connectivity(self):
        """测试服务器连接性"""
        print("🌐 测试服务器连接性...")
        
        # 测试不同的连接方式
        tests = [
            ("ping", f"ping -c 3 {self.target_server}"),
            ("telnet OTA端口", f"timeout 5 telnet {self.target_server} {self.ota_port}"),
            ("telnet WebSocket端口", f"timeout 5 telnet {self.target_server} {self.websocket_port}"),
            ("curl OTA", f"curl -m 10 http://{self.target_server}:{self.ota_port}/"),
            ("curl WebSocket", f"curl -m 10 http://{self.target_server}:{self.websocket_port}/")
        ]
        
        results = {}
        for test_name, command in tests:
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    results[test_name] = "✅ 成功"
                else:
                    results[test_name] = f"❌ 失败 (code: {result.returncode})"
            except subprocess.TimeoutExpired:
                results[test_name] = "⏰ 超时"
            except Exception as e:
                results[test_name] = f"❌ 错误: {e}"
        
        for test, result in results.items():
            print(f"  {test}: {result}")
        
        return results
    
    def test_ota_endpoint(self):
        """测试OTA端点"""
        print("\n🔍 测试OTA端点...")
        
        ota_url = f"http://{self.target_server}:{self.ota_port}/xiaozhi/ota/"
        
        # 构建测试请求
        test_request = {
            "application": {
                "version": "1.0.0",
                "name": "xiaozhi-android",
                "compile_time": "2025-01-27 12:00:00"
            },
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "chipModelName": "android",
            "board": {
                "type": "android",
                "manufacturer": "TestDevice",
                "model": "TestModel",
                "version": "14"
            },
            "uuid": "test-android-uuid-12345"
        }
        
        try:
            print(f"  请求URL: {ota_url}")
            print(f"  请求数据: {json.dumps(test_request, indent=2)}")
            
            response = requests.post(
                ota_url,
                json=test_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"  响应状态: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"  响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    return True, response_data
                except json.JSONDecodeError:
                    print(f"  响应文本: {response.text}")
                    return False, response.text
            else:
                print(f"  错误响应: {response.text}")
                return False, response.text
                
        except requests.exceptions.ConnectTimeout:
            print("  ❌ 连接超时")
            return False, "连接超时"
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ 连接错误: {e}")
            return False, f"连接错误: {e}"
        except Exception as e:
            print(f"  ❌ 其他错误: {e}")
            return False, f"其他错误: {e}"
    
    def test_alternative_servers(self):
        """测试替代服务器"""
        print("\n🔄 测试替代服务器...")
        
        # 一些可能的替代服务器
        alternative_servers = [
            "localhost:8002",
            "127.0.0.1:8002", 
            "192.168.1.100:8002",  # 常见的局域网地址
            "10.0.0.100:8002",     # 另一个常见的局域网地址
        ]
        
        for server in alternative_servers:
            try:
                url = f"http://{server}/xiaozhi/ota/"
                print(f"  测试: {url}")
                
                response = requests.get(url, timeout=3)
                print(f"    ✅ 可达 (状态: {response.status_code})")
                
                if response.status_code == 200:
                    print(f"    建议使用此服务器: {server}")
                    return server
                    
            except Exception as e:
                print(f"    ❌ 不可达: {e}")
        
        return None
    
    def suggest_network_fixes(self):
        """建议网络修复方案"""
        print("\n💡 网络修复建议:")
        
        print("1. **检查服务器状态**:")
        print("   - 确认小智服务器是否正在运行")
        print("   - 检查服务器防火墙设置")
        print("   - 验证端口8002和8000是否开放")
        
        print("\n2. **检查网络环境**:")
        print("   - 确认设备和服务器在同一网络")
        print("   - 检查路由器/防火墙设置")
        print("   - 尝试使用VPN或更换网络")
        
        print("\n3. **修改应用配置**:")
        print("   - 在应用设置中更改OTA URL")
        print("   - 使用局域网IP地址替代公网IP")
        print("   - 临时使用测试服务器")
        
        print("\n4. **本地测试方案**:")
        print("   - 在本地启动小智服务器")
        print("   - 修改应用配置指向本地服务器")
        print("   - 使用模拟器测试连接")
    
    def create_local_test_server(self):
        """创建本地测试服务器脚本"""
        print("\n🛠️ 创建本地测试服务器...")
        
        server_script = '''#!/usr/bin/env python3
"""
小智本地测试服务器
用于测试Android应用的OTA和WebSocket连接
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xiaozhi-test-server'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/xiaozhi/ota/', methods=['POST'])
def ota_check():
    """OTA检查端点"""
    try:
        data = request.get_json()
        print(f"收到OTA请求: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 生成随机激活码
        activation_code = f"{random.randint(100000, 999999)}"
        
        response = {
            "server_time": {
                "timestamp": int(time.time() * 1000),
                "timeZone": "Asia/Shanghai",
                "timezone_offset": 480
            },
            "activation": {
                "code": activation_code,
                "message": f"http://localhost:8002/#/home\\n{activation_code}"
            },
            "websocket": {
                "url": "ws://localhost:8000/xiaozhi/v1/"
            }
        }
        
        print(f"返回响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
        return jsonify(response)
        
    except Exception as e:
        print(f"OTA处理错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "小智本地测试服务器运行中"

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('response', {'data': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开')

@socketio.on('message')
def handle_message(data):
    print(f'收到消息: {data}')
    emit('response', {'data': f'收到: {data}'})

if __name__ == '__main__':
    print("启动小智本地测试服务器...")
    print("OTA端点: http://localhost:8002/xiaozhi/ota/")
    print("WebSocket端点: ws://localhost:8000/xiaozhi/v1/")
    print("管理面板: http://localhost:8002/#/home")
    
    # 在不同端口启动HTTP和WebSocket服务
    socketio.run(app, host='0.0.0.0', port=8002, debug=True)
'''
        
        with open("foobar/local_test_server.py", "w", encoding="utf-8") as f:
            f.write(server_script)
        
        print("  ✅ 本地测试服务器脚本已创建: foobar/local_test_server.py")
        print("  📦 安装依赖: pip install flask flask-socketio")
        print("  🚀 启动服务器: python3 foobar/local_test_server.py")
    
    def run_diagnosis(self):
        """运行完整网络诊断"""
        print("🔧 小智Android网络连接诊断工具")
        print("=" * 60)
        
        # 1. 测试基础连接
        connectivity_results = self.test_server_connectivity()
        
        # 2. 测试OTA端点
        ota_success, ota_result = self.test_ota_endpoint()
        
        # 3. 如果主服务器不可达，测试替代服务器
        if not ota_success:
            alternative = self.test_alternative_servers()
            if alternative:
                print(f"\n✅ 找到可用的替代服务器: {alternative}")
            else:
                print("\n❌ 未找到可用的替代服务器")
        
        # 4. 提供修复建议
        self.suggest_network_fixes()
        
        # 5. 创建本地测试服务器
        self.create_local_test_server()
        
        print("\n" + "=" * 60)
        print("🎯 总结:")
        if ota_success:
            print("  ✅ 网络连接正常，问题可能在应用端")
        else:
            print("  ❌ 网络连接有问题，需要修复网络配置")
            print("  💡 建议使用本地测试服务器进行调试")

def main():
    tool = NetworkFixTool()
    tool.run_diagnosis()

if __name__ == "__main__":
    main() 