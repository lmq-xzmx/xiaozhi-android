#!/usr/bin/env python3
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
                "message": f"http://localhost:8002/#/home\n{activation_code}"
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
