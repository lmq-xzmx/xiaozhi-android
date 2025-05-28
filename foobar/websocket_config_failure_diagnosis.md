# 🔍 WebSocket配置失败诊断报告

## 📋 问题描述
新APK出现WebSocket配置失败，需要诊断具体原因并提供解决方案。

## 🎯 可能的失败原因分析

### 1. **OTA配置阶段失败** ❌

#### 1.1 OTA请求失败
```kotlin
// 在ActivationManager.kt中
suspend fun checkActivationStatus(): ActivationResult {
    repeat(MAX_RETRY_ATTEMPTS) { attempt ->
        try {
            val success = ota.checkVersion(OTA_URL)
            if (!success) {
                throw Exception("OTA检查失败") // ❌ 可能的失败点
            }
        } catch (e: Exception) {
            Log.w(TAG, "OTA检查失败 (尝试 ${attempt + 1}): ${e.message}")
        }
    }
    // 所有重试都失败
    return ActivationResult.NetworkError("网络连接失败")
}
```

**可能原因：**
- 网络连接问题
- OTA服务器不可达 (`http://47.122.144.73:8002/xiaozhi/ota/`)
- 请求格式不匹配
- 服务器返回500错误

#### 1.2 OTA响应解析失败
```kotlin
// 在Ota.kt中
private suspend fun parseJsonResponse(json: JSONObject) {
    val otaResult = fromJsonToOtaResult(json)
    
    when {
        otaResult.isActivated -> {
            val websocketUrl = otaResult.websocketUrl!! // ❌ 可能为null
            // 保存WebSocket配置
            settingsRepository.webSocketUrl = websocketUrl
        }
    }
}
```

**可能原因：**
- 服务器返回的JSON格式异常
- `websocket`字段缺失或为空
- JSON解析异常

### 2. **WebSocket连接阶段失败** ❌

#### 2.1 WebSocket URL无效
```kotlin
// 在ChatViewModel.kt中
private suspend fun proceedWithActivatedDevice(websocketUrl: String) {
    // 步骤4: 初始化WebSocket协议
    protocol = WebsocketProtocol(deviceInfo!!, websocketUrl, accessToken)
    
    // 步骤5: 启动协议
    protocol?.start() // ❌ 可能失败
}
```

**可能原因：**
- WebSocket URL格式错误
- 服务器地址不可达
- 端口被防火墙阻止

#### 2.2 WebSocket握手失败
```kotlin
// 在WebsocketProtocol.kt中
override suspend fun openAudioChannel(): Boolean {
    try {
        val success = withTimeout(10000) {
            helloReceived.await() // ❌ 可能超时
        }
        return success
    } catch (e: TimeoutCancellationException) {
        Log.e(TAG, "Timeout waiting for server hello")
        return false
    }
}
```

**可能原因：**
- 服务器hello响应超时
- 认证失败
- 协议版本不匹配

### 3. **配置保存失败** ❌

#### 3.1 SettingsRepository同步失败
```kotlin
// 在Ota.kt中
// 同步到SettingsRepository
settingsRepository.webSocketUrl = websocketUrl // ❌ 可能失败
settingsRepository.transportType = TransportType.WebSockets
```

**可能原因：**
- SharedPreferences写入失败
- 权限问题
- 存储空间不足

## 🔧 诊断步骤

### 第一步：检查OTA配置
```bash
# 测试OTA端点可达性
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: test-device-id" \
  -H "Client-Id: test-client-id" \
  -d '{"application":{"version":"1.0.0"},"macAddress":"test-device-id","board":{"type":"android"}}' \
  "http://47.122.144.73:8002/xiaozhi/ota/"
```

**预期结果：**
- 返回包含`websocket`字段的JSON
- 或返回包含`activation`字段的JSON

### 第二步：检查WebSocket连接
```bash
# 测试WebSocket端点
curl -I "http://47.122.144.73:8000/xiaozhi/v1/"
```

**预期结果：**
- HTTP 200或101状态码
- 支持WebSocket升级

### 第三步：检查应用日志
```bash
# 查找关键错误日志
adb logcat | grep -E "(WebSocket|OTA|ActivationManager|ChatViewModel)"
```

**关键日志标识：**
- `❌ OTA检查失败`
- `❌ WebSocket connection failed`
- `❌ Timeout waiting for server hello`
- `❌ 激活后初始化失败`

## 🚨 常见失败模式

### 模式1：OTA网络失败
```
ActivationManager: OTA检查失败 (尝试 1): java.net.ConnectException
ActivationManager: 网络连接失败
ChatViewModel: 初始化失败: 网络连接失败
```

**解决方案：**
1. 检查网络连接
2. 确认服务器地址正确
3. 检查防火墙设置

### 模式2：WebSocket握手超时
```
WebsocketProtocol: WebSocket connected successfully
WebsocketProtocol: Sending hello message
WebsocketProtocol: Timeout waiting for server hello
ChatViewModel: 激活后初始化失败: WebSocket握手失败
```

**解决方案：**
1. 检查服务器WebSocket服务状态
2. 验证hello消息格式
3. 检查认证参数

### 模式3：配置保存失败
```
Ota: 设备已激活，WebSocket URL: ws://47.122.144.73:8000/xiaozhi/v1/
Ota: WebSocket配置已保存到SettingsRepository
ChatViewModel: 步骤4: 初始化WebSocket协议
WebsocketProtocol: Opening audio channel to null
```

**解决方案：**
1. 检查SettingsRepository实现
2. 验证配置读取逻辑
3. 清除应用数据重新配置

## 🔍 具体诊断代码

### 诊断脚本1：OTA配置检查
```kotlin
// 在ActivationManager中添加详细日志
suspend fun checkActivationStatus(): ActivationResult {
    Log.i(TAG, "🔍 开始OTA诊断...")
    Log.i(TAG, "OTA URL: $OTA_URL")
    
    try {
        val success = ota.checkVersion(OTA_URL)
        Log.i(TAG, "OTA请求结果: $success")
        
        val otaResult = ota.otaResult
        Log.i(TAG, "OTA结果: $otaResult")
        
        if (otaResult?.websocketUrl != null) {
            Log.i(TAG, "✅ 获得WebSocket URL: ${otaResult.websocketUrl}")
        } else {
            Log.e(TAG, "❌ WebSocket URL为空")
        }
        
        return handleOtaResult(otaResult)
    } catch (e: Exception) {
        Log.e(TAG, "❌ OTA诊断失败", e)
        return ActivationResult.NetworkError(e.message ?: "未知错误")
    }
}
```

### 诊断脚本2：WebSocket连接检查
```kotlin
// 在WebsocketProtocol中添加详细日志
override suspend fun openAudioChannel(): Boolean {
    Log.i(TAG, "🔍 开始WebSocket连接诊断...")
    Log.i(TAG, "目标URL: $url")
    Log.i(TAG, "设备ID: ${deviceInfo.mac_address}")
    Log.i(TAG, "访问令牌: $accessToken")
    
    try {
        // 创建连接
        websocket = client.newWebSocket(request, webSocketListener)
        
        // 等待握手
        val success = withTimeout(10000) {
            Log.i(TAG, "⏳ 等待服务器hello响应...")
            helloReceived.await()
        }
        
        if (success) {
            Log.i(TAG, "✅ WebSocket握手成功")
        } else {
            Log.e(TAG, "❌ WebSocket握手失败")
        }
        
        return success
    } catch (e: TimeoutCancellationException) {
        Log.e(TAG, "❌ WebSocket握手超时")
        return false
    } catch (e: Exception) {
        Log.e(TAG, "❌ WebSocket连接异常", e)
        return false
    }
}
```

### 诊断脚本3：配置状态检查
```kotlin
// 在ChatViewModel中添加配置验证
private suspend fun proceedWithActivatedDevice(websocketUrl: String) {
    Log.i(TAG, "🔍 开始设备初始化诊断...")
    Log.i(TAG, "输入WebSocket URL: $websocketUrl")
    
    // 验证URL格式
    if (websocketUrl.isBlank()) {
        throw Exception("WebSocket URL为空")
    }
    
    if (!websocketUrl.startsWith("ws://") && !websocketUrl.startsWith("wss://")) {
        throw Exception("WebSocket URL格式错误: $websocketUrl")
    }
    
    // 验证设备信息
    if (deviceInfo == null) {
        throw Exception("设备信息未初始化")
    }
    
    Log.i(TAG, "✅ 配置验证通过，继续初始化...")
    
    // 继续原有逻辑...
}
```

## 🎯 快速修复建议

### 立即检查项
1. **网络连接**: 确认设备可以访问`47.122.144.73:8002`和`47.122.144.73:8000`
2. **服务器状态**: 确认OTA和WebSocket服务正常运行
3. **应用权限**: 确认网络权限已授予
4. **配置清理**: 清除应用数据，重新进行设备绑定

### 临时解决方案
```kotlin
// 在ActivationManager中添加重试逻辑
private const val MAX_RETRY_ATTEMPTS = 5 // 增加重试次数
private const val RETRY_DELAY_MS = 3000L // 增加重试间隔
```

### 长期解决方案
1. **增强错误处理**: 提供更详细的错误信息
2. **添加离线模式**: 支持手动配置WebSocket URL
3. **改进重试机制**: 指数退避重试策略
4. **增加诊断工具**: 内置连接测试功能

## 📊 诊断检查清单

- [ ] OTA服务器可达性
- [ ] OTA请求格式正确性
- [ ] OTA响应JSON格式
- [ ] WebSocket服务器可达性
- [ ] WebSocket握手成功
- [ ] 配置保存成功
- [ ] 设备信息完整性
- [ ] 网络权限授予
- [ ] 应用日志检查

**建议优先检查OTA阶段，因为这是WebSocket URL获取的源头！** 