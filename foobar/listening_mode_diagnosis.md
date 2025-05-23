# "始终处于Listening模式"问题诊断

## 问题现状

✅ **已解决**: 两种服务器类型都能连接并进入聊天界面
❌ **待解决**: 模型一直处于listening状态，没有语音识别反馈

## 语音处理流程分析

### 正常的语音识别流程应该是：

1. **音频录制** → AudioRecorder采集麦克风数据
2. **音频编码** → OpusEncoder将PCM数据编码为Opus格式
3. **数据发送** → 通过WebSocket发送到服务器
4. **服务器处理** → 服务器进行语音识别(STT)
5. **结果返回** → 服务器返回识别的文本
6. **UI更新** → 显示用户说话内容和AI回复

### 可能的故障点：

## 1. 音频权限问题 🎤
**症状**: AudioRecorder初始化失败
**检查方法**: 查看日志中是否有"Security exception - missing audio permission"

## 2. 音频录制硬件问题 🔧
**症状**: AudioRecorder创建成功但无法采集数据
**检查方法**: 查看"Audio frames processed"计数是否增长

## 3. Opus编码器问题 📦
**症状**: 录制到音频但编码失败
**检查方法**: 查看"Opus encoding returned null"警告

## 4. 网络发送问题 🌐
**症状**: 编码成功但数据未发送到服务器
**检查方法**: 查看WebSocket发送日志和"Audio frames sent"计数

## 5. 服务器协议问题 🖥️
**症状**: 数据发送成功但服务器不识别或无响应
**检查方法**: 查看是否收到服务器的STT响应

## 6. 响应处理问题 📨
**症状**: 服务器有响应但客户端未正确处理
**检查方法**: 查看incomingJsonFlow的消息处理

## 诊断步骤

### 第一步：检查基础日志
运行以下命令收集关键日志：
```bash
adb logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

### 第二步：关键日志标识

**音频录制正常应该看到**:
```
AudioRecorder: Starting audio recording...
AudioRecorder: AudioRecord initialized successfully
AudioRecorder: Audio recording thread started
AudioRecorder: Audio frames processed: 100, last frame size: 1920 bytes
```

**音频编码正常应该看到**:
```
ChatViewModel: OpusEncoder created successfully
ChatViewModel: Encoding audio frame: 1920 bytes
ChatViewModel: Sending audio frame #1: 120 bytes
ChatViewModel: Audio frames sent: 50
```

**WebSocket发送正常应该看到**:
```
WS: Sending audio frame data (binary)
```

**服务器响应正常应该看到**:
```
WS: Received text message: {"type":"stt","text":"用户说的话"}
ChatViewModel: >> 用户说的话
```

### 第三步：问题定位

**如果停在某个步骤**:

1. **音频录制失败** → 检查录音权限、设备音频支持
2. **编码失败** → Opus库问题，可能需要检查NDK编译
3. **发送失败** → WebSocket连接问题
4. **无服务器响应** → 服务器端问题或协议不匹配
5. **响应未处理** → 客户端JSON解析问题

## 常见原因和解决方案

### 录音权限问题
```kotlin
// 在MainActivity中确认权限已授予
if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
    != PackageManager.PERMISSION_GRANTED) {
    // 权限未授予
}
```

### 服务器协议不匹配
**可能的问题**:
- 服务器期望不同的音频格式
- 服务器不支持实时语音识别
- 认证或会话问题

### 音频参数不匹配
**检查点**:
- 采样率：客户端16kHz vs 服务器期望
- 音频格式：Opus vs 其他格式
- 帧大小：60ms vs 服务器期望

## 快速排查命令

```bash
# 检查应用是否有录音权限
adb shell dumpsys package info.dourok.voicebot | grep RECORD_AUDIO

# 实时查看音频相关日志
adb logcat | grep -E "(AudioRecorder|OpusEncoder|ChatViewModel.*audio|WS.*audio)"

# 查看服务器响应
adb logcat | grep -E "(WS.*Received|ChatViewModel.*>>|ChatViewModel.*<<")"

# 检查权限和音频设备状态
adb shell dumpsys audio | grep -A 10 -B 10 "RECORD"
```

## 下一步行动

1. **运行日志收集命令**
2. **对比正常流程检查点**
3. **根据停止的步骤定位具体问题**
4. **实施对应的修复方案**

通过详细的日志分析，我们可以精确定位"始终listening"问题的根本原因。 