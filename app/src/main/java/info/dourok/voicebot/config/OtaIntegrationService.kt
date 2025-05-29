package info.dourok.voicebot.config

import android.util.Log
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.OtaResult
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * OTA集成服务
 * 安全地将OTA配置集成到现有系统，确保不影响STT功能
 */
@Singleton
class OtaIntegrationService @Inject constructor(
    private val otaConfigManager: OtaConfigManager,
    private val settingsRepository: SettingsRepository
) {
    companion object {
        private const val TAG = "OtaIntegrationService"
        private const val AUTO_REFRESH_INTERVAL_MS = 30000L // 30秒自动刷新间隔
        private const val BINDING_CHECK_INTERVAL_MS = 5000L // 5秒绑定检查间隔
    }
    
    private var otaConfigJob: Job? = null
    private var autoRefreshJob: Job? = null
    private var bindingCheckJob: Job? = null
    private var currentOtaResult: OtaResult? = null
    
    // 绑定状态流
    private val _bindingState = MutableStateFlow<BindingState>(BindingState.Unknown)
    val bindingState: StateFlow<BindingState> = _bindingState.asStateFlow()
    
    // 自动跳转事件流
    private val _navigationEvents = MutableStateFlow<NavigationEvent?>(null)
    val navigationEvents: StateFlow<NavigationEvent?> = _navigationEvents.asStateFlow()

    /**
     * 初始化OTA配置（非阻塞，不影响STT启动）
     */
    fun initializeOtaConfig(scope: CoroutineScope) {
        Log.i(TAG, "🔧 初始化OTA配置服务...")
        
        otaConfigJob = scope.launch {
            try {
                // 1. 首先尝试使用缓存的配置
                val cachedWebSocketUrl = otaConfigManager.getCachedWebSocketUrl()
                if (cachedWebSocketUrl != null) {
                    Log.i(TAG, "✅ 使用缓存的WebSocket配置: $cachedWebSocketUrl")
                    settingsRepository.webSocketUrl = cachedWebSocketUrl
                    settingsRepository.deviceId = otaConfigManager.getDeviceId()
                    _bindingState.value = BindingState.Bound(cachedWebSocketUrl)
                    
                    // 🔧 修改1: 缓存配置存在时也要主动刷新验证状态
                    Log.i(TAG, "🔄 主动验证缓存配置的有效性...")
                    val refreshResult = otaConfigManager.fetchOtaConfig()
                    if (refreshResult != null) {
                        currentOtaResult = refreshResult
                        processOtaResult(refreshResult)
                    }
                    return@launch
                }
                
                // 2. 如果没有缓存，尝试获取新配置（后台进行）
                Log.i(TAG, "📡 后台获取新的OTA配置...")
                val otaResult = otaConfigManager.fetchOtaConfig()
                
                if (otaResult != null) {
                    currentOtaResult = otaResult
                    processOtaResult(otaResult)
                } else {
                    Log.w(TAG, "⚠️ OTA配置获取失败，使用默认配置")
                    useDefaultConfig()
                }
                
                // 🔧 修改1: 启动自动刷新机制
                startAutoRefresh(scope)
                
            } catch (e: Exception) {
                Log.e(TAG, "❌ OTA配置初始化异常", e)
                useDefaultConfig()
            }
        }
    }
    
    /**
     * 🔧 修改1: 启动自动刷新机制
     */
    private fun startAutoRefresh(scope: CoroutineScope) {
        autoRefreshJob = scope.launch {
            while (isActive) {
                delay(AUTO_REFRESH_INTERVAL_MS)
                try {
                    Log.d(TAG, "🔄 执行自动刷新检查...")
                    val refreshResult = otaConfigManager.fetchOtaConfig()
                    if (refreshResult != null) {
                        val oldState = _bindingState.value
                        currentOtaResult = refreshResult
                        processOtaResult(refreshResult)
                        
                        // 检查状态是否发生变化
                        val newState = _bindingState.value
                        if (oldState != newState) {
                            Log.i(TAG, "🔔 绑定状态已更新: $oldState -> $newState")
                        }
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "⚠️ 自动刷新失败: ${e.message}")
                }
            }
        }
        Log.i(TAG, "✅ 自动刷新机制已启动，间隔: ${AUTO_REFRESH_INTERVAL_MS / 1000}秒")
    }
    
    /**
     * 🔧 修改1&2: 启动绑定状态监控（用于需要绑定的设备）
     */
    fun startBindingMonitor(scope: CoroutineScope, activationCode: String) {
        Log.i(TAG, "🔍 启动绑定状态监控，激活码: $activationCode")
        
        bindingCheckJob = scope.launch {
            var checkCount = 0
            while (isActive && checkCount < 60) { // 最多检查5分钟
                delay(BINDING_CHECK_INTERVAL_MS)
                checkCount++
                
                try {
                    Log.d(TAG, "🔍 检查绑定状态... ($checkCount/60)")
                    val refreshResult = otaConfigManager.fetchOtaConfig()
                    
                    if (refreshResult != null) {
                        currentOtaResult = refreshResult
                        
                        // 检查是否已绑定
                        if (refreshResult.isActivated) {
                            Log.i(TAG, "🎉 检测到设备已绑定成功！")
                            processOtaResult(refreshResult)
                            
                            // 🔧 修改2: 绑定成功后自动跳转到语音功能
                            _navigationEvents.value = NavigationEvent.NavigateToChat
                            break
                        } else if (refreshResult.needsActivation) {
                            val newCode = refreshResult.activationCode
                            if (newCode != null && newCode != activationCode) {
                                Log.i(TAG, "🔄 激活码已更新: $activationCode -> $newCode")
                                _bindingState.value = BindingState.NeedsBinding(newCode)
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "⚠️ 绑定状态检查失败: ${e.message}")
                }
            }
            
            if (checkCount >= 60) {
                Log.w(TAG, "⏰ 绑定状态监控超时")
                _bindingState.value = BindingState.CheckTimeout
            }
        }
    }
    
    /**
     * 停止绑定监控
     */
    fun stopBindingMonitor() {
        bindingCheckJob?.cancel()
        bindingCheckJob = null
        Log.i(TAG, "🛑 绑定状态监控已停止")
    }

    /**
     * 处理OTA配置结果
     */
    private fun processOtaResult(otaResult: OtaResult) {
        Log.i(TAG, "🔍 处理OTA配置结果...")
        
        when {
            otaResult.isActivated -> {
                // 设备已激活，使用WebSocket配置
                val websocketUrl = otaResult.websocketUrl
                if (websocketUrl != null) {
                    Log.i(TAG, "✅ 设备已激活，应用WebSocket配置: $websocketUrl")
                    settingsRepository.webSocketUrl = websocketUrl
                    settingsRepository.deviceId = otaConfigManager.getDeviceId()
                    settingsRepository.isUsingOtaConfig = true
                    _bindingState.value = BindingState.Bound(websocketUrl)
                } else {
                    Log.w(TAG, "⚠️ 设备已激活但无WebSocket配置")
                    useDefaultConfig()
                }
            }
            
            otaResult.needsActivation -> {
                // 设备需要激活
                val activationCode = otaResult.activationCode
                Log.i(TAG, "🔑 设备需要激活，激活码: $activationCode")
                
                // 这里不阻塞STT功能，设备激活将在UI层处理
                settingsRepository.deviceId = otaConfigManager.getDeviceId()
                settingsRepository.isUsingOtaConfig = false
                _bindingState.value = BindingState.NeedsBinding(activationCode!!)
                
                // 使用默认配置让STT先工作
                useDefaultConfig()
            }
            
            else -> {
                Log.w(TAG, "⚠️ OTA响应格式异常")
                _bindingState.value = BindingState.Error("OTA响应格式异常")
                useDefaultConfig()
            }
        }
    }
    
    /**
     * 使用默认配置（确保STT功能正常）
     */
    private fun useDefaultConfig() {
        Log.i(TAG, "🔧 使用默认WebSocket配置")
        
        // 使用硬编码的默认配置，确保STT能正常工作
        val defaultWebSocketUrl = "ws://47.122.144.73:8000/xiaozhi/v1/"
        settingsRepository.webSocketUrl = defaultWebSocketUrl
        settingsRepository.deviceId = otaConfigManager.getDeviceId()
        settingsRepository.isUsingOtaConfig = false
        
        Log.i(TAG, "✅ 默认配置已应用: $defaultWebSocketUrl")
    }
    
    /**
     * 获取当前WebSocket URL（STT使用）
     */
    fun getCurrentWebSocketUrl(): String? {
        val url = settingsRepository.webSocketUrl
        Log.d(TAG, "📡 当前WebSocket URL: $url")
        return url
    }
    
    /**
     * 获取当前设备ID
     */
    fun getCurrentDeviceId(): String {
        val deviceId = settingsRepository.deviceId ?: otaConfigManager.getDeviceId()
        settingsRepository.deviceId = deviceId
        return deviceId
    }
    
    /**
     * 手动刷新OTA配置（用于UI操作）
     */
    suspend fun refreshOtaConfig(): OtaResult? {
        Log.i(TAG, "🔄 手动刷新OTA配置...")
        
        return try {
            val otaResult = otaConfigManager.fetchOtaConfig()
            if (otaResult != null) {
                currentOtaResult = otaResult
                processOtaResult(otaResult)
            }
            otaResult
        } catch (e: Exception) {
            Log.e(TAG, "❌ 手动刷新OTA配置失败", e)
            null
        }
    }
    
    /**
     * 获取当前OTA结果（用于UI显示）
     */
    fun getCurrentOtaResult(): OtaResult? = currentOtaResult
    
    /**
     * 检查是否正在使用OTA配置
     */
    fun isUsingOtaConfig(): Boolean = settingsRepository.isUsingOtaConfig
    
    /**
     * 清理资源
     */
    fun cleanup() {
        otaConfigJob?.cancel()
        autoRefreshJob?.cancel()
        bindingCheckJob?.cancel()
        otaConfigJob = null
        autoRefreshJob = null
        bindingCheckJob = null
        Log.i(TAG, "🧹 OTA集成服务已清理")
    }
    
    /**
     * 清除导航事件（UI消费后调用）
     */
    fun clearNavigationEvent() {
        _navigationEvents.value = null
    }
}

/**
 * 绑定状态枚举
 */
sealed class BindingState {
    object Unknown : BindingState()
    data class NeedsBinding(val activationCode: String) : BindingState()
    data class Bound(val websocketUrl: String) : BindingState()
    data class Error(val message: String) : BindingState()
    object CheckTimeout : BindingState()
}

/**
 * 导航事件
 */
sealed class NavigationEvent {
    object NavigateToChat : NavigationEvent()
} 