# 🚀 并行开发执行计划

## 📊 并行开发策略（选项C）

基于您的需求，我们将同时推进三个阶段，采用并行开发模式：

### 🎯 并行开发优势：
- ⚡ **加速开发**：多条线并行推进
- 🔄 **快速迭代**：每天都有可见成果  
- 🛡️ **风险分散**：单个模块问题不影响整体进度
- 📈 **价值最大化**：优先级灵活调整

## 📅 三阶段并行时间线

### 第1天：多线启动
```
上午（4小时）：
├── 线程A：验证当前STT功能 + 开始手动绑定优化（2小时）
├── 线程B：OTA客户端架构设计（2小时）  
└── 线程C：ESP32 vs Android差异分析完善（已完成）

下午（4小时）：
├── 线程A：设备管理优化实现（2小时）
├── 线程B：网络层基础实现（2小时）
└── 集成测试：各模块接口对接验证
```

### 第2天：深化实现
```
上午（4小时）：
├── 线程A：用户体验提升（绑定状态UI）（2小时）
├── 线程B：OTA服务接口实现（2小时）

下午（4小时）：
├── 线程A：配置管理持久化（2小时）  
├── 线程B：自动绑定流程核心逻辑（2小时）
```

### 第3天：集成优化
```
上午（4小时）：
├── 线程A：手动绑定方案完善和测试（2小时）
├── 线程B：智能绑定UI集成（2小时）

下午（4小时）：
├── 统一管理界面设计（2小时）
└── 完整流程集成测试（2小时）
```

## 🔄 立即开始：第一步执行

### 立即执行任务列表：

#### ✅ 任务1：验证当前STT功能（30分钟）
```bash
# 1. 测试设备绑定状态
python3 test_your_device_id.py

# 2. 清除应用数据（手动在设备上）
# 设置 → 应用管理 → VoiceBot → 存储 → 清除数据

# 3. 重新编译运行
./gradlew app:assembleDebug
```

#### 🔥 任务2：并行启动 - 设备配置管理器（90分钟）
创建设备配置管理的核心组件：

##### 2.1 创建DeviceConfigManager
```kotlin
// app/src/main/java/info/dourok/voicebot/config/DeviceConfigManager.kt
class DeviceConfigManager(private val context: Context) {
    private val dataStore = context.createDataStore("device_config")
    
    companion object {
        val DEVICE_ID_KEY = stringPreferencesKey("device_id")
        val BINDING_STATUS_KEY = booleanPreferencesKey("binding_status")
        val LAST_CHECK_TIME_KEY = longPreferencesKey("last_check_time")
        val ACTIVATION_CODE_KEY = stringPreferencesKey("activation_code")
    }
    
    suspend fun getDeviceId(): String {
        return dataStore.data.first()[DEVICE_ID_KEY] ?: "00:11:22:33:44:55"
    }
    
    suspend fun setDeviceId(deviceId: String) {
        dataStore.edit { prefs ->
            prefs[DEVICE_ID_KEY] = deviceId
        }
    }
    
    suspend fun getBindingStatus(): Boolean {
        return dataStore.data.first()[BINDING_STATUS_KEY] ?: false
    }
    
    suspend fun updateBindingStatus(isbound: Boolean) {
        dataStore.edit { prefs ->
            prefs[BINDING_STATUS_KEY] = isbound
            prefs[LAST_CHECK_TIME_KEY] = System.currentTimeMillis()
        }
    }
}
```

##### 2.2 创建绑定状态检查器
```kotlin  
// app/src/main/java/info/dourok/voicebot/binding/BindingStatusChecker.kt
class BindingStatusChecker(
    private val deviceConfigManager: DeviceConfigManager,
    private val context: Context
) {
    
    suspend fun checkBindingStatus(): BindingCheckResult {
        val deviceId = deviceConfigManager.getDeviceId()
        
        return try {
            val response = performOTACheck(deviceId)
            
            when {
                response.has("activation") -> {
                    val activationCode = response.getJSONObject("activation").getString("code")
                    BindingCheckResult.Unbound(deviceId, activationCode)
                }
                response.has("websocket") -> {
                    val websocketUrl = response.getJSONObject("websocket").getString("url")
                    BindingCheckResult.Bound(deviceId, websocketUrl)
                }
                else -> {
                    BindingCheckResult.Error("Invalid server response")
                }
            }
        } catch (e: Exception) {
            BindingCheckResult.Error("Network error: ${e.message}")
        }
    }
    
    private suspend fun performOTACheck(deviceId: String): JSONObject {
        // 使用现有的OTA检查逻辑
        // ... 实现细节
    }
}

sealed class BindingCheckResult {
    data class Bound(val deviceId: String, val websocketUrl: String) : BindingCheckResult()
    data class Unbound(val deviceId: String, val activationCode: String) : BindingCheckResult()
    data class Error(val message: String) : BindingCheckResult()
}
```

#### 🎨 任务3：并行启动 - 设备配置UI（60分钟）
创建设备配置界面：

```kotlin
// app/src/main/java/info/dourok/voicebot/ui/config/DeviceConfigScreen.kt
@Composable
fun DeviceConfigScreen(
    viewModel: DeviceConfigViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "设备配置",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        // 设备ID配置卡片
        DeviceIdConfigCard(
            deviceId = uiState.deviceId,
            onDeviceIdChange = viewModel::updateDeviceId,
            onSave = viewModel::saveDeviceId
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 绑定状态卡片  
        BindingStatusCard(
            bindingStatus = uiState.bindingStatus,
            lastCheckTime = uiState.lastCheckTime,
            onRefresh = viewModel::checkBindingStatus,
            onManualBind = viewModel::showManualBindDialog
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // 激活码显示（如果需要绑定）
        if (uiState.activationCode != null) {
            ActivationCodeCard(
                activationCode = uiState.activationCode!!,
                onCopyCode = viewModel::copyActivationCode,
                onOpenManagement = viewModel::openManagementPanel
            )
        }
    }
}
```

## 🎯 今日目标完成标准

### ✅ 第1天结束时应达成：
1. **STT功能验证**：确认当前修正是否生效
2. **设备配置管理器**：DeviceConfigManager基础功能完成
3. **绑定状态检查器**：BindingStatusChecker能够正常工作  
4. **设备配置UI**：基础界面可用
5. **OTA架构设计**：核心接口和数据模型定义完成

### 📊 成功指标：
- ✅ 应用启动时能够显示当前设备ID
- ✅ 可以手动修改设备ID并保存
- ✅ 绑定状态检查功能正常
- ✅ 激活码能够正确显示
- ✅ 为明天的深度开发做好准备

## 🚀 立即开始执行

选择您希望优先开始的任务：

### 选项1：验证STT功能（推荐先做）
```bash
cd foobar && python3 test_your_device_id.py
```

### 选项2：开始代码实现（并行进行）
我可以立即为您创建上述核心组件的代码文件

### 选项3：两者并行
一边验证STT，一边开始代码架构设计

**请告诉我您希望从哪个任务开始，我将立即为您提供具体的实现代码！** 🎯 