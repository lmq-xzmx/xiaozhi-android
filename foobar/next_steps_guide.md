# 📋 下一步操作指南

## 🎯 当前状态总结

✅ **问题已确认**：您的Android应用STT不工作是因为设备绑定问题  
✅ **OTA接口测试成功**：使用`mac_address`字段名的请求格式正确  
✅ **解决方案明确**：需要进行设备绑定来解决STT问题  

## 🚀 立即执行的步骤

### 第1步：获取新设备的激活码

由于测试设备ID `aa:bb:cc:dd:ee:ff` 已经绑定，我们需要用一个新的设备ID获取激活码：

```bash
# 在Terminal中执行（不要用PowerShell）
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 00:11:22:33:44:55" \
  -H "Client-Id: android-test-new" \
  -d '{
    "mac_address": "00:11:22:33:44:55",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    },
    "chip_model_name": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

**期望响应**：
```json
{
  "activation": {
    "code": "123456",
    "message": "http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30\n123456"
  },
  "websocket": {
    "url": "ws://47.122.144.73:8000/xiaozhi/v1/"
  }
}
```

### 第2步：管理面板绑定设备

1. **打开管理面板**：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
2. **输入激活码**：在设备绑定界面输入获得的6位数字激活码
3. **确认绑定**：完成设备绑定操作

### 第3步：修改Android应用配置

将Android应用中的设备ID修改为新绑定的设备ID：

**文件位置**：`app/src/main/java/info/dourok/voicebot/data/model/ServerFormData.kt`

```kotlin
// 找到硬编码的设备ID配置并修改为：
val deviceId = "00:11:22:33:44:55"  // 使用刚绑定的设备ID
```

### 第4步：测试STT功能

1. **重新编译运行**Android应用
2. **连接WebSocket**：确认WebSocket连接成功
3. **测试STT**：尝试语音输入，验证STT功能是否正常

## 🔧 替代方案（如果curl不工作）

### 使用Python脚本

在Terminal中执行：
```bash
cd /Users/xzmx/Downloads/my-project/xiaozhi-android/foobar
python3 -c "
import requests
import json

device_id = '00:11:22:33:44:55'
headers = {
    'Content-Type': 'application/json',
    'Device-Id': device_id,
    'Client-Id': 'android-test-new'
}
payload = {
    'mac_address': device_id,
    'application': {'version': '1.0.0'},
    'board': {'type': 'android'},
    'chip_model_name': 'android'
}

response = requests.post('http://47.122.144.73:8002/xiaozhi/ota/', headers=headers, json=payload)
print('Status:', response.status_code)
print('Response:', json.dumps(response.json(), indent=2, ensure_ascii=False))
"
```

### 使用Postman或其他API工具

**URL**: `POST http://47.122.144.73:8002/xiaozhi/ota/`

**Headers**:
```
Content-Type: application/json
Device-Id: 00:11:22:33:44:55
Client-Id: android-test-new
```

**Body**:
```json
{
  "mac_address": "00:11:22:33:44:55",
  "application": {
    "version": "1.0.0"
  },
  "board": {
    "type": "android"
  },
  "chip_model_name": "android"
}
```

## 🎯 预期结果

完成上述步骤后：

1. ✅ **设备绑定成功**：新设备ID已绑定到您的账户
2. ✅ **WebSocket连接正常**：应用可以正常连接到WebSocket
3. ✅ **STT功能恢复**：语音识别功能开始正常工作
4. ✅ **问题解决**：Android应用完全恢复STT功能

## 🚨 注意事项

1. **设备ID一致性**：确保Device-Id头部和mac_address字段完全一致
2. **MAC地址格式**：使用标准MAC地址格式（如：00:11:22:33:44:55）
3. **管理面板访问**：确保能正常访问管理面板网站
4. **激活码有效期**：激活码可能有时效性，建议及时使用

## 🆘 如果遇到问题

1. **激活码无效**：重新获取新的激活码
2. **管理面板无法访问**：检查网络连接和URL是否正确
3. **STT仍不工作**：检查Android应用的设备ID配置是否正确
4. **WebSocket连接失败**：确认WebSocket URL配置正确

---
**下一步就是执行第1步获取激活码！选择您方便的方法（curl、Python或Postman）来获取激活码。** 