# 🚀 WebSocket配置修复 - 下一步行动指南

## 📋 **当前状态**
✅ **已完成的修复**：
1. ChatViewModel配置恢复逻辑 - 防止SettingsRepository配置丢失
2. ActivationManager缓存检查 - 避免不必要的OTA检查
3. 创建了测试验证脚本

## 🎯 **下一步具体行动**

### 第一步：编译修复后的代码 🔨

```bash
# 在xiaozhi-android目录下执行
./gradlew clean assembleDebug
```

**预期结果：**
- 生成 `app/build/outputs/apk/debug/app-debug.apk`
- 编译成功，无错误

**如果编译失败：**
```bash
# 检查编译错误
./gradlew assembleDebug --stacktrace

# 清理并重新编译
./gradlew clean
./gradlew assembleDebug
```

### 第二步：安装修复后的APK 📱

```bash
# 检查设备连接
adb devices

# 安装新APK（会覆盖旧版本）
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**预期结果：**
- 显示 "Success" 安装成功
- 应用版本更新

### 第三步：运行修复验证测试 🧪

```bash
# 运行我们创建的测试脚本
./foobar/websocket_config_fix_test.sh
```

**测试脚本会自动：**
1. 清除应用数据（模拟全新安装）
2. 首次启动并监控日志
3. 重启应用测试配置恢复
4. 检查配置文件状态
5. 总结测试结果

### 第四步：观察关键日志 👀

**成功修复的标志：**
```
✅ 使用缓存的WebSocket配置: ws://47.122.144.73:8000/xiaozhi/v1/
✅ 配置已从DeviceConfigManager恢复: ws://47.122.144.73:8000/xiaozhi/v1/
✅ SettingsRepository配置正常: ws://47.122.144.73:8000/xiaozhi/v1/
```

**仍有问题的标志：**
```
❌ SettingsRepository中WebSocket URL为空，从DeviceConfigManager恢复
❌ 🔍 没有缓存配置，执行OTA检查...
❌ WebSocket connection failed
```

### 第五步：手动验证功能 🎤

1. **完成设备绑定**
   - 启动应用
   - 如果显示激活码，访问管理面板完成绑定
   - 等待WebSocket连接建立

2. **测试语音功能**
   - 说话测试STT识别
   - 检查TTS播放
   - 验证语音打断功能

3. **测试重启恢复**
   - 强制停止应用：`adb shell am force-stop info.dourok.voicebot`
   - 重新启动：`adb shell am start -n info.dourok.voicebot/.MainActivity`
   - 检查是否自动恢复连接（无需重新绑定）

## 🔧 **备用方案**

### 如果修复仍不完全有效

**方案A：实施完整的SettingsRepository持久化**
```kotlin
// 修改 SettingsRepository.kt 使用DataStore
@Singleton
class SettingsRepositoryImpl @Inject constructor(
    private val context: Context
) : SettingsRepository {
    private val Context.settingsDataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")
    private val dataStore = context.settingsDataStore
    
    // 使用DataStore替代内存存储
    override var webSocketUrl: String?
        get() = runBlocking { dataStore.data.first()[WEBSOCKET_URL_KEY] }
        set(value) = runBlocking {
            dataStore.edit { prefs ->
                if (value != null) prefs[WEBSOCKET_URL_KEY] = value
                else prefs.remove(WEBSOCKET_URL_KEY)
            }
        }
}
```

**方案B：增强错误处理**
```kotlin
// 在ChatViewModel中添加更强的错误恢复
private suspend fun proceedWithActivatedDevice(websocketUrl: String) {
    // 多重配置恢复策略
    val finalWebsocketUrl = when {
        websocketUrl.isNotBlank() -> websocketUrl
        !settingsRepository.webSocketUrl.isNullOrEmpty() -> settingsRepository.webSocketUrl!!
        !deviceConfigManager.getWebsocketUrl().isNullOrEmpty() -> deviceConfigManager.getWebsocketUrl()!!
        else -> throw Exception("无法获取有效的WebSocket URL")
    }
    
    // 确保配置同步
    settingsRepository.webSocketUrl = finalWebsocketUrl
    settingsRepository.transportType = TransportType.WebSockets
}
```

## 📊 **成功标准**

修复成功的标准：
- ✅ 应用重启后无需重新绑定设备
- ✅ WebSocket连接自动恢复
- ✅ 语音功能正常工作
- ✅ 日志显示配置恢复成功

## 🚨 **故障排除**

### 编译问题
```bash
# 检查Java版本
java -version

# 检查Android SDK
echo $ANDROID_HOME

# 清理Gradle缓存
./gradlew clean
rm -rf .gradle
```

### 安装问题
```bash
# 卸载旧版本
adb uninstall info.dourok.voicebot

# 重新安装
adb install app/build/outputs/apk/debug/app-debug.apk
```

### 运行时问题
```bash
# 查看详细日志
adb logcat | grep -E "(WebSocket|ActivationManager|ChatViewModel|ERROR)"

# 检查应用崩溃
adb logcat | grep "AndroidRuntime"
```

## 📞 **需要帮助时**

如果遇到问题，请提供：
1. 编译日志（如果编译失败）
2. 安装日志（如果安装失败）
3. 应用运行日志（关键部分）
4. 测试脚本输出结果

**立即开始第一步：编译代码！** 🚀 