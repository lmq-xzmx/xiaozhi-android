# 🚀 小智Android应用最终操作指南

## 📋 当前状态总结

### ✅ **已完成的修复**
1. **绑定流程修复**：修复了`OtaResult.isActivated`判断逻辑
2. **WebSocket连接修复**：修复了`WebsocketProtocol.start()`方法
3. **原生库问题**：已解决`libapp.so`缺失问题

### 🎯 **核心修复内容**
- **文件**: `app/src/main/java/info/dourok/voicebot/protocol/WebsocketProtocol.kt`
- **修复**: `start()`方法现在会自动调用`openAudioChannel()`建立WebSocket连接
- **效果**: 应用启动时自动建立与服务器的连接，不再显示Idle状态

## 🛠️ **立即执行步骤**

### 第1步：重新构建APK
```bash
# 在xiaozhi-android目录下执行
./gradlew assembleDebug
```

### 第2步：安装修复版本
```bash
adb -s SOZ95PIFVS5H6PIZ install -r app/build/outputs/apk/debug/app-debug.apk
```

### 第3步：清除应用数据（推荐）
```bash
adb -s SOZ95PIFVS5H6PIZ shell pm clear info.dourok.voicebot
```

### 第4步：启动应用
```bash
adb -s SOZ95PIFVS5H6PIZ shell am start -n info.dourok.voicebot/.MainActivity
```

### 第5步：验证修复效果
等待10秒后，检查应用状态：
```bash
# 检查WebSocket日志
adb -s SOZ95PIFVS5H6PIZ logcat -d "WS:*" "*:S"
```

## 📊 **期望的修复效果**

### 应用界面变化
- ❌ **修复前**: 显示"Idle"状态，功能不可用
- ✅ **修复后**: 正常显示聊天界面，可以交互

### 日志变化
修复后应该看到以下关键日志：
```
I/WS: WebSocket protocol start() called
I/WS: 正在建立WebSocket连接...
I/WS: Opening audio channel to ws://47.122.144.73:8000/xiaozhi/v1/
I/WS: WebSocket connected successfully
I/WS: Sending hello message: {...}
I/WS: 收到服务器hello，解析中...
I/WS: WebSocket连接建立成功
```

### 功能测试
1. **聊天功能**: 点击聊天按钮应该有反应
2. **语音功能**: 应该可以进行语音交互
3. **状态显示**: 不再显示"Idle"，显示正常状态

## 🔍 **故障排除**

### 如果仍显示Idle状态
1. **检查日志**: 查看是否有WebSocket连接相关日志
2. **网络检查**: 确认设备可以访问`47.122.144.73:8000`
3. **重新安装**: 完全卸载后重新安装应用

### 如果连接失败
1. **服务器检查**: 
   ```bash
   # 测试服务器连通性
   curl http://47.122.144.73:8000/xiaozhi/v1/
   ```
2. **配置检查**: 确认OTA URL设置正确
3. **权限检查**: 确认应用有网络权限

## 🎯 **验证清单**

### 必须验证的项目
- [ ] APK重新构建成功
- [ ] APK安装成功
- [ ] 应用启动成功
- [ ] 可以看到WebSocket连接日志
- [ ] 应用不再显示"Idle"状态
- [ ] 聊天功能可以正常使用

### 可选验证项目
- [ ] 语音录制功能正常
- [ ] 语音播放功能正常
- [ ] 与服务器通信正常
- [ ] 长时间运行稳定

## 📞 **如果需要进一步帮助**

### 收集诊断信息
如果修复后仍有问题，请收集以下信息：

1. **应用日志**:
   ```bash
   adb -s SOZ95PIFVS5H6PIZ logcat -d > app_logs.txt
   ```

2. **应用状态**: 描述应用界面显示的内容

3. **网络状态**: 
   ```bash
   ping 47.122.144.73
   curl http://47.122.144.73:8000/xiaozhi/v1/
   ```

### 备选方案
如果WebSocket服务器不可用，可以使用本地测试服务器：
1. 启动本地服务器: `python3 foobar/fixed_test_server.py`
2. 修改应用配置指向本地服务器
3. 测试基本功能

## 🎉 **成功标志**

当您看到以下情况时，说明修复成功：
1. ✅ 应用启动后不再显示"Idle"状态
2. ✅ 可以看到WebSocket连接成功的日志
3. ✅ 聊天界面可以正常交互
4. ✅ 应用响应用户操作

---

**按照这个指南执行，应该能够完全解决小智Android应用的Idle状态问题！** 🚀 