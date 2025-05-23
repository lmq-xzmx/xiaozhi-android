# 🎯 STT问题根本原因和完整解决方案

## 🔍 问题根源确认

通过对服务器配置文件的深入分析，我找到了STT失效的**确切原因**：

### 服务器配置不匹配

**服务器端配置** (`/xiaozhi/main/xiaozhi-server/config.yaml` 第69-75行):
```yaml
xiaozhi:
  type: hello
  version: 1                    # ❌ 服务器版本是1
  transport: websocket
  audio_params:
    format: opus
    sample_rate: 16000
    channels: 1
    frame_duration: 60          # ❌ 服务器期望60ms
```

**客户端配置** (当前我们的修改):
```kotlin
// WebsocketProtocol.kt
val helloMessage = JSONObject().apply {
    put("version", 3)           # ❌ 客户端发送版本3
    put("frame_duration", 20)   # ❌ 客户端发送20ms
}
```

**协议不匹配导致STT失效**：
- 服务器期望 `version: 1, frame_duration: 60`
- 客户端发送 `version: 3, frame_duration: 20`
- 服务器接受连接但**拒绝处理音频**，因为参数不匹配

## 🛠️ 完整解决方案

### 方案1: 修改客户端匹配服务器 (推荐)

修改Android客户端以匹配服务器的实际配置：

#### 1.1 修复WebsocketProtocol.kt
```kotlin
// 修改为匹配服务器配置
val helloMessage = JSONObject().apply {
    put("type", "hello")
    put("version", 1)           // ✅ 改为版本1匹配服务器
    put("transport", "websocket")
    put("audio_params", JSONObject().apply {
        put("format", "opus")
        put("sample_rate", 16000)
        put("channels", 1)
        put("frame_duration", 60)  // ✅ 改为60ms匹配服务器
    })
}
```

#### 1.2 修复ChatViewModel.kt音频参数
```kotlin
// 修改音频编码参数匹配服务器
val frameSizeMs = 60  // ✅ 改为60ms
```

#### 1.3 修复WebsocketProtocol.kt常量
```kotlin
companion object {
    private const val TAG = "WS"
    private const val OPUS_FRAME_DURATION_MS = 60  // ✅ 改为60ms
}
```

### 方案2: 修改服务器匹配客户端

如果您有服务器管理权限，可以修改服务器配置：

#### 2.1 修改config.yaml
```yaml
xiaozhi:
  type: hello
  version: 3                    # 改为版本3
  transport: websocket
  audio_params:
    format: opus
    sample_rate: 16000
    channels: 1
    frame_duration: 20          # 改为20ms
```

#### 2.2 同时需要修改相关的Python处理文件
- `core/handle/sendAudioHandle.py` 第69行
- `core/utils/p3.py` 第9行  
- `core/providers/tts/base.py` 第79行

### 方案3: MQTT模式回退 (临时方案)

如果需要立即恢复功能，可以暂时回退到MQTT模式：

```kotlin
// SettingsRepository.kt
override var transportType: TransportType = TransportType.MQTT  // 回退到MQTT

// FormRepository.kt  
// 确保有有效的MQTT配置
```

## 🚀 立即行动计划

### 推荐：执行方案1

我将为您修改客户端代码以匹配服务器配置：

1. **修改WebsocketProtocol.kt** - 版本改为1，帧长度改为60ms
2. **修改ChatViewModel.kt** - 音频参数改为60ms
3. **测试验证** - 运行测试脚本确认STT功能恢复

### 为什么MQTT能工作而WebSocket不能？

**MQTT模式下的实际参数**：
通过分析MqttProtocol.kt，我发现MQTT使用的是：
- `version: 3`  
- `frame_duration: 20`
- `transport: "udp"`

但是**MQTT走的是UDP协议**，可能使用了**完全不同的服务器端点或处理逻辑**。

**WebSocket模式必须严格匹配**服务器config.yaml中的xiaozhi配置块。

## 🔧 验证步骤

修改完成后，您应该看到：

1. **连接日志**：`version: 1, frame_duration: 60`
2. **服务器响应**：`{"type":"hello","version":1,"frame_duration":60}`  
3. **STT响应**：`{"type":"stt","text":"用户说话内容"}`

## 总结

问题的核心不是协议选择，而是**协议参数不匹配**。服务器的WebSocket端点期望特定的版本和音频参数，我们需要精确匹配这些参数才能激活STT功能。 