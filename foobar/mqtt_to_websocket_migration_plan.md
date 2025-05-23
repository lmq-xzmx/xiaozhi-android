# MQTT到WebSocket完整迁移方案

## 问题根本原因

1. **协议层不匹配**：配置了WebSocket URL，但传输类型仍可能为MQTT
2. **依赖链断裂**：MQTT需要OTA配置，但服务器不提供完整的MQTT配置
3. **音频流程差异**：MQTT使用UDP+AES加密，WebSocket使用二进制帧直传

## 关联模块分析

### 核心模块依赖关系图
```
ServerFormData (配置层)
    ↓
FormRepository (业务层) 
    ↓ 设置 transportType 和 URL
SettingsRepository (数据层)
    ↓ 读取配置
ChatViewModel (UI层) 
    ↓ 根据 transportType 选择协议
Protocol 接口实现:
    ├── MqttProtocol (MQTT实现)
    └── WebsocketProtocol (WebSocket实现)
```

### 需要检查的关键文件

#### 1. 配置数据模型层
- ✅ `app/src/main/java/info/dourok/voicebot/data/model/ServerFormData.kt`
  - 确认 `XiaoZhiConfig.transportType = TransportType.WebSockets`

#### 2. 数据仓库层  
- ⚠️ `app/src/main/java/info/dourok/voicebot/data/SettingsRepository.kt`
  - **风险点**: 默认值 `transportType = TransportType.MQTT`
  - **需要修改**: 改为 `TransportType.WebSockets`

- ⚠️ `app/src/main/java/info/dourok/voicebot/data/FormRepository.kt`
  - **风险点**: 依赖OTA检查设置 `mqttConfig`
  - **需要修改**: WebSockets模式下跳过MQTT配置设置

#### 3. 协议实现层
- ✅ `app/src/main/java/info/dourok/voicebot/protocol/WebsocketProtocol.kt`
  - 正常工作，支持音频二进制帧传输

- ⚠️ `app/src/main/java/info/dourok/voicebot/ui/ChatViewModel.kt` 
  - **风险点**: MQTT模式下需要 `settings.mqttConfig!!`
  - **潜在问题**: 如果配置错误可能空指针异常

#### 4. 音频处理层
- ✅ `app/src/main/java/info/dourok/voicebot/AudioRecorder.kt`
- ✅ `app/src/main/java/info/dourok/voicebot/OpusEncoder.kt`
- ✅ `app/src/main/java/info/dourok/voicebot/OpusDecoder.kt`
- ✅ `app/src/main/java/info/dourok/voicebot/OpusStreamPlayer.kt`

#### 5. 表单验证层
- ✅ `app/src/main/java/info/dourok/voicebot/domain/ValidateFormUseCase.kt`
  - 已有协议类型与URL匹配验证

## 修改清单

### 必须修改的文件

#### 1. SettingsRepository.kt - 修改默认传输类型
```kotlin
// 当前问题代码
override var transportType: TransportType = TransportType.MQTT  ❌

// 应该修改为
override var transportType: TransportType = TransportType.WebSockets  ✅
```

#### 2. ChatViewModel.kt - 增强错误处理
```kotlin
// 当前存在风险的代码
TransportType.MQTT -> {
    MqttProtocol(context, settings.mqttConfig!!)  // 可能空指针
}

// 建议改进
TransportType.MQTT -> {
    val mqttConfig = settings.mqttConfig
    if (mqttConfig == null) {
        throw IllegalStateException("MQTT配置未初始化，请先执行OTA检查")
    }
    MqttProtocol(context, mqttConfig)
}
```

#### 3. FormRepository.kt - 优化配置设置逻辑
```kotlin
// 当前代码
if(formData.serverType == ServerType.XiaoZhi) {
    settingsRepository.transportType = formData.xiaoZhiConfig.transportType
    settingsRepository.webSocketUrl = formData.xiaoZhiConfig.webSocketUrl
    ota.checkVersion(formData.xiaoZhiConfig.qtaUrl)
    resultFlow.value = FormResult.XiaoZhiResult(ota.otaResult)
    settingsRepository.mqttConfig = ota.otaResult?.mqttConfig  // 可能为null
}

// 建议改进
if(formData.serverType == ServerType.XiaoZhi) {
    settingsRepository.transportType = formData.xiaoZhiConfig.transportType
    settingsRepository.webSocketUrl = formData.xiaoZhiConfig.webSocketUrl
    
    // 根据传输类型决定是否需要OTA检查
    if (formData.xiaoZhiConfig.transportType == TransportType.MQTT) {
        ota.checkVersion(formData.xiaoZhiConfig.qtaUrl)
        settingsRepository.mqttConfig = ota.otaResult?.mqttConfig
        resultFlow.value = FormResult.XiaoZhiResult(ota.otaResult)
    } else {
        // WebSockets模式下不需要OTA检查
        settingsRepository.mqttConfig = null
        resultFlow.value = FormResult.XiaoZhiResult(null)
    }
}
```

## 协议差异对比

### MQTT协议流程
1. 连接MQTT Broker (`tcp://endpoint`)
2. 通过OTA获取MQTT配置 (endpoint, clientId, username, password, topics)
3. 发送hello消息到发布主题
4. 服务器响应包含UDP配置 (server, port, AES key, nonce)
5. 建立UDP连接进行音频传输
6. 音频数据使用AES/CTR加密

### WebSocket协议流程  
1. 直接连接WebSocket服务器 (`ws://` 或 `wss://`)
2. 发送hello消息包含音频参数
3. 服务器响应确认连接
4. 音频数据直接通过WebSocket二进制帧传输
5. 无需额外加密（可依赖WSS的TLS）

## 音频传输对比

### MQTT模式音频参数
```json
{
  "format": "opus",
  "sample_rate": 16000,
  "channels": 1,
  "frame_duration": 20  // 20ms帧
}
```

### WebSocket模式音频参数
```json
{
  "format": "opus", 
  "sample_rate": 16000,
  "channels": 1,
  "frame_duration": 60  // 60ms帧
}
```

**关键差异**: 帧持续时间不同，可能需要服务器端适配

## 服务器兼容性检查

### 必须确认的服务器端支持：

1. **WebSocket连接支持**
   - 是否支持 `ws://47.122.144.73:8000/xiaozhi/v1/` 连接
   - 是否支持WebSocket子协议协商

2. **Hello消息格式**
   - 是否支持 `{"type":"hello","transport":"websocket"}` 格式
   - 是否正确响应session_id

3. **音频二进制帧处理**
   - 是否支持直接接收Opus编码的二进制数据
   - 是否支持60ms帧长度（或需要调整为20ms）

4. **STT响应格式**
   - 是否通过WebSocket文本消息返回识别结果
   - 响应格式是否为 `{"type":"stt","text":"识别文本"}`

## 验证步骤

### 第一步：确认配置正确
```bash
# 检查当前配置
adb logcat | grep -E "(ChatViewModel|SettingsRepository|transportType)"
```

### 第二步：测试WebSocket连接
```bash  
# 监控WebSocket连接日志
adb logcat | grep "WS"
```

### 第三步：验证音频流程
```bash
# 监控音频录制和编码
adb logcat | grep -E "(AudioRecorder|OpusEncoder)"
```

### 第四步：检查服务器响应
```bash
# 查看服务器STT响应
adb logcat | grep -E "(Received.*stt|>>.*)"
```

## 风险评估

### 低风险
- ✅ WebSocket协议实现已完成
- ✅ 音频录制和编码模块独立，不受协议影响  
- ✅ 表单验证已支持协议匹配检查

### 中风险  
- ⚠️ 服务器端是否完全支持WebSocket协议
- ⚠️ 音频帧长度差异可能需要调整
- ⚠️ 认证机制可能需要适配

### 高风险
- ❌ OTA检查逻辑耦合，需要条件化处理
- ❌ 默认传输类型仍为MQTT，可能导致配置错误
- ❌ 错误处理不够完善，可能出现空指针异常

## 立即行动项

1. **修改 SettingsRepository 默认值** (必须)
2. **优化 FormRepository 配置逻辑** (推荐)  
3. **增强 ChatViewModel 错误处理** (推荐)
4. **测试服务器兼容性** (必须)
5. **收集详细日志进行调试** (推荐)

## 回滚方案

如果WebSocket迁移出现问题，可以：
1. 恢复 `transportType = TransportType.MQTT`
2. 提供完整的MQTT服务器配置
3. 确保OTA端点返回完整的mqttConfig

总结：这个迁移主要是配置层面的修改，核心音频处理模块不需要改动，但需要仔细处理配置依赖关系和错误情况。 