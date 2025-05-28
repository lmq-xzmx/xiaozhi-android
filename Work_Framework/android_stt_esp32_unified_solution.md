# 📱 Android端STT与ESP32统一解决方案

## 🎯 **问题核心**

您确认了STT问题在于**客户端上的STT**，而ESP32端有更好的**服务器端STT方案**。我们需要让Android端与ESP32端保持一致。

## 🔍 **ESP32端STT方案（正确标准）**

### 📂 **位置与配置**
```
位置: ../xiaozhi/main/xiaozhi-server/core/providers/asr/
配置: config.yaml -> selected_module.ASR: FunASR
实现: fun_local.py / fun_server.py
```

### ⚙️ **工作原理**
1. **设备发送音频** → WebSocket传输Opus数据到服务器
2. **服务器处理STT** → 使用FunASR模型进行语音识别
3. **返回标准响应** → `{"type": "stt", "text": "识别结果", "session_id": "xxx"}`
4. **设备显示结果** → 解析STT响应并更新UI

## ❌ **Android端当前问题**

### 问题分析
1. **STT处理不一致** - Android可能在客户端处理STT
2. **响应处理缺失** - 没有正确接收服务器STT响应
3. **音频流程不完整** - 音频发送后缺少STT结果处理

### 关键代码检查
- ✅ `ChatViewModel.observeProtocolMessages()` 已有STT处理逻辑
- ✅ `WebsocketProtocol.onMessage()` 已有STT响应解析
- ❌ **问题可能在音频录制或传输环节**

## 🔧 **完整修复方案**

### 修复1: 确保音频录制流程完整
```kotlin
// ChatViewModel.startAudioRecordingFlow() 需要确保:
1. AudioRecorder.startRecording() 正常启动
2. OpusEncoder.encode() 正常编码
3. Protocol.sendAudio() 正常发送
4. 服务器能接收到音频数据
```

### 修复2: 验证服务器STT配置
```yaml
# 确认服务器配置正确
selected_module:
  ASR: FunASR  # 使用FunASR模型

ASR:
  FunASR:
    type: fun_local
    model_dir: models/SenseVoiceSmall
    output_dir: tmp/
```

### 修复3: 增强STT响应处理
```kotlin
// WebsocketProtocol.kt 中增强STT日志
"stt" -> {
    val text = json.optString("text")
    Log.i(TAG, "🎯 收到STT结果: '$text'")
    if (text.isNotEmpty()) {
        incomingJsonFlow.emit(json)
    } else {
        Log.w(TAG, "STT响应为空")
    }
}
```

## 🧪 **测试验证步骤**

### 步骤1: 启动应用测试
```bash
# 1. 安装最新APK
adb -s SOZ95PIFVS5H6PIZ install -r app-debug.apk

# 2. 启动应用
adb -s SOZ95PIFVS5H6PIZ shell am start -n info.dourok.voicebot/.MainActivity

# 3. 监控日志
adb -s SOZ95PIFVS5H6PIZ logcat | grep -E "STT|stt|audio|listen"
```

### 步骤2: 功能测试
1. **点击"开始监听"** - 确认状态变为"🎤 监听中"
2. **清晰说话** - "你好小智，请介绍一下你自己"
3. **观察日志** - 查看STT响应: `{"type": "stt", "text": "..."}`
4. **检查UI** - 确认聊天界面显示用户输入

### 步骤3: 问题排查
- **无音频发送** → 检查录音权限和AudioRecorder
- **无服务器响应** → 检查FunASR服务和网络
- **有响应无STT** → 检查响应格式和解析逻辑
- **有STT无UI更新** → 检查ChatViewModel处理流程

## 📊 **预期效果**

### 修复后的完整流程
```
用户说话 → 录音(PCM) → Opus编码 → WebSocket发送 
                                    ↓
服务器FunASR识别 → 生成文本 → 返回STT响应 → Android解析 → UI显示
```

### 成功标志
- ✅ 日志显示: `🎯 收到STT结果: '你好小智'`
- ✅ 聊天界面显示用户输入
- ✅ 服务器返回对应的TTS响应
- ✅ Android端与ESP32端STT方案完全一致

## 🎯 **关键检查点**

1. **音频权限** - `android.permission.RECORD_AUDIO` 已授予
2. **WebSocket连接** - 连接状态正常，能收发消息
3. **服务器STT** - FunASR服务运行正常
4. **响应格式** - 服务器返回标准STT格式
5. **UI处理** - ChatViewModel正确处理STT消息

## 🔄 **下一步操作**

1. **重新构建APK**: `./gradlew assembleDebug`
2. **安装测试**: `adb install -r app-debug.apk`
3. **启动应用**: 测试STT功能
4. **监控日志**: 确认STT响应正常
5. **验证一致性**: 与ESP32端对比测试

---

**目标**: 让Android端使用与ESP32端相同的**服务器端FunASR STT方案**，确保产品一致性和稳定性。 