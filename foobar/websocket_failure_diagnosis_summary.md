# 🚨 WebSocket配置失败诊断总结

## 📋 问题现象
新APK出现WebSocket配置失败，导致应用无法正常工作。

## 🔍 根据代码分析的可能原因

### 1. **最可能的原因：OTA配置阶段失败** ⭐⭐⭐⭐⭐

#### 1.1 网络连接问题
```kotlin
// ActivationManager.kt:68
_activationState.value = ActivationState.Error("网络连接失败")
return ActivationResult.NetworkError(lastException?.message ?: "未知网络错误")
```

**症状：**
- 应用显示"网络连接失败"
- 无法获取激活码或WebSocket URL
- 初始化状态停留在"检查激活状态"

**可能原因：**
- 设备无法访问 `http://47.122.144.73:8002/xiaozhi/ota/`
- 网络权限未授予
- 防火墙阻止连接

#### 1.2 OTA服务器响应异常
```kotlin
// Ota.kt:280-290
if (response.isSuccessful && responseBody.isNotEmpty()) {
    val json = JSONObject(responseBody)
    if (json.has("code") && json.has("msg")) {
        val code = json.getInt("code")
        if (code == 0) {
            // API成功，检查data字段
        } else {
            Log.w(TAG, "API返回错误: code=$code, msg=$msg")
            return false
        }
    }
}
```

**症状：**
- OTA请求发送成功但返回错误码
- 服务器返回500内部错误
- JSON格式异常

### 2. **次要原因：WebSocket握手失败** ⭐⭐⭐

#### 2.1 服务器Hello超时
```kotlin
// WebsocketProtocol.kt:245-255
try {
    val success = withTimeout(10000) {
        helloReceived.await() // ❌ 可能超时
    }
} catch (e: TimeoutCancellationException) {
    Log.e(TAG, "Timeout waiting for server hello")
    return false
}
```

**症状：**
- WebSocket连接建立成功
- 发送Hello消息后无响应
- 10秒后超时失败

#### 2.2 认证参数问题
```kotlin
// WebsocketProtocol.kt:75-85
val request = Request.Builder()
    .url(url)
    .addHeader("Authorization", "Bearer $accessToken")
    .addHeader("Device-Id", deviceInfo.mac_address)
    .addHeader("Client-Id", deviceInfo.uuid)
    .build()
```

**症状：**
- 认证失败
- 设备ID格式错误
- 访问令牌无效

### 3. **配置同步问题** ⭐⭐

#### 3.1 SettingsRepository写入失败
```kotlin
// Ota.kt:399-405
// 同步到SettingsRepository
settingsRepository.webSocketUrl = websocketUrl
settingsRepository.transportType = TransportType.WebSockets
```

**症状：**
- OTA获取WebSocket URL成功
- 但应用读取到的URL为空
- 配置未正确保存

## 🎯 诊断优先级

### 第一优先级：检查OTA配置 🔥
```bash
# 测试命令（需要在能访问网络的环境中执行）
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: test-android-device" \
  -H "Client-Id: test-client-$(date +%s)" \
  -d '{"application":{"version":"1.0.0"},"macAddress":"test-android-device","board":{"type":"android"}}' \
  "http://47.122.144.73:8002/xiaozhi/ota/"
```

**预期结果：**
- 返回包含`websocket`字段的JSON（已绑定设备）
- 或返回包含`activation`字段的JSON（需要绑定）

### 第二优先级：检查应用日志 📱
```bash
# 关键日志过滤
adb logcat | grep -E "(ActivationManager|Ota|WebsocketProtocol|ChatViewModel)"
```

**关键错误标识：**
- `❌ OTA检查失败`
- `❌ 网络连接失败`
- `❌ WebSocket connection failed`
- `❌ Timeout waiting for server hello`

### 第三优先级：检查WebSocket服务 🌐
```bash
# 测试WebSocket端点
curl -I "http://47.122.144.73:8000/xiaozhi/v1/"
```

## 🔧 具体修复步骤

### 步骤1：确认网络连接
```bash
# 测试基础连接
ping 47.122.144.73

# 测试端口可达性
telnet 47.122.144.73 8002
telnet 47.122.144.73 8000
```

### 步骤2：清除应用数据
```bash
# Android设备上
adb shell pm clear info.dourok.voicebot
```

### 步骤3：重新配置设备
1. 打开应用
2. 等待OTA检查完成
3. 如果显示激活码，访问管理面板完成绑定
4. 重新启动应用

### 步骤4：检查服务器状态
1. 确认OTA服务运行正常
2. 确认WebSocket服务运行正常
3. 检查服务器日志

## 🚨 紧急修复方案

### 方案1：增加详细日志
在`ActivationManager.kt`中添加：
```kotlin
suspend fun checkActivationStatus(): ActivationResult {
    Log.i(TAG, "🔍 开始详细OTA诊断...")
    Log.i(TAG, "OTA URL: $OTA_URL")
    Log.i(TAG, "设备ID: ${deviceConfigManager.getDeviceId()}")
    
    // 原有逻辑...
}
```

### 方案2：增加重试次数
```kotlin
companion object {
    private const val MAX_RETRY_ATTEMPTS = 5 // 从3增加到5
    private const val RETRY_DELAY_MS = 3000L // 从2秒增加到3秒
}
```

### 方案3：添加手动配置选项
在设置界面添加手动输入WebSocket URL的选项，绕过OTA配置。

## 📊 问题概率评估

| 问题类型 | 概率 | 影响 | 修复难度 |
|---------|------|------|----------|
| OTA网络连接失败 | 70% | 高 | 低 |
| 服务器配置问题 | 20% | 高 | 中 |
| WebSocket握手失败 | 8% | 中 | 中 |
| 应用内部逻辑错误 | 2% | 低 | 高 |

## 🎯 建议立即执行的操作

1. **检查网络连接**：确认设备可以访问服务器
2. **查看应用日志**：使用adb logcat查看详细错误信息
3. **清除应用数据**：重新进行设备配置
4. **检查服务器状态**：确认OTA和WebSocket服务正常

**最重要的是先确认OTA服务器的可达性，因为这是WebSocket URL获取的源头！** 