# 🔧 修正的安装和测试命令

## ✅ **APK文件位置已找到**

正确的APK路径：`./app/build/intermediates/apk/debug/app-debug.apk`

## 📱 **修正的命令序列**

请在Terminal.app中逐条执行：

### **第一步：重新安装应用**

```bash
# 安装应用到真实设备（使用正确路径）
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r ./app/build/intermediates/apk/debug/app-debug.apk
```

### **第二步：手动授予权限（在设备上操作）**

由于adb无法直接授予权限，需要：

1. **在Android设备上打开"设置"**
2. **找到"应用管理"或"应用"**
3. **找到"VoiceBot"应用**
4. **点击"权限"**
5. **开启"麦克风"权限**

**或者更简单的方法**：
- 直接启动VoiceBot应用
- 应用会自动请求麦克风权限
- 点击"允许"

### **第三步：开始监控日志**

```bash
# 清空日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -c

# 开始监控关键日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

### **第四步：应用测试**

1. **启动VoiceBot应用**
2. **授予麦克风权限**（如果弹出请求）
3. **选择服务器配置**（XiaoZhi或SelfHost）
4. **点击连接**
5. **进入聊天界面**
6. **对着设备说话测试**

## 🔍 **监控重点**

观察日志是否按以下顺序出现：

```
AudioRecorder: Starting audio recording...           # 🎤 音频录制启动
AudioRecorder: AudioRecord initialized successfully  # ✅ 录音组件初始化
ChatViewModel: OpusEncoder created successfully       # ✅ 编码器创建成功
AudioRecorder: Audio recording thread started        # ✅ 录音线程启动
ChatViewModel: Device state set to LISTENING         # ✅ 设备进入监听状态
AudioRecorder: Audio frames processed: 100           # 📊 音频帧处理
ChatViewModel: Sending audio frame #1: 120 bytes     # 📤 音频数据发送
WS: Received text message: {"type":"stt","text":"..."} # 🗣️ 服务器响应
```

## ⚠️ **如果出现问题**

**如果日志停在某一步，告诉我具体位置**：

| 停止位置 | 可能原因 | 解决方案 |
|---------|----------|----------|
| 音频录制启动前 | 权限未授予 | 检查麦克风权限 |
| 录音组件初始化 | 硬件问题 | 重启应用/设备 |
| 音频帧处理 | 录音失败 | 确认对着设备说话 |
| 音频数据发送 | 网络问题 | 检查网络连接 |
| 服务器响应 | 服务器问题 | 尝试不同服务器配置 |

## 🚀 **立即执行**

现在请按照上述步骤操作，并告诉我：

1. **应用安装是否成功**
2. **权限是否已授予** 
3. **日志输出内容**
4. **应用界面反应**

这样我们就能定位"始终Listening"问题的根本原因！ 