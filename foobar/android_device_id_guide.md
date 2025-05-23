# 📱 Android应用设备ID配置指南

## 🔍 当前问题分析

您的Android应用使用随机生成的MAC地址作为设备ID，每次运行都可能不同，这导致：
1. 设备无法在服务器端正确绑定
2. STT功能被阻断
3. 需要重复进行设备绑定

## 🎯 解决方案：固定设备ID

### 方案1：修改设备信息生成逻辑（推荐）

**文件位置**：`app/src/main/java/info/dourok/voicebot/data/model/DeviceInfo.kt`

在第155行的`generateMacAddress()`函数中，修改为返回固定的MAC地址：

```kotlin
private fun generateMacAddress(): String {
    // 原始代码（随机生成）：
    // return List(6) { Random.nextInt(0x00, 0xFF) }
    //     .joinToString(":") { String.format("%02x", it) }
    
    // 修改为固定MAC地址：
    return "00:11:22:33:44:55"  // 使用固定的设备ID
}
```

### 方案2：在SharedPreferences中持久化设备ID

**文件位置**：`app/src/main/java/info/dourok/voicebot/AppModule.kt`

修改第58-63行的逻辑：

```kotlin
// 原始代码
sp.getString("device_id", null)?.let {
    DeviceInfo = fromJsonToDeviceInfo(it)
} ?: run {
    DeviceInfo = DummyDataGenerator.generate()
    sp.edit { putString("device_id", deviceInfo.toJson()) }
}

// 修改为（确保MAC地址固定）
sp.getString("device_id", null)?.let {
    DeviceInfo = fromJsonToDeviceInfo(it)
} ?: run {
    DeviceInfo = DummyDataGenerator.generate().copy(
        mac_address = "00:11:22:33:44:55"  // 强制使用固定MAC地址
    )
    sp.edit { putString("device_id", deviceInfo.toJson()) }
}
```

## 🚀 完整操作流程

### 第1步：获取激活码

使用固定设备ID `00:11:22:33:44:55` 获取激活码：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 00:11:22:33:44:55" \
  -H "Client-Id: android-app" \
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

### 第2步：管理面板绑定

1. 访问：http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30
2. 输入获得的6位激活码
3. 完成设备绑定

### 第3步：修改Android代码

选择方案1或方案2修改设备ID生成逻辑

### 第4步：清除应用数据（重要）

```bash
# 清除应用的SharedPreferences数据
adb shell pm clear info.dourok.voicebot
```

或在设备上：设置 → 应用 → VoiceBot → 存储 → 清除数据

### 第5步：重新编译运行

1. 重新编译Android应用
2. 运行应用，验证设备ID为 `00:11:22:33:44:55`
3. 测试STT功能

## 🔧 验证设备ID

在应用中添加日志验证当前使用的设备ID：

```kotlin
// 在WebsocketProtocol.kt的第79行附近添加
Log.d("DeviceInfo", "Current Device-Id: ${deviceInfo.mac_address}")
```

## 📋 快速测试方法

### Python脚本验证

```python
import requests
import json

# 测试固定设备ID是否已绑定
device_id = "00:11:22:33:44:55"
response = requests.post(
    "http://47.122.144.73:8002/xiaozhi/ota/",
    headers={
        "Content-Type": "application/json",
        "Device-Id": device_id,
        "Client-Id": "android-app"
    },
    json={
        "mac_address": device_id,
        "application": {"version": "1.0.0"},
        "board": {"type": "android"},
        "chip_model_name": "android"
    }
)

result = response.json()
if "activation" in result:
    print(f"需要绑定，激活码：{result['activation']['code']}")
elif "websocket" in result:
    print("设备已绑定，可以使用STT功能")
else:
    print("意外响应：", result)
```

## 🎯 预期结果

完成所有步骤后：

✅ **设备ID固定**：应用每次启动都使用相同的设备ID  
✅ **设备已绑定**：服务器识别并允许STT功能  
✅ **STT功能正常**：语音识别开始正常工作  
✅ **问题彻底解决**：不再需要重复绑定设备  

## 🚨 重要提醒

1. **清除应用数据**：修改代码后必须清除应用数据，否则还会使用旧的随机设备ID
2. **设备ID唯一性**：每个设备应该使用不同的固定ID，避免冲突
3. **生产环境**：在生产环境中可以基于设备硬件信息生成固定ID

---
**关键：修改代码后务必清除应用数据，确保使用新的固定设备ID！** 