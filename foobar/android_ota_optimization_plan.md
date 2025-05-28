# 🚀 Android OTA优化方案

## 📊 基于ESP32对比的优化策略

基于ESP32硬件设备的OTA设计，我们需要为Android应用制定专门的优化方案。

## 🎯 核心优化目标

### 1. 设备标识稳定性
**问题**：Android应用重装后设备ID可能改变  
**解决方案**：多层设备标识策略

### 2. 绑定状态持久性  
**问题**：应用数据清除导致绑定丢失  
**解决方案**：云端绑定状态同步

### 3. 用户体验优化
**问题**：ESP32自动化vs Android手动操作  
**解决方案**：智能绑定流程

## 🔧 具体实施方案

### 第一阶段：设备标识优化（2小时）

#### 1.1 多层设备ID策略
```kotlin
class DeviceIdentityManager(private val context: Context) {
    
    // 优先级1：用户自定义ID（最高优先级）
    suspend fun getCustomDeviceId(): String? {
        return dataStore.getStringValue("custom_device_id")
    }
    
    // 优先级2：Android设备指纹（中等稳定性）
    fun getDeviceFingerprint(): String {
        val androidId = Settings.Secure.getString(
            context.contentResolver, 
            Settings.Secure.ANDROID_ID
        )
        val buildInfo = "${Build.MANUFACTURER}_${Build.MODEL}_${Build.ID}"
        return generateMacFromFingerprint("$androidId-$buildInfo")
    }
    
    // 优先级3：应用级UUID（应用独有）
    suspend fun getAppUniqueId(): String {
        return dataStore.getStringValue("app_uuid") 
            ?: UUID.randomUUID().toString().also {
                dataStore.saveStringValue("app_uuid", it)
            }
    }
    
    // 最终设备ID获取策略
    suspend fun getFinalDeviceId(): String {
        // 1. 优先使用自定义ID
        getCustomDeviceId()?.let { return it }
        
        // 2. 使用设备指纹生成稳定ID
        val fingerprint = getDeviceFingerprint()
        if (fingerprint.isNotEmpty()) {
            return fingerprint
        }
        
        // 3. 降级到应用UUID
        return getAppUniqueId()
    }
    
    private fun generateMacFromFingerprint(fingerprint: String): String {
        val hash = fingerprint.hashCode()
        return String.format(
            "%02x:%02x:%02x:%02x:%02x:%02x",
            (hash ushr 24) and 0xFF,
            (hash ushr 16) and 0xFF,
            (hash ushr 8) and 0xFF,
            hash and 0xFF,
            0x00, // 固定后两位避免冲突
            0x01
        )
    }
}
```

#### 1.2 设备信息增强
```kotlin
class EnhancedDeviceInfo {
    
    fun generateAndroidDeviceInfo(): DeviceInfo {
        return DeviceInfo(
            version = 2,
            flash_size = getAppStorageSize(),
            psram_size = getAvailableMemory(),
            mac_address = deviceIdentityManager.getFinalDeviceId(),
            uuid = getAppInstanceId(),
            chip_model_name = "android-${Build.VERSION.SDK_INT}",
            chip_info = getAndroidChipInfo(),
            application = getAppInfo(),
            partition_table = getAndroidPartitionInfo(),
            ota = OTA("app_update"),
            board = getAndroidBoardInfo()
        )
    }
    
    private fun getAndroidChipInfo(): ChipInfo {
        return ChipInfo(
            model = 1000 + Build.VERSION.SDK_INT, // Android API Level
            cores = Runtime.getRuntime().availableProcessors(),
            revision = BuildConfig.VERSION_CODE,
            features = getAndroidFeatures()
        )
    }
    
    private fun getAndroidFeatures(): Int {
        var features = 0
        if (hasWiFi()) features = features or 0x01
        if (hasBluetooth()) features = features or 0x02
        if (hasMicrophone()) features = features or 0x04
        if (hasSpeaker()) features = features or 0x08
        return features
    }
}
```

### 第二阶段：云端绑定同步（3小时）

#### 2.1 绑定状态管理器
```kotlin
class BindingStateManager(
    private val otaService: OTAService,
    private val localStore: DataStore<Preferences>
) {
    
    data class BindingState(
        val deviceId: String,
        val isbound: Boolean,
        val bindTime: Long,
        val lastSyncTime: Long,
        val activationCode: String?
    )
    
    // 本地绑定状态
    suspend fun getLocalBindingState(): BindingState? {
        return localStore.data.first().let { prefs ->
            val deviceId = prefs[DEVICE_ID_KEY] ?: return null
            BindingState(
                deviceId = deviceId,
                isbound = prefs[IS_BOUND_KEY] ?: false,
                bindTime = prefs[BIND_TIME_KEY] ?: 0L,
                lastSyncTime = prefs[LAST_SYNC_KEY] ?: 0L,
                activationCode = prefs[ACTIVATION_CODE_KEY]
            )
        }
    }
    
    // 云端绑定状态检查
    suspend fun checkRemoteBindingState(deviceId: String): BindingResult {
        return try {
            val response = otaService.checkDeviceStatus(
                deviceId = deviceId,
                clientId = "android-app",
                request = createOTARequest(deviceId)
            )
            
            if (response.activation != null) {
                BindingResult.Unbound(response.activation.code)
            } else if (response.websocket != null) {
                BindingResult.Bound(response.websocket.url)
            } else {
                BindingResult.Error("Invalid response")
            }
        } catch (e: Exception) {
            BindingResult.Error(e.message ?: "Network error")
        }
    }
    
    // 智能绑定同步
    suspend fun smartBindingSync(): SyncResult {
        val localState = getLocalBindingState()
        val deviceId = deviceIdentityManager.getFinalDeviceId()
        
        // 如果本地无状态，直接检查远程
        if (localState == null) {
            return handleFirstTimeBinding(deviceId)
        }
        
        // 如果设备ID发生变化，需要重新绑定
        if (localState.deviceId != deviceId) {
            return handleDeviceIdChange(localState, deviceId)
        }
        
        // 定期同步验证
        val timeSinceLastSync = System.currentTimeMillis() - localState.lastSyncTime
        if (timeSinceLastSync > SYNC_INTERVAL_MS) {
            return handlePeriodicSync(localState)
        }
        
        return SyncResult.NoSyncNeeded(localState)
    }
    
    private suspend fun handleFirstTimeBinding(deviceId: String): SyncResult {
        val remoteState = checkRemoteBindingState(deviceId)
        return when (remoteState) {
            is BindingResult.Bound -> {
                // 设备已在云端绑定，更新本地状态
                saveLocalBindingState(deviceId, true, remoteState.websocketUrl)
                SyncResult.SyncedFromRemote(deviceId, true)
            }
            is BindingResult.Unbound -> {
                // 需要绑定，保存激活码
                saveLocalBindingState(deviceId, false, null, remoteState.activationCode)
                SyncResult.BindingRequired(deviceId, remoteState.activationCode)
            }
            is BindingResult.Error -> {
                SyncResult.SyncError(remoteState.error)
            }
        }
    }
}
```

#### 2.2 自动绑定流程
```kotlin
class AutoBindingFlow(
    private val bindingStateManager: BindingStateManager,
    private val uiManager: BindingUIManager
) {
    
    suspend fun executeAutoBinding(): AutoBindingResult {
        // 1. 智能同步绑定状态
        val syncResult = bindingStateManager.smartBindingSync()
        
        return when (syncResult) {
            is SyncResult.NoSyncNeeded -> {
                AutoBindingResult.AlreadyBound(syncResult.state.deviceId)
            }
            
            is SyncResult.SyncedFromRemote -> {
                if (syncResult.isBound) {
                    AutoBindingResult.SyncedAndBound(syncResult.deviceId)
                } else {
                    AutoBindingResult.SyncedButNeedBinding(syncResult.deviceId)
                }
            }
            
            is SyncResult.BindingRequired -> {
                // 需要用户操作绑定
                handleUserBinding(syncResult.deviceId, syncResult.activationCode)
            }
            
            is SyncResult.SyncError -> {
                AutoBindingResult.Error(syncResult.error)
            }
        }
    }
    
    private suspend fun handleUserBinding(
        deviceId: String, 
        activationCode: String
    ): AutoBindingResult {
        
        // 显示绑定UI
        val userAction = uiManager.showBindingDialog(
            deviceId = deviceId,
            activationCode = activationCode,
            onBindConfirm = { confirmBinding(deviceId) },
            onSkip = { skipBinding() }
        )
        
        return when (userAction) {
            is UserBindingAction.Confirmed -> {
                AutoBindingResult.UserBound(deviceId)
            }
            is UserBindingAction.Skipped -> {
                AutoBindingResult.BindingSkipped(deviceId)
            }
            is UserBindingAction.Failed -> {
                AutoBindingResult.BindingFailed(userAction.error)
            }
        }
    }
}
```

### 第三阶段：智能UI集成（3小时）

#### 3.1 绑定状态UI组件
```kotlin
@Composable
fun DeviceBindingStatusCard(
    bindingState: BindingState?,
    onRefresh: () -> Unit,
    onManualBind: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "设备绑定状态",
                    style = MaterialTheme.typography.headlineSmall
                )
                
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, contentDescription = "刷新")
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            when {
                bindingState == null -> {
                    UnknownStatusContent(onManualBind)
                }
                bindingState.isbound -> {
                    BoundStatusContent(bindingState)
                }
                else -> {
                    UnboundStatusContent(bindingState, onManualBind)
                }
            }
        }
    }
}

@Composable
private fun BoundStatusContent(bindingState: BindingState) {
    Row(
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            Icons.Default.CheckCircle,
            contentDescription = "已绑定",
            tint = Color.Green
        )
        Spacer(modifier = Modifier.width(8.dp))
        Column {
            Text("设备已绑定")
            Text(
                "设备ID: ${bindingState.deviceId}",
                style = MaterialTheme.typography.bodySmall,
                color = Color.Gray
            )
        }
    }
}

@Composable
private fun UnboundStatusContent(
    bindingState: BindingState,
    onManualBind: () -> Unit
) {
    Column {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.Warning,
                contentDescription = "未绑定",
                tint = Color.Orange
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("设备未绑定")
        }
        
        bindingState.activationCode?.let { code ->
            Spacer(modifier = Modifier.height(8.dp))
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(
                    modifier = Modifier.padding(12.dp)
                ) {
                    Text(
                        "激活码: $code",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "请在管理面板中输入此激活码完成绑定",
                        style = MaterialTheme.typography.bodySmall
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Button(
                            onClick = { /* 复制激活码 */ }
                        ) {
                            Text("复制激活码")
                        }
                        
                        OutlinedButton(
                            onClick = onManualBind
                        ) {
                            Text("手动绑定")
                        }
                    }
                }
            }
        }
    }
}
```

#### 3.2 自动绑定入口集成
```kotlin
class MainActivity : ComponentActivity() {
    
    private val autoBindingFlow by lazy {
        (application as VoiceBotApplication).autoBindingFlow
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 启动时执行自动绑定
        lifecycleScope.launch {
            handleAutoBinding()
        }
        
        setContent {
            VoiceBotTheme {
                MainScreen()
            }
        }
    }
    
    private suspend fun handleAutoBinding() {
        val result = autoBindingFlow.executeAutoBinding()
        
        when (result) {
            is AutoBindingResult.AlreadyBound -> {
                Log.i("AutoBinding", "设备已绑定: ${result.deviceId}")
                // 直接启动语音服务
            }
            
            is AutoBindingResult.BindingRequired -> {
                Log.i("AutoBinding", "需要用户绑定: ${result.activationCode}")
                // UI自动显示绑定对话框
            }
            
            is AutoBindingResult.Error -> {
                Log.e("AutoBinding", "绑定检查失败: ${result.error}")
                // 显示错误提示，但允许用户继续使用
            }
        }
    }
}
```

## 📊 实施时间线

### 今天（3小时）：
- ✅ **第一阶段**：设备标识优化（2小时）
- ✅ **测试验证**：设备ID稳定性测试（1小时）

### 明天（6小时）：
- ✅ **第二阶段**：云端绑定同步（3小时）
- ✅ **第三阶段**：智能UI集成（3小时）

### 第三天（2小时）：
- ✅ **集成测试**：完整流程测试（1小时）
- ✅ **用户体验优化**：细节打磨（1小时）

## 🎯 预期效果

### 用户体验：
- 📱 **首次使用**：自动检测绑定状态，智能引导
- 🔄 **重装应用**：自动恢复绑定状态（如设备指纹未变）
- ⚙️ **手动管理**：提供设备ID配置和手动绑定选项

### 技术收益：
- 🛡️ **稳定性**：多层设备标识策略
- 🔗 **兼容性**：与ESP32 OTA接口完全兼容
- 🚀 **可扩展性**：为未来功能扩展奠定基础

---
**这个优化方案将Android应用的OTA体验提升到接近ESP32硬件设备的自动化水平！** 🎉 

# Android OTA优化详细方案

## 问题诊断

### 当前OTA实现的核心问题

1. **请求格式不标准**
   - Android使用`mac_address`字段，但服务器期望`macAddress`
   - 缺少必要的`application`对象结构
   - `chip_model_name`应为`chipModelName`

2. **设备ID生成不稳定**
   ```kotlin
   // 问题代码 - DeviceInfo.kt
   val DEFAULT_DEVICE_ID = "00:11:22:33:44:55" // 固定值，所有用户相同
   ```

3. **错误处理不完善**
   ```kotlin
   // 当前错误处理 - Ota.kt
   catch (e: Exception) {
       Log.e(TAG, "HTTP request failed: ${e.message}")
       return@withContext false  // 丢失了错误详情
   }
   ```

## 解决方案

### 1. 标准化设备ID管理器

```kotlin
@Singleton
class DeviceIdManager @Inject constructor(
    private val context: Context,
    private val dataStore: DataStore<Preferences>
) {
    companion object {
        private val DEVICE_ID_KEY = stringPreferencesKey("stable_device_id")
        private val CUSTOM_ID_KEY = stringPreferencesKey("custom_device_id")
        private const val TAG = "DeviceIdManager"
    }
    
    /**
     * 获取稳定的设备ID，格式为MAC地址样式：xx:xx:xx:xx:xx:xx
     * 优先级：用户自定义ID > 已保存ID > 基于Android ID生成的新ID
     */
    suspend fun getStableDeviceId(): String {
        // 1. 检查用户自定义ID
        val customId = dataStore.data.first()[CUSTOM_ID_KEY]
        if (!customId.isNullOrEmpty() && isValidMacFormat(customId)) {
            Log.d(TAG, "使用用户自定义ID: $customId")
            return customId
        }
        
        // 2. 检查已保存的ID
        val savedId = dataStore.data.first()[DEVICE_ID_KEY]
        if (!savedId.isNullOrEmpty()) {
            Log.d(TAG, "使用已保存的ID: $savedId")
            return savedId
        }
        
        // 3. 生成新的稳定ID
        val newId = generateStableId()
        dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = newId
        }
        Log.i(TAG, "生成新的设备ID: $newId")
        return newId
    }
    
    /**
     * 基于Android ID和设备指纹生成稳定的MAC格式ID
     */
    private fun generateStableId(): String {
        try {
            val androidId = Settings.Secure.getString(
                context.contentResolver, 
                Settings.Secure.ANDROID_ID
            ) ?: "unknown"
            
            val deviceFingerprint = "${Build.MANUFACTURER}-${Build.MODEL}-${Build.FINGERPRINT}"
            val combined = "$androidId-$deviceFingerprint"
            
            // 使用SHA-256生成稳定哈希
            val hash = MessageDigest.getInstance("SHA-256")
                .digest(combined.toByteArray())
            
            // 取前6个字节转换为MAC格式
            return hash.take(6)
                .joinToString(":") { "%02x".format(it) }
                .uppercase()
        } catch (e: Exception) {
            Log.w(TAG, "生成设备ID失败，使用fallback方案: ${e.message}")
            // Fallback: 基于时间戳的伪随机ID
            val timestamp = System.currentTimeMillis()
            val random = Random(timestamp).nextBytes(6)
            return random.joinToString(":") { "%02x".format(it) }
        }
    }
    
    /**
     * 允许用户设置自定义设备ID（用于测试或特殊需求）
     */
    suspend fun setCustomDeviceId(customId: String): Boolean {
        if (!isValidMacFormat(customId)) {
            Log.w(TAG, "无效的MAC格式: $customId")
            return false
        }
        
        dataStore.edit { preferences ->
            preferences[CUSTOM_ID_KEY] = customId.uppercase()
        }
        Log.i(TAG, "设置自定义设备ID: $customId")
        return true
    }
    
    /**
     * 清除自定义ID，恢复使用自动生成的ID
     */
    suspend fun clearCustomDeviceId() {
        dataStore.edit { preferences ->
            preferences.remove(CUSTOM_ID_KEY)
        }
        Log.i(TAG, "已清除自定义设备ID")
    }
    
    /**
     * 验证MAC地址格式
     */
    private fun isValidMacFormat(mac: String): Boolean {
        val macPattern = Regex("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        return macPattern.matches(mac)
    }
    
    /**
     * 获取设备信息摘要（用于调试）
     */
    suspend fun getDeviceInfoSummary(): Map<String, String> {
        return mapOf(
            "deviceId" to getStableDeviceId(),
            "androidId" to (Settings.Secure.getString(
                context.contentResolver, 
                Settings.Secure.ANDROID_ID
            ) ?: "unknown"),
            "manufacturer" to Build.MANUFACTURER,
            "model" to Build.MODEL,
            "hasCustomId" to (dataStore.data.first()[CUSTOM_ID_KEY] != null).toString()
        )
    }
}
```

### 2. 标准化OTA请求格式

```kotlin
// 修改 Ota.kt 的请求构建方法
class Ota @Inject constructor(
    private val context: Context,
    private val deviceInfo: DeviceInfo,
    private val deviceIdManager: DeviceIdManager
) {
    
    /**
     * 构建标准化的OTA请求体
     * 符合服务器端期望的格式
     */
    private suspend fun buildStandardOtaRequest(): JSONObject {
        val deviceId = deviceIdManager.getStableDeviceId()
        
        return JSONObject().apply {
            // 应用信息
            put("application", JSONObject().apply {
                put("version", deviceInfo.application.version)
                put("name", "xiaozhi-android")
                put("compile_time", SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                    .format(Date()))
            })
            
            // 设备信息 - 使用标准字段名
            put("macAddress", deviceId)  // 注意：使用驼峰命名
            put("chipModelName", "android")  // 注意：使用驼峰命名
            
            // 板子信息
            put("board", JSONObject().apply {
                put("type", "android")
                put("manufacturer", Build.MANUFACTURER)
                put("model", Build.MODEL)
                put("version", Build.VERSION.RELEASE)
            })
            
            // 客户端信息
            put("uuid", deviceInfo.uuid)
            put("build_time", System.currentTimeMillis() / 1000)
        }
    }
    
    /**
     * 改进的版本检查方法
     */
    suspend fun checkVersion(checkVersionUrl: String): OTACheckResult = withContext(Dispatchers.IO) {
        Log.i(TAG, "开始OTA版本检查: $checkVersionUrl")
        
        try {
            // 验证URL
            if (checkVersionUrl.length < 10 || !checkVersionUrl.startsWith("http")) {
                return@withContext OTACheckResult.Error("无效的OTA URL: $checkVersionUrl")
            }
            
            // 构建请求
            val deviceId = deviceIdManager.getStableDeviceId()
            val requestBody = buildStandardOtaRequest()
            
            val request = Request.Builder()
                .url(checkVersionUrl)
                .post(requestBody.toString().toRequestBody("application/json".toMediaTypeOrNull()))
                .addHeader("Content-Type", "application/json")
                .addHeader("Device-Id", deviceId)
                .addHeader("Client-Id", deviceInfo.uuid)
                .addHeader("X-Language", "Chinese")
                .build()
            
            Log.d(TAG, "OTA请求详情:")
            Log.d(TAG, "URL: $checkVersionUrl")
            Log.d(TAG, "Device-Id: $deviceId")
            Log.d(TAG, "Client-Id: ${deviceInfo.uuid}")
            Log.d(TAG, "请求体: ${requestBody.toString(2)}")
            
            // 发送请求
            val response = client.newCall(request).execute()
            
            if (!response.isSuccessful) {
                val errorBody = response.body?.string() ?: "空响应"
                Log.e(TAG, "OTA请求失败: ${response.code} - ${response.message}")
                Log.e(TAG, "错误响应: $errorBody")
                return@withContext OTACheckResult.Error("服务器错误(${response.code}): $errorBody")
            }
            
            val responseBody = response.body?.string() ?: run {
                Log.e(TAG, "OTA响应体为空")
                return@withContext OTACheckResult.Error("服务器响应为空")
            }
            
            Log.i(TAG, "OTA响应成功: $responseBody")
            
            // 解析响应
            parseOTAResponse(responseBody)
            
        } catch (e: Exception) {
            Log.e(TAG, "OTA检查异常", e)
            val errorMessage = when (e) {
                is SocketTimeoutException -> "网络连接超时，请检查网络设置"
                is ConnectException -> "无法连接到服务器，请检查服务器地址"
                is UnknownHostException -> "无法解析服务器地址，请检查网络"
                else -> "网络错误：${e.message}"
            }
            OTACheckResult.Error(errorMessage)
        }
    }
    
    /**
     * 解析OTA响应
     */
    private fun parseOTAResponse(responseBody: String): OTACheckResult {
        return try {
            val json = JSONObject(responseBody)
            
            // 检查是否包含激活码（需要绑定）
            if (json.has("activation")) {
                val activationObj = json.getJSONObject("activation")
                val activationCode = activationObj.getString("code")
                val message = activationObj.optString("message", "")
                
                Log.i(TAG, "设备需要绑定，激活码: $activationCode")
                OTACheckResult.NeedBinding(activationCode, message)
            }
            // 检查是否包含WebSocket配置（已绑定）
            else if (json.has("websocket")) {
                val websocketObj = json.getJSONObject("websocket")
                val websocketUrl = websocketObj.getString("url")
                
                // 解析固件信息（如果有）
                val firmware = if (json.has("firmware")) {
                    val firmwareObj = json.getJSONObject("firmware")
                    FirmwareInfo(
                        version = firmwareObj.getString("version"),
                        url = firmwareObj.optString("url", ""),
                        size = firmwareObj.optLong("size", 0),
                        sha256 = firmwareObj.optString("sha256", "")
                    )
                } else null
                
                // 解析服务器时间（如果有）
                val serverTime = if (json.has("server_time")) {
                    val timeObj = json.getJSONObject("server_time")
                    ServerTimeInfo(
                        timestamp = timeObj.getLong("timestamp"),
                        timezoneOffset = timeObj.optInt("timezone_offset", 0)
                    )
                } else null
                
                Log.i(TAG, "设备已绑定，WebSocket URL: $websocketUrl")
                OTACheckResult.Success(
                    websocketUrl = websocketUrl,
                    firmware = firmware,
                    serverTime = serverTime
                )
            }
            else {
                Log.e(TAG, "OTA响应格式无效，缺少activation或websocket字段")
                OTACheckResult.Error("服务器响应格式无效")
            }
        } catch (e: Exception) {
            Log.e(TAG, "解析OTA响应失败", e)
            OTACheckResult.Error("响应解析失败：${e.message}")
        }
    }
}

/**
 * OTA检查结果
 */
sealed class OTACheckResult {
    data class Success(
        val websocketUrl: String,
        val firmware: FirmwareInfo? = null,
        val serverTime: ServerTimeInfo? = null
    ) : OTACheckResult()
    
    data class NeedBinding(
        val activationCode: String,
        val message: String = ""
    ) : OTACheckResult()
    
    data class Error(val message: String) : OTACheckResult()
}

data class FirmwareInfo(
    val version: String,
    val url: String,
    val size: Long,
    val sha256: String
)

data class ServerTimeInfo(
    val timestamp: Long,
    val timezoneOffset: Int
)
```

### 3. 智能重试机制

```kotlin
@Singleton
class RetryManager @Inject constructor() {
    companion object {
        private const val TAG = "RetryManager"
    }
    
    /**
     * 指数退避重试策略
     */
    suspend fun <T> retryWithExponentialBackoff(
        maxRetries: Int = 3,
        initialDelayMs: Long = 1000,
        maxDelayMs: Long = 16000,
        backoffMultiplier: Double = 2.0,
        jitterFactor: Double = 0.1,
        operation: suspend () -> T
    ): T {
        var lastException: Exception? = null
        var delay = initialDelayMs
        
        repeat(maxRetries) { attempt ->
            try {
                Log.d(TAG, "执行操作，尝试次数: ${attempt + 1}/$maxRetries")
                return operation()
            } catch (e: Exception) {
                lastException = e
                Log.w(TAG, "操作失败，尝试次数: ${attempt + 1}/$maxRetries", e)
                
                if (attempt == maxRetries - 1) {
                    Log.e(TAG, "所有重试均失败，抛出最后一个异常")
                    throw e
                }
                
                // 计算下次重试延迟（包含抖动）
                val jitter = (delay * jitterFactor * Random.nextDouble(-1.0, 1.0)).toLong()
                val actualDelay = delay + jitter
                
                Log.d(TAG, "等待 ${actualDelay}ms 后重试")
                delay(actualDelay)
                
                // 更新延迟时间
                delay = minOf((delay * backoffMultiplier).toLong(), maxDelayMs)
            }
        }
        
        throw lastException ?: Exception("重试失败")
    }
    
    /**
     * 根据异常类型决定是否应该重试
     */
    fun shouldRetry(exception: Exception): Boolean {
        return when (exception) {
            is SocketTimeoutException -> true
            is ConnectException -> true
            is IOException -> true
            is HttpException -> exception.code() in 500..599 // 服务器错误可重试
            else -> false
        }
    }
    
    /**
     * 智能重试（根据异常类型决定是否重试）
     */
    suspend fun <T> smartRetry(
        maxRetries: Int = 3,
        operation: suspend () -> T
    ): T {
        return retryWithExponentialBackoff(maxRetries = maxRetries) {
            try {
                operation()
            } catch (e: Exception) {
                if (!shouldRetry(e)) {
                    Log.d(TAG, "异常不适合重试，直接抛出: ${e.javaClass.simpleName}")
                    throw e
                }
                throw e
            }
        }
    }
}
```

### 4. 配置验证器

```kotlin
@Singleton
class ConfigValidator @Inject constructor() {
    companion object {
        private const val TAG = "ConfigValidator"
    }
    
    /**
     * 验证OTA URL格式
     */
    fun validateOtaUrl(url: String): ValidationResult {
        if (url.isBlank()) {
            return ValidationResult.Error("OTA URL不能为空")
        }
        
        if (url.length < 10) {
            return ValidationResult.Error("OTA URL过短")
        }
        
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            return ValidationResult.Error("OTA URL必须以http://或https://开头")
        }
        
        try {
            URL(url) // 验证URL格式
        } catch (e: MalformedURLException) {
            return ValidationResult.Error("OTA URL格式无效: ${e.message}")
        }
        
        return ValidationResult.Success
    }
    
    /**
     * 验证WebSocket URL格式
     */
    fun validateWebSocketUrl(url: String): ValidationResult {
        if (url.isBlank()) {
            return ValidationResult.Error("WebSocket URL不能为空")
        }
        
        if (!url.startsWith("ws://") && !url.startsWith("wss://")) {
            return ValidationResult.Error("WebSocket URL必须以ws://或wss://开头")
        }
        
        try {
            URL(url.replace("ws://", "http://").replace("wss://", "https://"))
        } catch (e: MalformedURLException) {
            return ValidationResult.Error("WebSocket URL格式无效: ${e.message}")
        }
        
        return ValidationResult.Success
    }
    
    /**
     * 验证设备ID格式
     */
    fun validateDeviceId(deviceId: String): ValidationResult {
        if (deviceId.isBlank()) {
            return ValidationResult.Error("设备ID不能为空")
        }
        
        val macPattern = Regex("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        if (!macPattern.matches(deviceId)) {
            return ValidationResult.Error("设备ID必须是MAC地址格式 (xx:xx:xx:xx:xx:xx)")
        }
        
        return ValidationResult.Success
    }
    
    /**
     * 验证激活码格式
     */
    fun validateActivationCode(code: String): ValidationResult {
        if (code.isBlank()) {
            return ValidationResult.Error("激活码不能为空")
        }
        
        if (code.length != 6) {
            return ValidationResult.Error("激活码必须是6位数字")
        }
        
        if (!code.matches(Regex("^\\d{6}$"))) {
            return ValidationResult.Error("激活码只能包含数字")
        }
        
        return ValidationResult.Success
    }
}

sealed class ValidationResult {
    object Success : ValidationResult()
    data class Error(val message: String) : ValidationResult()
    
    val isValid: Boolean
        get() = this is Success
        
    val errorMessage: String?
        get() = if (this is Error) message else null
}
```

## 测试验证

### 单元测试示例

```kotlin
@ExperimentalCoroutinesApi
class DeviceIdManagerTest {
    
    @Mock
    private lateinit var context: Context
    
    @Mock
    private lateinit var dataStore: DataStore<Preferences>
    
    private lateinit var deviceIdManager: DeviceIdManager
    
    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        deviceIdManager = DeviceIdManager(context, dataStore)
    }
    
    @Test
    fun `getStableDeviceId should return consistent ID`() = runTest {
        // Given
        val preferences = MutablePreferences()
        whenever(dataStore.data).thenReturn(flowOf(preferences))
        
        // When
        val firstCall = deviceIdManager.getStableDeviceId()
        val secondCall = deviceIdManager.getStableDeviceId()
        
        // Then
        assertEquals(firstCall, secondCall)
        assertTrue(isValidMacFormat(firstCall))
    }
    
    @Test
    fun `setCustomDeviceId should reject invalid format`() = runTest {
        // When
        val result = deviceIdManager.setCustomDeviceId("invalid-format")
        
        // Then
        assertFalse(result)
    }
    
    private fun isValidMacFormat(mac: String): Boolean {
        val macPattern = Regex("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        return macPattern.matches(mac)
    }
}
```

### 集成测试检查清单

- [ ] 新设备首次OTA检查返回激活码
- [ ] 已绑定设备OTA检查返回WebSocket URL
- [ ] 网络异常时重试机制生效
- [ ] 设备ID在应用重装后保持一致
- [ ] 自定义设备ID功能正常工作
- [ ] 配置验证器正确识别无效输入
- [ ] 错误信息对用户友好且有指导性

## 部署建议

### 渐进式部署策略

1. **第一阶段**：仅修复设备ID和请求格式
2. **第二阶段**：添加重试机制和配置验证
3. **第三阶段**：完整的错误处理和用户体验优化

### 配置开关

```kotlin
// 在Application类中添加功能开关
object FeatureFlags {
    const val USE_NEW_DEVICE_ID_MANAGER = true
    const val USE_STANDARDIZED_OTA_FORMAT = true
    const val ENABLE_SMART_RETRY = true
    const val ENABLE_CONFIG_VALIDATION = true
}
```

这样可以在出现问题时快速回滚到旧版本实现。 