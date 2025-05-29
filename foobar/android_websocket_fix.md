# Android WebSocket修复方案

## 🎯 问题根因
经过测试发现，Android客户端的Hello握手消息**缺少服务器要求的认证字段**：
- ❌ Android发送: `{"type":"hello","version":1,"transport":"websocket","audio_params":{...}}`
- ✅ 服务器期望: `{"type":"hello","device_id":"xxx","device_mac":"xxx","token":"xxx"}`

## 🔧 修复方案

### Step 1: 修复WebsocketProtocol.kt中的Hello消息

**文件**: `xiaozhi-android/app/src/main/java/info/dourok/voicebot/protocol/WebsocketProtocol.kt`

**修改onOpen方法中的Hello消息**:

```kotlin
override fun onOpen(webSocket: WebSocket, response: Response) {
    isOpen = true
    Log.i(TAG, "WebSocket connected")
    scope.launch {
        audioChannelStateFlow.emit(AudioState.OPENED)
    }

    // 发送正确格式的Hello消息 - 修复STT问题的关键
    val helloMessage = JSONObject().apply {
        put("type", "hello")
        put("device_id", deviceInfo.uuid) // 添加设备ID
        put("device_name", "Android VoiceBot") // 添加设备名称
        put("device_mac", deviceInfo.mac_address) // 添加MAC地址
        put("token", accessToken) // 添加访问令牌
        
        // 保留原有的版本和音频参数（可选）
        put("version", 1)
        put("transport", "websocket")
        put("audio_params", JSONObject().apply {
            put("format", "opus")
            put("sample_rate", 16000)
            put("channels", 1)
            put("frame_duration", OPUS_FRAME_DURATION_MS)
        })
    }
    Log.i(TAG, "WebSocket hello with auth: $helloMessage")
    webSocket.send(helloMessage.toString())
}
```

### Step 2: 增强日志输出用于调试

**在onMessage方法中添加详细STT调试**:

```kotlin
override fun onMessage(webSocket: WebSocket, text: String) {
    Log.i(TAG, "=== 📨 收到服务器消息 ===")
    Log.i(TAG, "原始消息: $text")
    Log.i(TAG, "消息长度: ${text.length}")
    Log.i(TAG, "时间戳: ${System.currentTimeMillis()}")
    
    scope.launch {
        try {
            val json = JSONObject(text)
            val type = json.optString("type", "")
            Log.i(TAG, "消息类型: $type")
            
            // 专门检查STT相关字段
            val sttFields = listOf("stt", "text", "transcript", "result", "recognition")
            sttFields.forEach { field ->
                if (json.has(field)) {
                    Log.i(TAG, "🎯 STT字段: $field = ${json.get(field)}")
                }
            }
            
            when (type) {
                "hello" -> {
                    Log.i(TAG, "✅ Hello握手响应")
                    if (json.has("session_id")) {
                        Log.i(TAG, "🆔 Session ID: ${json.optString("session_id")}")
                    }
                    parseServerHello(json)
                }
                "stt" -> {
                    Log.i(TAG, "🎉 *** 收到STT识别结果! ***")
                    Log.i(TAG, "STT文本: ${json.optString("text")}")
                    incomingJsonFlow.emit(json)
                }
                "error" -> {
                    Log.e(TAG, "❌ 服务器错误: ${json.toString()}")
                    incomingJsonFlow.emit(json)
                }
                "" -> {
                    Log.w(TAG, "⚠️ 无类型消息: $text")
                    // 可能是裸STT响应，检查是否包含文本
                    if (text.contains("text") || text.contains("识别")) {
                        Log.i(TAG, "🔍 可能的STT响应: $text")
                    }
                    incomingJsonFlow.emit(json)
                }
                else -> {
                    Log.i(TAG, "📝 其他消息类型: $type")
                    incomingJsonFlow.emit(json)
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ JSON解析失败", e)
            Log.e(TAG, "问题消息: $text")
            
            // 即使JSON解析失败，也尝试检查是否包含STT内容
            if (text.contains("识别") || text.contains("听到")) {
                Log.w(TAG, "🔍 可能的非JSON格式STT响应: $text")
            }
        }
    }
}
```

### Step 3: 修复Listen Start消息格式

**确保Listen消息使用正确的session_id**:

```kotlin
// 在sendStartListening方法中
override suspend fun sendStartListening() {
    Log.i(TAG, "📞 发送开始监听命令")
    
    if (sessionId.isNullOrEmpty()) {
        Log.e(TAG, "❌ 无Session ID，无法发送Listen命令")
        return
    }
    
    val listenMessage = JSONObject().apply {
        put("session_id", sessionId)
        put("type", "listen")
        put("state", "start")
        put("mode", "auto")
    }
    
    Log.i(TAG, "📤 Listen Start: $listenMessage")
    sendText(listenMessage.toString())
}
```

### Step 4: 增强音频发送日志

**在sendAudio方法中添加调试信息**:

```kotlin
override suspend fun sendAudio(data: ByteArray) {
    frameCount++
    
    // 每50帧记录一次，避免日志过多
    if (frameCount % 50 == 0) {
        Log.d(TAG, "📤 发送第${frameCount}帧音频，大小: ${data.size}字节")
        Log.d(TAG, "🎙️ 音频帧特征: ${if (data.size < 30) "静音帧" else "语音帧"}")
    }
    
    websocket?.run {
        send(ByteString.of(*data))
    } ?: Log.e(TAG, "❌ WebSocket连接丢失，无法发送音频")
}
```

## 🧪 测试验证

### 预期修复后的日志流程:

```
✅ WebSocket连接成功
📤 发送Hello消息 (包含device_id, device_mac, token)
✅ 收到Hello握手响应，Session ID: xxx-xxx-xxx
📤 发送Listen Start命令
📤 开始发送音频帧...
🎉 *** 收到STT识别结果! ***
STT文本: 你好小智
📱 UI显示: >> 你好小智
```

### 关键验证点:

1. **Hello握手**: 确认收到session_id
2. **音频传输**: 确认音频帧正常发送到服务器  
3. **STT响应**: 确认收到类型为"stt"的消息
4. **UI更新**: 确认识别文本显示在界面上

## 🚀 立即行动

1. **修改Hello消息格式** - 添加认证字段
2. **增强日志输出** - 便于诊断STT问题
3. **测试完整流程** - 验证STT功能恢复
4. **监控服务器响应** - 确认协议对接正确

这个修复方案针对核心问题：**服务器端认证失败导致STT功能无法使用**。修复后Android应用应该能够正常接收STT识别结果。 