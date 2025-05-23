# STT问题深度分析报告

## 📊 当前状态评估

基于您提供的日志分析，协议迁移已经**基本成功**，但STT功能存在问题。

### ✅ 正常工作的部分

1. **WebSocket连接** ✅
   - Hello握手成功完成
   - Session ID正确获取: `103cb587-0d78-496f-b545-a2a2760cd3a3`
   - 服务器正确响应连接请求

2. **音频录制和编码** ✅  
   - OpusEncoder工作正常
   - AudioRecorder持续捕获音频
   - 音频帧大小变化正常(静音时小帧，说话时大帧)

3. **音频传输** ✅
   - 成功发送了数百个音频帧
   - 二进制数据通过WebSocket正常传输
   - 无传输错误或连接中断

4. **协议层** ✅
   - 监听状态正确设置: `{"type":"listen","state":"start","mode":"auto"}`
   - 所有控制消息格式正确

### ❌ 问题所在：STT响应缺失

**核心问题**: 服务器接收音频但未返回STT结果

## 🔍 问题定位分析

### 可能原因 1: 服务器STT处理问题

**症状**:
- 音频成功发送到服务器
- 没有收到任何 `{"type":"stt"}` 响应
- 没有看到 `ChatViewModel: >> XXX` 用户语音显示

**可能的服务器端问题**:
1. **STT服务未启动**或配置错误
2. **音频格式不兼容**：服务器期望不同的Opus参数
3. **音频质量问题**：录音质量不足以进行识别
4. **认证问题**：使用的"test-token"可能无效

### 可能原因 2: 音频参数不匹配

**客户端参数**:
```json
{
  "format": "opus",
  "sample_rate": 16000,
  "channels": 1,
  "frame_duration": 60  // 60ms帧
}
```

**可能的服务器期望**:
- 不同的帧长度(20ms而非60ms)
- 不同的采样率
- 特定的Opus编码参数

### 可能原因 3: 客户端响应处理问题

服务器可能返回了STT结果，但：
1. **消息格式不匹配**：实际格式与期望不符
2. **JSON解析失败**：响应格式有问题
3. **消息类型错误**：不是"stt"类型而是其他类型

## 🔧 诊断步骤

### 第一步：服务器端验证

**检查服务器是否接收到音频**:
```bash
# 运行STT诊断脚本
./foobar/stt_diagnosis.sh
```

**关键监控点**:
- 是否有任何服务器响应消息
- 是否有错误或超时消息
- 音频帧发送是否稳定

### 第二步：音频质量检查

**音频帧大小分析**:
从日志看，音频帧大小变化正常：
- 静音时：60-150 bytes (正常)
- 说话时：400-600 bytes (正常)
- 表明音频录制和编码工作正常

### 第三步：服务器兼容性测试

**尝试不同的音频参数**:

如果需要，可以修改 `WebsocketProtocol.kt` 中的参数：

```kotlin
// 当前设置 (line 108-113)
put("audio_params", JSONObject().apply {
    put("format", "opus")
    put("sample_rate", 16000)
    put("channels", 1)
    put("frame_duration", 60)  // 尝试改为20
})
```

## 🛠️ 立即可行的修复方案

### 方案 1: 增强日志输出

修改 `WebsocketProtocol.kt` 增加详细日志：

```kotlin
// 在 onMessage 方法中添加
override fun onMessage(webSocket: WebSocket, text: String) {
    Log.i(TAG, "Received text message: $text")
    Log.d(TAG, "Message length: ${text.length}")
    Log.d(TAG, "Raw message content: ${text.take(200)}...")  // 前200字符
    
    // ... 现有处理逻辑
}
```

### 方案 2: 音频参数调整

尝试将帧长度改为20ms：

```kotlin
private const val OPUS_FRAME_DURATION_MS = 20  // 改为20ms
```

### 方案 3: 服务器连接测试

**使用WebSocket测试工具验证服务器**:

```javascript
// 浏览器控制台测试
const ws = new WebSocket('ws://47.122.144.73:8000/xiaozhi/v1/');
ws.onopen = () => {
    console.log('连接成功');
    ws.send('{"type":"hello","transport":"websocket"}');
};
ws.onmessage = (e) => console.log('收到:', e.data);
```

## 📋 检查清单

### 必须确认的问题

- [ ] 服务器STT服务是否正常运行？
- [ ] 服务器是否支持60ms的Opus帧？
- [ ] "test-token"认证是否有效？
- [ ] 服务器日志中是否有音频处理错误？

### 客户端检查

- [x] WebSocket连接 ✅
- [x] 音频录制 ✅  
- [x] Opus编码 ✅
- [x] 音频传输 ✅
- [ ] 服务器响应处理 ❓
- [ ] STT结果显示 ❌

## 🚀 下一步行动

1. **运行STT诊断脚本**: `./foobar/stt_diagnosis.sh`
2. **检查服务器日志**: 确认STT服务状态  
3. **测试音频参数**: 尝试20ms帧长度
4. **验证认证**: 确认token有效性
5. **增强客户端日志**: 捕获所有服务器响应

## 💡 快速测试建议

**测试1**: 说清晰的简单词语（如"你好"）
**测试2**: 增加音量，确保音频质量
**测试3**: 检查网络连接稳定性
**测试4**: 尝试重启服务器端STT服务

**结论**: 协议迁移成功，问题集中在STT处理环节。需要重点检查服务器端配置和音频参数匹配。 