# 📱 Android端STT修复：与ESP32保持一致

## 🔍 **问题分析**

### ESP32端STT方案（正确的）
- **位置**：`../xiaozhi/main/xiaozhi-server/core/providers/asr/`
- **模型**：FunASR（本地或服务器）
- **处理方式**：服务器端STT
- **工作流程**：
  1. 设备发送Opus音频 → 服务器
  2. 服务器使用FunASR进行STT → 生成文本
  3. 服务器返回：`{"type": "stt", "text": "识别结果", "session_id": "xxx"}`

### Android端问题（不一致）
- **当前状态**：只发送音频，但STT响应处理不完整
- **问题1**：缺少STT响应的正确解析
- **问题2**：ChatViewModel中STT结果显示逻辑缺失
- **问题3**：没有正确处理服务器返回的STT消息

## 🎯 **修复方案**

### 1. 完善WebSocket协议STT响应处理
```kotlin
// 在WebsocketProtocol.kt中增强STT响应处理
when (type) {
    "stt" -> {
        Log.i(TAG, "🎯 收到STT结果: ${json.optString("text")}")
        // 发送到UI更新流程
        incomingJsonFlow.emit(json)
    }
}
```

### 2. 修复ChatViewModel中STT处理
```kotlin
// 在observeProtocolMessages()中添加STT处理
"stt" -> {
    val text = json.optString("text")
    if (text.isNotEmpty()) {
        Log.i(TAG, ">> STT识别: $text")
        schedule {
            display.setChatMessage("user", text)
        }
    }
}
```

### 3. 确保音频流程完整
- ✅ 音频录制：AndroidRecorder
- ✅ Opus编码：OpusEncoder  
- ✅ WebSocket传输：sendAudio()
- ❌ **STT响应处理**：需要修复
- ❌ **UI更新**：需要完善

## 🔧 **具体修复步骤**

### 步骤1：修复WebSocket STT响应解析
### 步骤2：完善ChatViewModel STT处理逻辑  
### 步骤3：确保UI正确显示STT结果
### 步骤4：测试完整STT流程

## 📊 **预期效果**

修复后的Android端STT流程：
```
用户说话 → 录音 → Opus编码 → WebSocket发送 
         ↓
服务器FunASR识别 → 返回STT结果 → Android接收 → UI显示
```

这样Android端就与ESP32端使用相同的服务器端STT方案，确保产品一致性。 