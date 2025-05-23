# 🚀 语音助手优化策略

## 📊 **诊断结果总结**

### ✅ **正常工作的组件**
- WebSocket连接：✅ 连接成功 (101 Response)
- 协议握手：✅ 服务器确认audio_params匹配
- 会话建立：✅ 获得有效session_id
- 客户端音频：✅ 录制、编码、发送正常

### ❌ **核心问题**
服务器收到监听请求后，无响应确认，STT服务未工作

## 🎯 **优化策略（按优先级）**

### **策略1：添加服务器响应监控** 🔍

增强日志监控，确认服务器是否响应监听请求：

```bash
# 监控所有服务器响应
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat | grep -E "(Received.*listen|Received.*ready|Received.*status)"
```

**期望看到的响应**：
```json
{"type":"listen","state":"ready","session_id":"..."}
```

### **策略2：服务器端配置验证** ⚙️

验证服务器STT服务状态：

```bash
# 测试服务器健康状态
curl -v http://47.122.144.73:8000/health
curl -v http://47.122.144.73:8000/xiaozhi/status
```

### **策略3：音频数据传输确认** 📤

修改WebsocketProtocol.kt，添加音频发送确认：

```kotlin
// 在sendAudio方法中添加
Log.d("WS", "Sending audio frame: ${data.size} bytes to session $sessionId")
websocket?.send(ByteString.of(*data))
Log.d("WS", "Audio frame sent successfully")
```

### **策略4：监听请求格式优化** 📝

尝试不同的监听请求格式：

```kotlin
// 在ChatViewModel.kt中修改监听请求
val listenRequest = JSONObject().apply {
    put("session_id", sessionId)
    put("type", "listen")
    put("state", "start")
    put("mode", "auto")
    put("language", "zh-CN")  // 添加语言参数
    put("sample_rate", 16000) // 明确指定采样率
}
```

### **策略5：分步测试策略** 🧪

#### **5.1 静音测试**
先测试不说话的情况，确认监听状态确认：
```bash
# 启动应用但不说话，观察是否收到监听确认
```

#### **5.2 简单音频测试**  
发送简单的测试音频：
```bash
# 说简单的词语如"你好"，观察STT响应
```

#### **5.3 不同服务器测试**
测试其他可用的STT服务：
```kotlin
// 尝试切换到其他STT服务URL
val alternativeUrl = "ws://另一个服务器地址/stt"
```

## 📋 **立即执行的优化步骤**

### **第一步：增强监控**
运行增强的日志监控：
```bash
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat | grep -E "(WS.*Received|listen|ready|stt|error|Audio frame sent)"
```

### **第二步：验证音频发送**
在应用中说话时，确认日志中是否有：
```
WS: Sending audio frame: XXX bytes
ChatViewModel: Sending audio frame #XXX
```

### **第三步：服务器健康检查**  
在另一个终端测试：
```bash
curl -v http://47.122.144.73:8000/
ping 47.122.144.73
```

### **第四步：协议调试**
如果服务器无响应，尝试：
1. 重启服务器
2. 检查服务器STT模块状态  
3. 验证服务器日志

## 🎯 **预期优化结果**

### **短期目标**：
- 确认服务器收到并响应监听请求
- 建立音频数据传输确认机制
- 获得STT服务状态反馈

### **长期目标**：
- 实现完整的语音识别流程
- 优化音频参数和网络传输
- 增强错误处理和重连机制

## 📊 **成功指标**

监控以下关键日志的出现：
```
✅ WS: Received text message: {"type":"listen","state":"ready"}
✅ WS: Audio frame sent successfully  
✅ WS: Received text message: {"type":"stt","text":"用户说的话"}
✅ ChatViewModel: >> 用户说的话
```

一旦看到这些日志，说明语音助手功能完全恢复正常！ 