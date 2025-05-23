# Android调试环境设置指南

## 🚨 当前问题

1. ✅ **Gradle构建成功** - 应用已成功编译
2. ❌ **ADB命令不可用** - 需要配置Android SDK路径

## 🔧 解决方案

### 第一步：配置ADB命令

您的Android SDK已安装在：`~/Library/Android/sdk/platform-tools/`

**临时解决方案（当前终端会话）：**
```bash
export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"
```

**永久解决方案（推荐）：**
将以下行添加到您的shell配置文件：

对于zsh（默认）：
```bash
echo 'export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

对于bash：
```bash
echo 'export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 第二步：验证ADB可用

```bash
adb version
```

应该显示类似：
```
Android Debug Bridge version 1.0.41
```

### 第三步：安装并调试应用

1. **连接Android设备或启动模拟器**

2. **验证设备连接**：
```bash
adb devices
```

3. **安装应用**：
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

4. **启动日志监控**：
```bash
adb logcat -c  # 清空日志
adb logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

5. **在另一个终端窗口**启动应用并测试语音功能

## 🎯 预期的日志输出

### 正常情况下应该看到：

```
ChatViewModel: Starting audio encoding and recording setup...
AudioRecorder: Starting audio recording...
AudioRecorder: AudioRecord initialized successfully
ChatViewModel: OpusEncoder created successfully
ChatViewModel: AudioRecorder created successfully
AudioRecorder: Audio recording thread started
ChatViewModel: Audio recording flow started
ChatViewModel: Device state set to LISTENING
AudioRecorder: Audio frames processed: 100, last frame size: 1920 bytes
ChatViewModel: Encoding audio frame: 1920 bytes
ChatViewModel: Sending audio frame #1: 120 bytes
WS: Received text message: {"type":"stt","text":"您说的话"}
ChatViewModel: >> 您说的话
```

### 如果在某步停止，对应的问题：

1. **停在"Starting audio recording"** → 权限问题
2. **停在"AudioRecord initialized"** → 硬件/权限问题  
3. **停在"OpusEncoder created"** → NDK库问题
4. **停在"Audio frames processed"** → 录音失败
5. **停在"Sending audio frame"** → WebSocket连接问题
6. **没有"Received text message"** → 服务器端问题

## 🔍 快速诊断命令

```bash
# 检查录音权限
adb shell dumpsys package info.dourok.voicebot | grep RECORD_AUDIO

# 检查设备连接
adb devices

# 查看完整应用日志
adb logcat | grep voicebot

# 仅查看错误
adb logcat | grep -E "(ERROR|FATAL)"
```

## 📱 测试步骤

1. 确保设备已连接且开启USB调试
2. 启动日志监控
3. 打开应用
4. 选择任一服务器配置（XiaoZhi或SelfHost）
5. 点击连接进入聊天界面
6. 对着手机说话测试
7. 观察日志输出和应用反应

## 🛠 常见问题解决

### 权限被拒绝
```bash
# 手动授予录音权限
adb shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO
```

### 设备未检测到
```bash
# 重启adb服务
adb kill-server
adb start-server
```

### 应用崩溃
```bash
# 查看崩溃日志
adb logcat | grep -A 10 -B 10 "FATAL EXCEPTION"
```

根据日志输出，我们可以精确定位"始终Listening"问题的根本原因并提供针对性解决方案。 