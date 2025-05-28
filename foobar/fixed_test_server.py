#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的小智测试服务器
只返回激活码，不返回WebSocket配置，用于测试绑定流程
"""

from flask import Flask, request, jsonify
import json
import random
import time

app = Flask(__name__)

@app.route('/')
def index():
    return "修复后的小智测试服务器运行中"

@app.route('/xiaozhi/ota/', methods=['POST'])
def ota_check():
    """OTA检查端点 - 只返回激活码"""
    try:
        data = request.get_json()
        print(f"收到OTA请求: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 生成随机激活码
        activation_code = f"{random.randint(100000, 999999)}"
        
        # 只返回激活码，不返回WebSocket配置
        response = {
            "server_time": {
                "timestamp": int(time.time() * 1000),
                "timeZone": "Asia/Shanghai",
                "timezone_offset": 480
            },
            "activation": {
                "code": activation_code,
                "message": f"http://192.168.0.129:8002/#/home\n{activation_code}"
            }
            # 注意：这里不返回websocket字段
        }
        
        print(f"返回响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
        return jsonify(response)
        
    except Exception as e:
        print(f"OTA处理错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/xiaozhi/ota/', methods=['GET'])
def ota_info():
    """OTA信息端点"""
    return jsonify({
        "service": "xiaozhi-ota-fixed",
        "version": "1.0.0",
        "status": "running",
        "note": "只返回激活码，用于测试绑定流程"
    })

if __name__ == '__main__':
    print("启动修复后的小智测试服务器...")
    print("OTA端点: http://192.168.0.129:8003/xiaozhi/ota/")
    print("特点: 只返回激活码，不返回WebSocket配置")
    print("用途: 测试Android应用的绑定流程")
    
    app.run(host='0.0.0.0', port=8003, debug=True) 