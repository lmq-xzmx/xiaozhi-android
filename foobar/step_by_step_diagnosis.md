# 🔍 语音助手问题逐步诊断流程

## 📋 **您的操作清单**

### ✅ **第一步：设备连接验证**

请在**新的终端窗口**（非PowerShell）中执行：

```bash
# 打开新的终端（Terminal.app）并导航到项目目录
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 检查设备连接
~/Library/Android/sdk/platform-tools/adb devices
```

**期望结果**：
```
List of devices attached
XXXXXXXXXXXXXX	device
```

如果没有设备或显示"unauthorized"，请：
1. 确保设备已连接USB线
2. 在设备上开启USB调试
3. 允许计算机调试权限

---

### ✅ **第二步：运行自动化诊断脚本**

在终端中执行：
```bash
./foobar/debug_voice_app.sh
```

**此脚本会自动执行**：
- ✅ 检查设备连接
- ✅ 清空旧日志
- ✅ 安装最新应用
- ✅ 授予录音权限
- ✅ 开始实时日志监控

---

### ✅ **第三步：应用测试流程**

1. **启动应用**：在设备上找到并点击"VoiceBot"应用

2. **进入配置**：
   - 选择任一服务器类型（XiaoZhi或SelfHost）
   - 点击"连接"

3. **进入聊天界面**：应该看到聊天界面和表情符号

4. **语音测试**：
   - 对着设备说话（例如："你好"）
   - 观察应用反应和终端日志

---

### ✅ **第四步：日志分析配合**

在语音测试过程中，请**同时观察**：

#### 🖥️ **终端日志输出应该显示**：
```
[19:30:15] 🎤 AudioRecorder: Starting audio recording...
[19:30:15] ✅ AudioRecorder: AudioRecord initialized successfully  
[19:30:15] ✅ ChatViewModel: OpusEncoder created successfully
[19:30:16] 📊 AudioRecorder: Audio frames processed: 100
[19:30:16] 📤 ChatViewModel: Sending audio frame #1: 120 bytes
[19:30:17] 🗣️ WS: Received text message: {"type":"stt","text":"你好"}
```

#### 📱 **应用界面应该显示**：
- 设备状态从"LISTENING"变为显示用户输入文本
- 出现AI回复
- 表情符号发生变化

---

### ✅ **第五步：问题定位配合**

**根据日志停止的位置，我们可以确定问题**：

| 日志停止位置 | 问题类型 | 您需要确认 |
|------------|----------|------------|
| 🎤 Starting audio recording | 权限问题 | 设备是否弹出录音权限请求 |
| ✅ AudioRecord initialized | 硬件问题 | 设备麦克风是否正常工作 |
| 📊 Audio frames processed | 录音数据问题 | 是否对着设备说话 |
| 📤 Sending audio frame | 网络问题 | 设备网络连接是否正常 |
| 🗣️ Received stt | 服务器问题 | 服务器是否支持语音识别 |

---

### ✅ **第六步：实时问题反馈**

**在测试过程中，请告诉我**：

1. **设备连接状态**：`adb devices`的输出结果
2. **应用安装结果**：是否成功安装
3. **权限授予结果**：是否有权限相关提示
4. **日志输出情况**：日志在哪一步停止了
5. **应用界面状态**：始终显示"LISTENING"还是有其他变化
6. **语音测试反应**：说话时是否有任何反馈

---

## 🚀 **开始执行**

现在请您：

1. **打开新的终端窗口**（避免PowerShell问题）
2. **连接Android设备**
3. **执行以上步骤**
4. **将每步的结果告诉我**

这样我们就能精确定位问题并提供针对性解决方案！

---

## 💡 **备用手动命令**

如果自动脚本有问题，可以手动执行：

```bash
# 检查连接
~/Library/Android/sdk/platform-tools/adb devices

# 安装应用
~/Library/Android/sdk/platform-tools/adb install -r app/build/outputs/apk/debug/app-debug.apk

# 授予权限
~/Library/Android/sdk/platform-tools/adb shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO

# 监控日志
~/Library/Android/sdk/platform-tools/adb logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
``` 