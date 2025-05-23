# MQTT vs WebSocket STT失效原因分析

## 🎯 核心问题

**现象**: MQTT协议下STT正常工作，切换到WebSocket后STT失效
**结论**: 问题不在STT服务本身，而在于两种协议的**具体实现差异**

## 📋 详细协议对比

### MQTT协议工作流程 (原先可用)

#### 1. 连接阶段
```kotlin
// MqttProtocol.kt - 连接流程
1. 连接MQTT Broker: tcp://${mqttConfig.endpoint}
2. 认证: username/password从OTA获取
3. 订阅主题: devices/A4_B1_C2_D3_E4_F5
4. 发布主题: device-server
```

#### 2. Hello握手
```kotlin
// MqttProtocol.kt line 131-142
val helloMessage = JSONObject().apply {
    put("type", "hello")
    put("version", 3)                    // 版本3
    put("transport", "udp")              // 关键：声明UDP传输
    put("audio_params", JSONObject().apply {
        put("format", "opus")
        put("sample_rate", 16000)
        put("channels", 1)
        put("frame_duration", 20)        // 20ms帧长度
    })
}
```

#### 3. 音频传输 - UDP + AES加密
```kotlin
// MqttProtocol.kt line 84-110
1. 服务器返回UDP配置: {server, port, AES key, nonce}
2. 建立UDP连接到专用音频服务器
3. 音频数据AES/CTR加密后通过UDP发送
4. 每个音频包包含: nonce + 加密的opus数据
```

### WebSocket协议工作流程 (当前不可用)

#### 1. 连接阶段
```kotlin
// WebsocketProtocol.kt - 连接流程
1. 直接连接WebSocket: ws://47.122.144.73:8000/xiaozhi/v1/
2. 简单认证: "test-token"
3. 单一连接用于控制和音频
```

#### 2. Hello握手
```kotlin
// WebsocketProtocol.kt line 104-113
val helloMessage = JSONObject().apply {
    put("type", "hello")
    put("version", 1)                    // 版本1 (不同!)
    put("transport", "websocket")        // 关键：声明WebSocket传输
    put("audio_params", JSONObject().apply {
        put("format", "opus")
        put("sample_rate", 16000)
        put("channels", 1)
        put("frame_duration", 60)        // 60ms帧长度 (不同!)
    })
}
```

#### 3. 音频传输 - 直接二进制帧
```kotlin
// WebsocketProtocol.kt line 35-38
override suspend fun sendAudio(data: ByteArray) {
    websocket?.run {
        send(ByteString.of(*data))       // 直接发送未加密的opus数据
    }
}
```

## 🚨 关键差异识别

### 差异1: 协议版本不匹配
- **MQTT**: `"version": 3`
- **WebSocket**: `"version": 1`
- **影响**: 服务器可能根据版本使用不同的处理逻辑

### 差异2: 音频帧长度不同
- **MQTT**: `"frame_duration": 20` (20ms)
- **WebSocket**: `"frame_duration": 60` (60ms) 
- **影响**: STT引擎可能只支持特定帧长度

### 差异3: 传输方式根本不同
- **MQTT**: UDP专用连接 + AES加密
- **WebSocket**: 同一连接的二进制帧
- **影响**: 服务器音频处理器可能期望特定的传输格式

### 差异4: 服务器端点可能不同
- **MQTT**: 专用UDP音频服务器 (从hello响应获取)
- **WebSocket**: 同一个WebSocket端点
- **影响**: WebSocket端点可能没有音频处理能力

## 🔧 问题根源分析

### 最可能的原因: 服务器端架构差异

从代码可以看出，MQTT和WebSocket是完全不同的服务器架构：

#### MQTT架构 (可工作)
```
客户端 → MQTT Broker → 服务器控制层
             ↓
客户端 → UDP音频服务器 → STT引擎
```

#### WebSocket架构 (不工作)  
```
客户端 → WebSocket服务器 → ???
```

**关键问题**: WebSocket服务器可能**没有集成STT处理能力**，或者STT处理模块期望的是UDP+加密的音频数据，而不是WebSocket二进制帧。

## 🛠️ 立即验证方案

### 方案1: 匹配MQTT的音频参数

修改WebSocket协议使用与MQTT相同的参数：

```kotlin
// WebsocketProtocol.kt 修改
private const val OPUS_FRAME_DURATION_MS = 20  // 改为20ms

// Hello消息修改
put("version", 3)                    // 改为版本3
put("frame_duration", 20)            // 改为20ms
```

### 方案2: 检查服务器能力

通过增强日志查看服务器是否返回任何STT相关响应：

```kotlin
// 在WebsocketProtocol.kt的onMessage中添加
override fun onMessage(webSocket: WebSocket, text: String) {
    Log.i(TAG, "=== 服务器完整响应 ===")
    Log.i(TAG, text)
    Log.i(TAG, "========================")
    
    // 现有处理逻辑...
}
```

### 方案3: 对比认证方式

MQTT使用完整的OTA获取认证，WebSocket使用简单token：

```kotlin
// 可能需要真实的认证token而不是"test-token"
WebsocketProtocol(deviceInfo, webSocketUrl, "real-auth-token")
```

## 📋 诊断优先级

### 🔴 高优先级 - 立即检查
1. **音频帧长度**: 改为20ms测试
2. **协议版本**: 改为version 3测试  
3. **服务器响应**: 确认是否收到任何非hello响应

### 🟡 中优先级 - 后续检查
1. **认证token**: 使用真实token
2. **音频编码参数**: 匹配MQTT的具体opus设置
3. **传输加密**: 是否需要某种加密

### 🟢 低优先级 - 确认检查
1. **网络路径**: WebSocket和UDP路径是否到达同一STT服务
2. **服务器配置**: WebSocket端点是否启用了STT功能

## 🎯 最可能的修复方案

基于分析，最可能的问题是**音频帧长度不匹配**。建议立即尝试：

```kotlin
// WebsocketProtocol.kt
private const val OPUS_FRAME_DURATION_MS = 20  // 20ms而不是60ms
```

同时修改hello消息:
```kotlin
put("frame_duration", 20)    // 匹配MQTT的20ms
put("version", 3)            // 匹配MQTT的版本3
```

## 💡 验证策略

1. **运行诊断脚本**: `./foobar/stt_diagnosis.sh`
2. **逐项测试**: 先改帧长度，再改版本，逐步匹配MQTT参数
3. **对比日志**: 观察服务器响应是否有变化

**结论**: 问题很可能是WebSocket实现没有完全匹配MQTT的音频参数和协议规范，导致服务器端STT模块无法正确处理音频数据。 