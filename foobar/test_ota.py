#!/usr/bin/env python3
import requests
import json

data = {
    'macAddress': 'AA:BB:CC:DD:EE:FF',
    'chipModelName': 'android',
    'application': {'version': '1.0.0', 'name': 'xiaozhi-android'},
    'board': {'type': 'android'},
    'uuid': 'test-uuid'
}

try:
    response = requests.post('http://localhost:8002/xiaozhi/ota/', json=data, timeout=5)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
except Exception as e:
    print(f'错误: {e}') 