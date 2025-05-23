# 🚨 TEST_ONLY APK安装问题解决

## ❌ **问题原因**
```
INSTALL_FAILED_TEST_ONLY
```
这表示APK以测试模式构建，需要特殊参数安装。

## ✅ **解决方案1：使用-t参数安装测试APK**

```bash
# 使用-t参数强制安装测试APK
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r -t ./app/build/intermediates/apk/debug/app-debug.apk
```

## ✅ **解决方案2：构建正式调试版本**

如果方案1不行，重新构建APK：

```bash
# 清理并重新构建
./gradlew clean
./gradlew assembleDebug
```

构建完成后APK路径可能变为：`app/build/outputs/apk/debug/app-debug.apk`

## 🚀 **立即尝试**

**先试方案1（推荐）**：
```bash
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ install -r -t ./app/build/intermediates/apk/debug/app-debug.apk
```

**如果成功，继续后续步骤**：
```bash
# 清空日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -c

# 监控日志
~/Library/Android/sdk/platform-tools/adb -s SOZ95PIFVS5H6PIZ logcat -s AudioRecorder ChatViewModel WS OpusEncoder OpusDecoder
```

## 📱 **然后在设备上**：
1. 启动VoiceBot应用
2. 授予麦克风权限
3. 选择服务器配置
4. 测试语音功能
5. 观察日志输出

告诉我执行结果！ 