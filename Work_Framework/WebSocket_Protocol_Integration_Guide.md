# WebSocket协议对接完整指导

## 🎯 问题明确

**现状**: WebSocket服务器 `ws://47.122.144.73:8000/xiaozhi/v1/` 正常运行  
**目标**: Android客户端正确对接到远程服务器，实现完整STT功能  
**关键**: 确保协议流程的每个环节都正确执行

## 📋 标准协议流程

### 1. WebSocket连接阶段
```
Android客户端 → 服务器
- URL: ws://47.122.144.73:8000/xiaozhi/v1/
- Headers: Authorization, Protocol-Version, Device-Id, Client-Id
```

### 2. Hello握手阶段  
```json
// Android发送
{
  "type": "hello",
  "version": 1, 
  "transport": "websocket",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1, 
    "frame_duration": 60
  }
}

// 服务器响应
{
  "type": "hello",
  "session_id": "xxx-xxx-xxx",
  "transport": "websocket",
  "version": 1,
  "audio_params": {...}
}
```

### 3. Listen Start阶段
```json
// Android发送
{
  "session_id": "xxx-xxx-xxx",
  "type": "listen",
  "state": "start", 
  "mode": "auto"
}

// 服务器处理: conn.client_have_voice = True
```

### 4. 音频传输阶段
- Android: 发送Opus编码音频帧(60ms/帧)
- 服务器: VAD检测 → ASR识别

### 5. STT响应阶段
```json
// 服务器返回
{
  "type": "stt",
  "text": "识别的文本内容",
  "session_id": "xxx-xxx-xxx"
}
```

## 🔧 关键修复点

### 1. Android客户端日志增强

在 `WebsocketProtocol.kt` 的 `onMessage` 方法中：

```kotlin
override fun onMessage(webSocket: WebSocket, text: String) {
    Log.i(TAG, "=== 收到服务器消息 ===")
    Log.i(TAG, "原始消息: $text")
    
    scope.launch {
        try {
            val json = JSONObject(text)
            val type = json.optString("type")
            Log.i(TAG, "消息类型: $type")
            
            when (type) {
                "hello" -> {
                    Log.i(TAG, "✅ Hello握手响应")
                    Log.i(TAG, "Session ID: ${json.optString("session_id")}")
                    parseServerHello(json)
                }
                "stt" -> {
                    Log.i(TAG, "🎉 *** STT识别响应! ***")
                    Log.i(TAG, "识别文本: ${json.optString("text")}")
                    incomingJsonFlow.emit(json)
                }
                "listen_ack" -> {
                    Log.i(TAG, "🎧 Listen Start确认")
                    incomingJsonFlow.emit(json)
                }
                else -> {
                    Log.i(TAG, "其他消息: $type")
                    incomingJsonFlow.emit(json)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ 消息解析失败", e)
        }
    }
}
```

### 2. 服务器端Listen确认

在xiaozhi-server的 `textHandle.py` 中添加：

```python
elif msg_json["type"] == "listen":
    if msg_json["state"] == "start":
        conn.client_have_voice = True
        conn.client_voice_stop = False
        
        # 添加确认响应
        await conn.websocket.send(json.dumps({
            "type": "listen_ack",
            "state": "ready",
            "session_id": conn.session_id,
            "timestamp": time.time()
        }))
        logger.bind(tag=TAG).info(f"已确认客户端监听开始")
```

### 3. 音频传输日志

Android客户端音频发送增强：

```kotlin
override suspend fun sendAudio(data: ByteArray) {
    if (frameCount % 50 == 0) { // 每50帧记录一次
        Log.d(TAG, "📤 发送第${frameCount}帧音频，大小: ${data.size}字节")
    }
    frameCount++
    
    websocket?.run {
        send(ByteString.of(*data))
    } ?: Log.e(TAG, "❌ WebSocket连接丢失")
}
```

## 🧪 验证步骤

### Step 1: 基础连接测试
```bash
# 测试HTTP端点
curl -I http://47.122.144.73:8000/xiaozhi/v1/

# 预期: 收到HTTP响应，确认服务器可达
```

### Step 2: Android应用测试
1. **启动应用** - 观察连接建立日志
2. **Hello握手** - 确认收到session_id
3. **开始录音** - 观察Listen Start和音频发送
4. **结束录音** - 等待STT响应

### Step 3: 日志监控
同时观察Android客户端和服务器端日志：

```bash
# 服务器端日志 (如果可以访问)
tail -f /path/to/xiaozhi-server/tmp/server.log | grep -E "(Hello|STT|listen|音频)"
```

## 📊 问题诊断清单

| 环节 | 检查点 | 正常表现 |
|------|--------|----------|
| 连接 | WebSocket连接 | ✅ 连接成功，收到欢迎消息 |
| 握手 | Hello往返 | ✅ 收到session_id |
| 监听 | Listen Start | ✅ 收到listen_ack (可选) |
| 音频 | 音频流发送 | ✅ 持续发送音频帧 |
| 识别 | STT响应 | ✅ 收到STT消息和文本 |
| 显示 | UI更新 | ✅ 显示 `>> [识别内容]` |

## 🚀 立即行动计划

### 阶段1: 连接验证 (5分钟)
1. 在Android应用中启用详细日志
2. 测试WebSocket连接和Hello握手
3. 确认session_id获取成功

### 阶段2: 协议调试 (15分钟)  
1. 添加Listen Start确认机制
2. 增强音频传输日志
3. 验证STT响应格式

### 阶段3: 完整测试 (10分钟)
1. 端到端录音测试
2. 确认STT识别结果显示
3. 验证完整对话流程

## 🎯 预期结果

修复后应看到完整的日志流：

```
✅ WebSocket连接成功
✅ 收到服务器欢迎消息 
✅ Hello握手完成，Session ID: xxx
✅ Listen Start确认收到
📤 开始发送音频帧...
🎉 收到STT响应: "你好小智"
📱 UI显示: >> 你好小智
```

## 🔧 工具资源

创建的辅助工具：
1. `websocket_protocol_fix.md` - 详细修复方案
2. `websocket_connection_test.py` - 连接测试脚本  
3. `STT_Problem_Complete_Analysis.md` - 完整问题分析

按照这个指导，您的Android客户端应该能够成功对接到远程WebSocket服务器并实现完整的STT功能！ 