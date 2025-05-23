# 🚀 完整修正方案：重新构建和安装

## ❌ **问题分析**
APK文件不存在，需要重新构建应用。

## ✅ **完整解决步骤**

### **第一步：重新构建APK**

在Terminal.app中执行：

```bash
# 导航到项目目录
cd /Users/xzmx/Downloads/my-project/xiaozhi-android

# 清理项目
./gradlew clean

# 构建调试版本APK
./gradlew assembleDebug
```

### **第二步：查找新生成的APK**

```bash
# 查找APK文件位置
find . -name "*.apk" -type f
```

常见的APK位置：
- `app/build/outputs/apk/debug/app-debug.apk`
- `app/build/intermediates/apk/debug/app-debug.apk`

### **第三步：安装APK到设备**

假设APK在标准位置，使用以下命令：

```bash
# 方式1：如果APK在outputs目录
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r app/build/outputs/apk/debug/app-debug.apk

# 方式2：如果需要-t参数（测试APK）
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r -t app/build/outputs/apk/debug/app-debug.apk
```

### **第四步：启动日志监控**

```bash
# 清空日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -c

# 开始监控关键日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

### **第五步：测试应用**

1. **在设备上启动VoiceBot应用**
2. **授予麦克风权限**（点击"允许"）
3. **选择服务器配置**（XiaoZhi或SelfHost）
4. **点击连接进入聊天界面**
5. **对着设备说话测试**
6. **观察日志输出**

## 🔍 **监控重点**

观察日志是否依次出现：

```
AudioRecorder: Starting audio recording...           # 🎤 音频录制启动
AudioRecorder: AudioRecord initialized successfully  # ✅ 录音组件初始化
ChatViewModel: OpusEncoder created successfully       # ✅ 编码器创建
AudioRecorder: Audio recording thread started        # ✅ 录音线程启动
ChatViewModel: Device state set to LISTENING         # ✅ 进入监听状态
AudioRecorder: Audio frames processed: 100           # 📊 音频帧处理
ChatViewModel: Sending audio frame #1: 120 bytes     # 📤 发送音频数据
WS: Received text message: {"type":"stt","text":"..."} # 🗣️ 服务器响应
```

## ⚠️ **如果构建失败**

如果`./gradlew assembleDebug`失败，尝试：

```bash
# 确保Gradle Wrapper有执行权限
chmod +x gradlew

# 或者使用系统Gradle
gradle assembleDebug
```

## 📋 **完成后请告诉我**：

1. **构建是否成功**
2. **APK文件的确切位置**
3. **安装是否成功**
4. **日志输出内容**
5. **应用的语音测试反应**

这样我们就能最终解决"始终Listening"问题！ 