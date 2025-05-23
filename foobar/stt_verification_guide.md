# 🎯 STT功能验证指南

## 📊 当前状态

✅ **代码已修改**：DeviceInfo.kt中的设备ID已设置为固定值 `00:11:22:33:44:55`

## 🚀 验证步骤

### 第1步：检查设备绑定状态

**方法1：使用Terminal（非PowerShell）**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 00:11:22:33:44:55" \
  -H "Client-Id: android-app" \
  -d '{
    "mac_address": "00:11:22:33:44:55",
    "application": {"version": "1.0.0"},
    "board": {"type": "android"},
    "chip_model_name": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

**方法2：使用Python（如果curl不可用）**
```python
import requests
import json

response = requests.post(
    "http://47.122.144.73:8002/xiaozhi/ota/",
    headers={
        "Content-Type": "application/json",
        "Device-Id": "00:11:22:33:44:55",
        "Client-Id": "android-app"
    },
    json={
        "mac_address": "00:11:22:33:44:55",
        "application": {"version": "1.0.0"},
        "board": {"type": "android"},
        "chip_model_name": "android"
    }
)

result = response.json()
if "activation" in result:
    print(f"需要绑定，激活码: {result['activation']['code']}")
elif "websocket" in result:
    print("设备已绑定，可以测试STT")
else:
    print("意外响应:", result)
```

### 第2步：设备绑定（如果需要）

如果第1步返回激活码，请执行：

1. **访问管理面板**：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
2. **输入激活码**：在设备绑定界面输入获得的6位数字激活码
3. **确认绑定**：完成设备绑定操作

### 第3步：清除应用数据（重要！）

**方法1：使用ADB命令**
```bash
adb shell pm clear info.dourok.voicebot
```

**方法2：手动清除**
1. 在Android设备上打开"设置"
2. 进入"应用管理" 或 "应用"
3. 找到"VoiceBot"应用
4. 点击"存储"
5. 点击"清除数据"

**为什么要清除数据？**
- 确保应用使用新的固定设备ID
- 清除旧的随机设备ID缓存
- 重新初始化设备信息

### 第4步：重新编译和运行应用

1. **重新编译**Android项目
2. **安装到设备**
3. **启动应用**

### 第5步：验证STT功能

#### 5.1 检查设备ID日志

在`WebsocketProtocol.kt`文件第79行附近添加日志：
```kotlin
.addHeader("Device-Id", deviceInfo.mac_address)
Log.d("DeviceInfo", "Current Device-Id: ${deviceInfo.mac_address}")
```

**预期结果**：日志应显示 `Current Device-Id: 00:11:22:33:44:55`

#### 5.2 验证WebSocket连接

**预期行为**：
- ✅ WebSocket连接成功
- ✅ 没有绑定错误提示
- ✅ 应用正常初始化

#### 5.3 测试STT功能

1. **点击录音按钮**
2. **说话测试**：说一些简单的话
3. **观察结果**：
   - ✅ 应该显示转录的文字
   - ✅ 没有"需要绑定设备"的提示
   - ✅ STT功能正常工作

## 🔍 故障排除

### 问题1：设备ID仍然是随机的

**解决方案**：
- 确认代码修改正确
- 完全清除应用数据
- 重新编译安装

### 问题2：WebSocket连接失败

**检查项目**：
- 网络连接是否正常
- WebSocket URL是否正确
- 设备是否已正确绑定

### 问题3：STT仍然不工作

**可能原因**：
- 设备绑定未完成
- 设备ID不匹配
- 服务器端问题

**验证方法**：
- 重新检查设备绑定状态
- 查看应用日志中的设备ID
- 确认WebSocket连接状态

## 📱 成功标志

### 完全成功的STT应该显示：

1. **日志输出**：
   ```
   Current Device-Id: 00:11:22:33:44:55
   WebSocket connected successfully
   ```

2. **应用行为**：
   - 语音识别按钮可用
   - 说话后显示转录文字
   - 没有错误提示

3. **服务器响应**：
   - WebSocket消息正常
   - STT响应及时
   - 没有绑定错误

## 🎯 快速验证命令

创建这个快速测试脚本：

```bash
# 创建 quick_stt_test.sh
echo '#!/bin/bash
echo "=== STT功能快速验证 ==="
echo "1. 检查设备绑定状态..."

curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 00:11:22:33:44:55" \
  -H "Client-Id: android-app" \
  -d "{\"mac_address\":\"00:11:22:33:44:55\",\"application\":{\"version\":\"1.0.0\"},\"board\":{\"type\":\"android\"},\"chip_model_name\":\"android\"}" \
  http://47.122.144.73:8002/xiaozhi/ota/ | python3 -m json.tool

echo ""
echo "2. 如果看到activation字段，请到管理面板绑定设备"
echo "3. 如果只看到websocket字段，说明已绑定，可以测试STT"
echo "4. 记得清除应用数据后重新运行！"
' > quick_stt_test.sh

chmod +x quick_stt_test.sh
./quick_stt_test.sh
```

---
**关键提醒**：修改代码后务必清除应用数据，这是最容易忽略但最重要的步骤！ 