# 🎯 STT功能完整修复指南

## ✅ 已完成的修复

1. **编译错误修正**：WebsocketProtocol.kt语法问题已解决
2. **设备ID固定**：`00:11:22:33:44:55`（已在服务器绑定）
3. **Gradle版本修正**：AGP版本从8.10.0修正为8.7.0

## 🚀 立即执行步骤

### 重要提示：由于PowerShell有显示问题，请使用macOS原生Terminal执行以下命令

### 步骤1：打开新的Terminal窗口
```bash
# 按 Cmd+Space，输入 Terminal，回车
# 或者在Finder中找到 应用程序 → 实用工具 → 终端
```

### 步骤2：导航到项目目录并清理
```bash
cd /Users/xzmx/Downloads/my-project/xiaozhi-android
./gradlew clean
```

### 步骤3：编译Debug APK
```bash
./gradlew app:assembleDebug
```

### 步骤4：检查连接的Android设备
```bash
adb devices -l
```

### 步骤5：清除应用数据（最关键步骤！）
选择以下任一方法：

**方法A：手机上手动操作**
- 设置 → 应用管理 → VoiceBot → 存储 → 清除数据

**方法B：如果设备已连接**
```bash
adb shell pm clear info.dourok.voicebot
```

### 步骤6：安装更新的APK
```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### 步骤7：验证设备绑定状态
```bash
cd foobar
python3 test_your_device_id.py
```

## 🎯 测试STT功能

1. **启动VoiceBot应用**
2. **点击录音按钮**
3. **说话测试**
4. **期望结果**：应该显示转录文字！

## 📋 成功验证标志

### 预期日志输出：
```
Current Device-Id: 00:11:22:33:44:55
WebSocket connected successfully
```

### 预期应用行为：
- ✅ 语音识别按钮可用
- ✅ 说话后显示转录文字  
- ✅ 没有"设备绑定"错误提示

## 🔧 故障排除

如果STT功能仍然不工作：

1. **确认应用数据已清除**（这是最常见的问题）
2. **检查设备ID日志**（应该显示 `00:11:22:33:44:55`）
3. **确认WebSocket连接成功**（没有绑定错误）
4. **重新验证绑定状态**：
   ```bash
   cd foobar && python3 test_your_device_id.py
   ```

## 📱 如果没有Android设备连接

如果您没有Android设备连接到电脑，可以：

1. **使用Android模拟器**：
   ```bash
   # 启动Android Studio
   # 创建或启动一个AVD（Android Virtual Device）
   ```

2. **通过USB连接真实设备**：
   - 在Android设备上启用开发者选项
   - 启用USB调试
   - 连接USB线到电脑

3. **通过WiFi连接**（如果设备支持）：
   ```bash
   # 首先通过USB连接一次
   adb tcpip 5555
   adb connect DEVICE_IP:5555
   ```

## 🎉 预期结果

完成所有步骤后，STT功能应该完全恢复正常：
- 语音识别按钮可用
- 说话后立即显示转录文字
- 没有设备绑定错误
- WebSocket连接稳定

---
**如果按照此指南操作后仍有问题，请提供具体的错误信息！** 🚀 