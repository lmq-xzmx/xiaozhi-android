# 🚀 多设备问题快速修复

## 🎯 **问题解决**

您有两个设备连接，需要指定具体设备ID。

### ✅ **推荐方案：使用真实设备测试**

在Terminal.app中执行以下命令（逐条复制执行）：

```bash
# 1. 导航到项目目录
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 2. 清空日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -c

# 3. 安装应用到真实设备
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r app/build/outputs/apk/debug/app-debug.apk

# 4. 授予录音权限
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO

# 5. 开始监控日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

### 📱 **测试流程**

**执行完上述命令后**：

1. **在真实设备(SOZ95PIFVS5H6PIZ)上**启动VoiceBot应用
2. **选择服务器配置**（XiaoZhi或SelfHost）
3. **点击连接**进入聊天界面
4. **对着设备说话**测试语音功能
5. **观察终端日志输出**

### 🔍 **预期日志流程**

正常情况下应该看到：

```
AudioRecorder: Starting audio recording...
AudioRecorder: AudioRecord initialized successfully
ChatViewModel: OpusEncoder created successfully
AudioRecorder: Audio recording thread started
ChatViewModel: Device state set to LISTENING
AudioRecorder: Audio frames processed: 100
ChatViewModel: Sending audio frame #1: 120 bytes
WS: Received text message: {"type":"stt","text":"您说的话"}
```

### ⚠️ **如果日志在某步停止**

告诉我停在哪一步，我们可以精确定位问题：

- **停在"Starting audio recording"** → 权限问题
- **停在"AudioRecord initialized"** → 硬件问题  
- **停在"Audio frames processed"** → 录音失败
- **停在"Sending audio frame"** → 网络问题
- **没有"Received text message"** → 服务器问题

### 🆘 **备用方案：使用模拟器**

如果真实设备有问题，可以测试模拟器：

```bash
# 替换所有命令中的设备ID为模拟器ID
# 将 SOZ95PIFVS5H6PIZ 替换为 emulator-5554
```

### ✅ **下一步操作**

1. **在Terminal.app中逐条执行上述命令**
2. **在真实设备上测试应用**
3. **将日志输出结果告诉我**

这样我们就能精确定位"始终Listening"问题的根本原因！ 