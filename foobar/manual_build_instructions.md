# 📱 手动编译安装APK指令

## 🎯 编译环境准备

### 1. 确认项目目录
```bash
cd /Users/xzmx/Downloads/my-project/xiaozhi-android
```

### 2. 检查设备连接
```bash
adb devices
# 应该看到: SOZ95PIFVS5H6PIZ    device
```

## 🔧 编译步骤

### 步骤1: 清理项目
```bash
./gradlew clean
```

### 步骤2: 编译APK
```bash
./gradlew assembleDebug
```

### 步骤3: 检查APK文件
```bash
ls -la app/build/outputs/apk/debug/app-debug.apk
```

## 📲 安装步骤

### 步骤4: 卸载旧版本
```bash
adb -s SOZ95PIFVS5H6PIZ uninstall info.dourok.voicebot
```

### 步骤5: 安装新APK
```bash
adb -s SOZ95PIFVS5H6PIZ install app/build/outputs/apk/debug/app-debug.apk
```

### 步骤6: 授予权限
```bash
adb -s SOZ95PIFVS5H6PIZ shell pm grant info.dourok.voicebot android.permission.RECORD_AUDIO
adb -s SOZ95PIFVS5H6PIZ shell pm grant info.dourok.voicebot android.permission.INTERNET
adb -s SOZ95PIFVS5H6PIZ shell pm grant info.dourok.voicebot android.permission.ACCESS_NETWORK_STATE
adb -s SOZ95PIFVS5H6PIZ shell pm grant info.dourok.voicebot android.permission.WAKE_LOCK
```

### 步骤7: 启动应用
```bash
adb -s SOZ95PIFVS5H6PIZ shell am start -n info.dourok.voicebot/.MainActivity
```

## 🔍 验证和调试

### 查看实时日志
```bash
adb -s SOZ95PIFVS5H6PIZ logcat -s ChatViewModel OtaConfigManager OtaIntegrationService
```

### 检查OTA配置
```bash
adb -s SOZ95PIFVS5H6PIZ logcat -s ChatViewModel | grep -i "ota\|websocket"
```

### 应用信息
```bash
adb -s SOZ95PIFVS5H6PIZ shell dumpsys package info.dourok.voicebot
```

## 🎯 OTA配置验证

编译成功后，应用将包含以下新功能：

1. **OTA配置获取**: 从 `http://47.122.144.73:8002/xiaozhi/ota/` 获取配置
2. **动态WebSocket**: 自动配置 `ws://47.122.144.73:8000/xiaozhi/v1/`
3. **Fallback机制**: 配置失败时使用默认配置
4. **STT兼容**: 语音识别功能保持完全不变

## 📊 测试要点

### 首次启动测试
- 检查OTA配置获取日志
- 验证WebSocket连接建立
- 测试语音识别功能

### 设备激活测试
- 如提示激活，记录激活码
- 访问管理面板完成绑定
- 验证激活后的配置更新

### 功能完整性测试
- 语音识别准确性
- TTS播放流畅性
- 连续对话稳定性

## 🚨 常见问题

### 编译失败
- 检查NDK版本兼容性
- 清理`.gradle`缓存
- 使用Android Studio编译

### 安装失败
- 确保设备已开启USB调试
- 检查应用签名冲突
- 尝试手动卸载旧版本

### 运行异常
- 查看logcat日志
- 检查权限授予情况
- 验证网络连接

## 🎉 成功标志

编译安装成功后，您应该看到：
- ✅ APK文件生成成功
- ✅ 设备安装无错误
- ✅ 权限授予完成
- ✅ 应用正常启动
- ✅ OTA配置获取成功
- ✅ STT功能正常工作 