# 🏗️ 阶段二：架构优化方案

## 🎯 目标
建立模块化、可扩展的OTA和设备管理架构，实现企业级的自动化绑定流程。

## ⏰ 时间估算：2-3天（16-24小时）

### 2.1 OTA客户端架构重构（6小时）

#### 问题
当前OTA实现过于耦合，缺乏统一的状态管理和错误处理。

#### 解决方案：模块化OTA架构

```kotlin
// core/ota/OTARepository.kt - 统一OTA数据层
@Singleton
class OTARepository @Inject constructor(
    private val otaService: OTAService,
    private val deviceIdManager: DeviceIdManager,
    private val configManager: DeviceConfigManager
) {
    
    suspend fun checkDeviceStatus(): OTAResult {
        val deviceId = deviceIdManager.getStableDeviceId()
        val request = createStandardOTARequest(deviceId)
        
        return try {
            val response = otaService.checkDeviceActivation(request)
            parseOTAResponse(response)
        } catch (e: Exception) {
            OTAResult.NetworkError(e.message ?: "Network request failed")
        }
    }
    
    private fun createStandardOTARequest(deviceId: String) = OTARequest(
        macAddress = deviceId,
        clientId = "android-${Build.VERSION.SDK_INT}",
        application = ApplicationInfo(
            name = "xiaozhi-android",
            version = BuildConfig.VERSION_NAME,
            buildTime = BuildConfig.BUILD_TIME
        ),
        deviceInfo = AndroidDeviceInfo(
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL,
            osVersion = Build.VERSION.RELEASE,
            chipModel = "android-${Build.VERSION.SDK_INT}"
        )
    )
    
    private fun parseOTAResponse(response: OTAResponse): OTAResult {
        return when {
            response.hasActivation() -> {
                OTAResult.RequiresBinding(
                    activationCode = response.activation.code,
                    message = response.activation.message,
                    validUntil = System.currentTimeMillis() + 3600000 // 1小时有效
                )
            }
            response.hasWebSocket() -> {
                OTAResult.Activated(
                    websocketUrl = response.websocket.url,
                    serverTime = response.serverTime?.timestamp
                )
            }
            else -> {
                OTAResult.InvalidResponse("服务器响应格式无效")
            }
        }
    }
}

// core/ota/OTAResult.kt - 标准化结果类型
sealed class OTAResult {
    data class Activated(
        val websocketUrl: String,
        val serverTime: Long?
    ) : OTAResult()
    
    data class RequiresBinding(
        val activationCode: String,
        val message: String,
        val validUntil: Long
    ) : OTAResult()
    
    data class NetworkError(val message: String) : OTAResult()
    data class InvalidResponse(val message: String) : OTAResult()
    
    val isSuccess: Boolean get() = this is Activated || this is RequiresBinding
    val isActivated: Boolean get() = this is Activated
    val requiresBinding: Boolean get() = this is RequiresBinding
}
```

### 2.2 设备生命周期管理（4小时）

#### 问题
设备状态变化缺乏统一管理，导致状态不一致。

#### 解决方案：设备生命周期管理器

```kotlin
// core/device/DeviceLifecycleManager.kt
@Singleton 
class DeviceLifecycleManager @Inject constructor(
    private val otaRepository: OTARepository,
    private val bindingManager: DeviceBindingManager,
    private val settingsRepository: SettingsRepository
) {
    
    private val _deviceState = MutableStateFlow(DeviceState.UNKNOWN)
    val deviceState: StateFlow<DeviceState> = _deviceState.asStateFlow()
    
    private val _bindingEvents = MutableSharedFlow<BindingEvent>()
    val bindingEvents: SharedFlow<BindingEvent> = _bindingEvents.asSharedFlow()
    
    suspend fun initializeDevice(): DeviceInitResult {
        _deviceState.value = DeviceState.INITIALIZING
        
        return try {
            // 1. 验证设备身份
            val deviceId = validateDeviceIdentity()
            
            // 2. 检查绑定状态
            val otaResult = otaRepository.checkDeviceStatus()
            
            // 3. 处理不同状态
            when (otaResult) {
                is OTAResult.Activated -> {
                    handleActivatedDevice(otaResult)
                }
                is OTAResult.RequiresBinding -> {
                    handleUnboundDevice(otaResult)
                }
                else -> {
                    handleErrorState(otaResult)
                }
            }
        } catch (e: Exception) {
            _deviceState.value = DeviceState.ERROR
            DeviceInitResult.Failed(e.message ?: "设备初始化失败")
        }
    }
    
    private suspend fun handleActivatedDevice(result: OTAResult.Activated): DeviceInitResult {
        _deviceState.value = DeviceState.ACTIVATED
        
        // 配置WebSocket连接
        settingsRepository.transportType = TransportType.WebSockets
        settingsRepository.webSocketUrl = result.websocketUrl
        
        // 更新本地绑定状态
        bindingManager.updateBindingStatus(true, result.websocketUrl)
        
        _bindingEvents.emit(BindingEvent.DeviceActivated(result.websocketUrl))
        
        return DeviceInitResult.Success(DeviceStatus.READY_FOR_SERVICE)
    }
    
    private suspend fun handleUnboundDevice(result: OTAResult.RequiresBinding): DeviceInitResult {
        _deviceState.value = DeviceState.REQUIRES_BINDING
        
        // 保存激活码信息
        bindingManager.saveActivationInfo(
            code = result.activationCode,
            message = result.message,
            validUntil = result.validUntil
        )
        
        _bindingEvents.emit(BindingEvent.BindingRequired(result.activationCode))
        
        return DeviceInitResult.RequiresBinding(result.activationCode, result.message)
    }
    
    suspend fun retryBinding(): BindingRetryResult {
        val currentState = _deviceState.value
        
        if (currentState != DeviceState.REQUIRES_BINDING) {
            return BindingRetryResult.NotRequired
        }
        
        _deviceState.value = DeviceState.CHECKING_BINDING
        
        return when (val result = otaRepository.checkDeviceStatus()) {
            is OTAResult.Activated -> {
                handleActivatedDevice(result)
                BindingRetryResult.Success
            }
            is OTAResult.RequiresBinding -> {
                _deviceState.value = DeviceState.REQUIRES_BINDING
                BindingRetryResult.StillRequired(result.activationCode)
            }
            else -> {
                _deviceState.value = DeviceState.ERROR
                BindingRetryResult.Failed(result.toString())
            }
        }
    }
}

// core/device/DeviceState.kt
enum class DeviceState {
    UNKNOWN,
    INITIALIZING,
    REQUIRES_BINDING,
    CHECKING_BINDING,
    ACTIVATED,
    ERROR
}

sealed class BindingEvent {
    data class DeviceActivated(val websocketUrl: String) : BindingEvent()
    data class BindingRequired(val activationCode: String) : BindingEvent()
    data class BindingCompleted(val deviceId: String) : BindingEvent()
    data class BindingFailed(val error: String) : BindingEvent()
}
```

### 2.3 自动化绑定流程（6小时）

#### 问题
当前需要用户手动操作多个步骤，体验不佳。

#### 解决方案：智能绑定工作流

```kotlin
// core/binding/AutoBindingWorkflow.kt
@Singleton
class AutoBindingWorkflow @Inject constructor(
    private val deviceLifecycleManager: DeviceLifecycleManager,
    private val bindingUIManager: BindingUIManager,
    private val notificationManager: BindingNotificationManager
) {
    
    private val _workflowState = MutableStateFlow(WorkflowState.IDLE)
    val workflowState: StateFlow<WorkflowState> = _workflowState.asStateFlow()
    
    suspend fun startAutoBinding(): AutoBindingResult {
        _workflowState.value = WorkflowState.STARTING
        
        // 1. 设备初始化检查
        val initResult = deviceLifecycleManager.initializeDevice()
        
        return when (initResult) {
            is DeviceInitResult.Success -> {
                _workflowState.value = WorkflowState.COMPLETED
                AutoBindingResult.AlreadyBound
            }
            
            is DeviceInitResult.RequiresBinding -> {
                _workflowState.value = WorkflowState.WAITING_FOR_USER
                handleUserBindingFlow(initResult.activationCode, initResult.message)
            }
            
            is DeviceInitResult.Failed -> {
                _workflowState.value = WorkflowState.FAILED
                AutoBindingResult.Failed(initResult.error)
            }
        }
    }
    
    private suspend fun handleUserBindingFlow(
        activationCode: String, 
        message: String
    ): AutoBindingResult {
        
        // 显示绑定UI
        val userAction = bindingUIManager.showBindingDialog(
            BindingDialogConfig(
                activationCode = activationCode,
                message = message,
                autoRetryEnabled = true,
                timeoutMinutes = 10
            )
        )
        
        return when (userAction) {
            is UserBindingAction.StartBinding -> {
                handleAssistedBinding(activationCode)
            }
            is UserBindingAction.ManualBinding -> {
                startManualBindingFlow(activationCode)
            }
            is UserBindingAction.Cancelled -> {
                _workflowState.value = WorkflowState.CANCELLED
                AutoBindingResult.Cancelled
            }
        }
    }
    
    private suspend fun handleAssistedBinding(activationCode: String): AutoBindingResult {
        _workflowState.value = WorkflowState.ASSISTED_BINDING
        
        // 1. 自动打开管理面板
        bindingUIManager.openManagementPanel(activationCode)
        
        // 2. 复制激活码到剪贴板
        bindingUIManager.copyToClipboard(activationCode)
        
        // 3. 显示引导通知
        notificationManager.showBindingGuide(activationCode)
        
        // 4. 启动后台轮询检查
        return startBindingPolling(activationCode)
    }
    
    private suspend fun startBindingPolling(activationCode: String): AutoBindingResult {
        val maxAttempts = 30 // 5分钟，每10秒检查一次
        var attempts = 0
        
        while (attempts < maxAttempts && _workflowState.value == WorkflowState.ASSISTED_BINDING) {
            delay(10000) // 等待10秒
            
            val retryResult = deviceLifecycleManager.retryBinding()
            
            when (retryResult) {
                is BindingRetryResult.Success -> {
                    _workflowState.value = WorkflowState.COMPLETED
                    notificationManager.showBindingSuccess()
                    return AutoBindingResult.BindingCompleted
                }
                is BindingRetryResult.StillRequired -> {
                    attempts++
                    // 继续轮询
                }
                is BindingRetryResult.Failed -> {
                    _workflowState.value = WorkflowState.FAILED
                    return AutoBindingResult.Failed(retryResult.error)
                }
                BindingRetryResult.NotRequired -> {
                    // 状态异常，重新开始
                    return startAutoBinding()
                }
            }
        }
        
        // 超时
        _workflowState.value = WorkflowState.TIMEOUT
        return AutoBindingResult.Timeout
    }
}

// core/binding/BindingUIManager.kt
@Singleton
class BindingUIManager @Inject constructor(
    private val context: Context,
    private val clipboardManager: ClipboardManager
) {
    
    suspend fun showBindingDialog(config: BindingDialogConfig): UserBindingAction {
        return suspendCancellableCoroutine { continuation ->
            // 在主线程显示对话框
            CoroutineScope(Dispatchers.Main).launch {
                // 实现自定义绑定对话框
                val dialog = createBindingDialog(config) { action ->
                    if (continuation.isActive) {
                        continuation.resume(action)
                    }
                }
                dialog.show()
            }
        }
    }
    
    fun openManagementPanel(activationCode: String) {
        val managementUrl = buildManagementUrl(activationCode)
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(managementUrl)).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
    }
    
    fun copyToClipboard(text: String) {
        val clip = ClipData.newPlainText("激活码", text)
        clipboardManager.setPrimaryClip(clip)
    }
    
    private fun buildManagementUrl(activationCode: String): String {
        val baseUrl = "http://47.122.144.73:8002"
        val agentId = "6bf580ad09cf4b1e8bd332dafb9e6d30"
        return "$baseUrl/#/device-management?agentId=$agentId&code=$activationCode"
    }
}

enum class WorkflowState {
    IDLE,
    STARTING,
    WAITING_FOR_USER,
    ASSISTED_BINDING,
    MANUAL_BINDING,
    COMPLETED,
    FAILED,
    CANCELLED,
    TIMEOUT
}
```

### 2.4 WebSocket连接管理优化（4小时）

#### 问题
WebSocket连接缺乏智能重连和状态管理。

#### 解决方案：企业级连接管理

```kotlin
// core/websocket/WebSocketConnectionManager.kt
@Singleton
class WebSocketConnectionManager @Inject constructor(
    private val deviceLifecycleManager: DeviceLifecycleManager,
    private val networkMonitor: NetworkMonitor,
    private val settingsRepository: SettingsRepository
) {
    
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private var reconnectJob: Job? = null
    private var currentProtocol: WebsocketProtocol? = null
    
    suspend fun establishConnection(): ConnectionResult {
        val deviceState = deviceLifecycleManager.deviceState.value
        
        if (deviceState != DeviceState.ACTIVATED) {
            return ConnectionResult.DeviceNotReady("设备未激活，请先完成绑定")
        }
        
        val websocketUrl = settingsRepository.webSocketUrl
        if (websocketUrl.isNullOrEmpty()) {
            return ConnectionResult.ConfigurationError("WebSocket URL未配置")
        }
        
        return try {
            _connectionState.value = ConnectionState.CONNECTING
            
            val protocol = createWebSocketProtocol(websocketUrl)
            val success = protocol.openAudioChannel()
            
            if (success) {
                currentProtocol = protocol
                _connectionState.value = ConnectionState.CONNECTED
                startNetworkMonitoring()
                ConnectionResult.Success(protocol)
            } else {
                _connectionState.value = ConnectionState.FAILED
                ConnectionResult.ConnectionFailed("WebSocket握手失败")
            }
            
        } catch (e: Exception) {
            _connectionState.value = ConnectionState.FAILED
            ConnectionResult.ConnectionFailed("连接异常: ${e.message}")
        }
    }
    
    private fun startNetworkMonitoring() {
        reconnectJob = CoroutineScope(Dispatchers.IO).launch {
            networkMonitor.networkState.collect { networkState ->
                when (networkState) {
                    NetworkState.LOST -> {
                        _connectionState.value = ConnectionState.NETWORK_LOST
                    }
                    NetworkState.AVAILABLE -> {
                        if (_connectionState.value == ConnectionState.NETWORK_LOST) {
                            // 网络恢复，尝试重连
                            attemptReconnection()
                        }
                    }
                }
            }
        }
    }
    
    private suspend fun attemptReconnection() {
        _connectionState.value = ConnectionState.RECONNECTING
        
        // 指数退避重连策略
        val maxRetries = 5
        var retryDelay = 1000L // 1秒
        
        repeat(maxRetries) { attempt ->
            try {
                val result = establishConnection()
                if (result is ConnectionResult.Success) {
                    return // 重连成功
                }
            } catch (e: Exception) {
                Log.w(TAG, "重连尝试 ${attempt + 1} 失败: ${e.message}")
            }
            
            if (attempt < maxRetries - 1) {
                delay(retryDelay)
                retryDelay = minOf(retryDelay * 2, 30000L) // 最多30秒
            }
        }
        
        _connectionState.value = ConnectionState.FAILED
    }
    
    fun disconnect() {
        reconnectJob?.cancel()
        currentProtocol?.closeAudioChannel()
        currentProtocol = null
        _connectionState.value = ConnectionState.DISCONNECTED
    }
}

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    NETWORK_LOST,
    FAILED
}

sealed class ConnectionResult {
    data class Success(val protocol: WebsocketProtocol) : ConnectionResult()
    data class DeviceNotReady(val reason: String) : ConnectionResult()
    data class ConfigurationError(val message: String) : ConnectionResult()
    data class ConnectionFailed(val error: String) : ConnectionResult()
}
```

### 2.5 统一状态管理（4小时）

#### 问题
各模块状态分散，缺乏统一的状态同步机制。

#### 解决方案：中央状态管理器

```kotlin
// core/state/AppStateManager.kt
@Singleton
class AppStateManager @Inject constructor(
    private val deviceLifecycleManager: DeviceLifecycleManager,
    private val connectionManager: WebSocketConnectionManager,
    private val autoBindingWorkflow: AutoBindingWorkflow
) {
    
    private val _appState = MutableStateFlow(AppState.INITIALIZING)
    val appState: StateFlow<AppState> = _appState.asStateFlow()
    
    // 组合各模块状态
    private val _uiState = combine(
        deviceLifecycleManager.deviceState,
        connectionManager.connectionState,
        autoBindingWorkflow.workflowState
    ) { deviceState, connectionState, workflowState ->
        AppUIState(
            deviceState = deviceState,
            connectionState = connectionState,
            workflowState = workflowState,
            isReady = deviceState == DeviceState.ACTIVATED && 
                     connectionState == ConnectionState.CONNECTED
        )
    }.stateIn(
        scope = CoroutineScope(Dispatchers.Default),
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = AppUIState()
    )
    
    val uiState: StateFlow<AppUIState> = _uiState
    
    suspend fun initializeApp(): AppInitResult {
        _appState.value = AppState.INITIALIZING
        
        try {
            // 1. 设备初始化
            val deviceInit = deviceLifecycleManager.initializeDevice()
            
            when (deviceInit) {
                is DeviceInitResult.Success -> {
                    // 2. 建立连接
                    val connectionResult = connectionManager.establishConnection()
                    
                    if (connectionResult is ConnectionResult.Success) {
                        _appState.value = AppState.READY
                        return AppInitResult.Ready
                    } else {
                        _appState.value = AppState.CONNECTION_FAILED
                        return AppInitResult.ConnectionFailed(connectionResult.toString())
                    }
                }
                
                is DeviceInitResult.RequiresBinding -> {
                    _appState.value = AppState.REQUIRES_BINDING
                    return AppInitResult.RequiresBinding(deviceInit.activationCode)
                }
                
                is DeviceInitResult.Failed -> {
                    _appState.value = AppState.DEVICE_ERROR
                    return AppInitResult.DeviceError(deviceInit.error)
                }
            }
            
        } catch (e: Exception) {
            _appState.value = AppState.FATAL_ERROR
            return AppInitResult.FatalError(e.message ?: "应用初始化失败")
        }
    }
    
    suspend fun startBindingProcess(): BindingProcessResult {
        if (_appState.value != AppState.REQUIRES_BINDING) {
            return BindingProcessResult.InvalidState("当前状态不允许启动绑定流程")
        }
        
        _appState.value = AppState.BINDING_IN_PROGRESS
        
        val bindingResult = autoBindingWorkflow.startAutoBinding()
        
        return when (bindingResult) {
            AutoBindingResult.AlreadyBound -> {
                // 重新初始化应用
                initializeApp()
                BindingProcessResult.Completed
            }
            AutoBindingResult.BindingCompleted -> {
                // 建立连接
                val connectionResult = connectionManager.establishConnection()
                if (connectionResult is ConnectionResult.Success) {
                    _appState.value = AppState.READY
                    BindingProcessResult.Completed
                } else {
                    _appState.value = AppState.CONNECTION_FAILED
                    BindingProcessResult.ConnectionFailed(connectionResult.toString())
                }
            }
            is AutoBindingResult.Failed -> {
                _appState.value = AppState.BINDING_FAILED
                BindingProcessResult.Failed(bindingResult.error)
            }
            AutoBindingResult.Cancelled -> {
                _appState.value = AppState.REQUIRES_BINDING
                BindingProcessResult.Cancelled
            }
            AutoBindingResult.Timeout -> {
                _appState.value = AppState.BINDING_TIMEOUT
                BindingProcessResult.Timeout
            }
        }
    }
}

// 应用状态枚举
enum class AppState {
    INITIALIZING,
    REQUIRES_BINDING,
    BINDING_IN_PROGRESS,
    BINDING_FAILED,
    BINDING_TIMEOUT,
    CONNECTION_FAILED,
    DEVICE_ERROR,
    READY,
    FATAL_ERROR
}

// UI状态数据类
data class AppUIState(
    val deviceState: DeviceState = DeviceState.UNKNOWN,
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val workflowState: WorkflowState = WorkflowState.IDLE,
    val isReady: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)
```

## 📋 实施计划

### Day 1: 核心架构搭建
- [ ] 实现OTARepository和标准化数据模型
- [ ] 创建DeviceLifecycleManager
- [ ] 建立基础的状态管理框架

### Day 2: 自动化绑定流程
- [ ] 实现AutoBindingWorkflow
- [ ] 创建BindingUIManager
- [ ] 集成通知和用户引导

### Day 3: 连接管理和集成测试
- [ ] 实现WebSocketConnectionManager
- [ ] 完成AppStateManager集成
- [ ] 端到端测试和优化

## 🎯 预期收益

**架构收益**：
- 🏗️ 模块化设计，易于维护和扩展
- 🔄 统一状态管理，减少状态不一致问题
- 🛡️ 完善的错误处理和恢复机制
- 📊 清晰的数据流和依赖关系

**用户体验收益**：
- 🚀 自动化程度大幅提升
- 📱 智能引导减少用户困惑
- 🔗 可靠的连接管理
- ⏱️ 更快的初始化和恢复时间

**开发效率收益**：
- 🧪 更容易进行单元测试
- 🔧 模块化便于并行开发
- 📈 清晰的监控和日志记录
- 🎯 标准化的接口设计

---
**这个架构将为后续功能扩展提供坚实的基础！** 🏗️ 