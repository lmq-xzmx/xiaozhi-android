package info.dourok.voicebot.binding

import android.content.Context
import android.util.Log
import info.dourok.voicebot.config.DeviceConfigManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 智能绑定管理器
 * 负责管理整个设备绑定生命周期，包括：
 * - 设备初始化检查
 * - 自动获取激活码
 * - 引导用户完成绑定
 * - 绑定状态验证
 * - 自动重试机制
 */
@Singleton
class SmartBindingManager @Inject constructor(
    private val bindingStatusChecker: BindingStatusChecker,
    private val deviceConfigManager: DeviceConfigManager,
    private val context: Context
) {
    companion object {
        private const val TAG = "SmartBindingManager"
        private const val POLLING_INTERVAL_MS = 15000L // 15秒轮询间隔
        private const val MAX_POLLING_ATTEMPTS = 20 // 最多轮询5分钟
    }
    
    private val _bindingState = MutableStateFlow<BindingState>(BindingState.Unknown)
    val bindingState: StateFlow<BindingState> = _bindingState.asStateFlow()
    
    private val _bindingEvents = MutableStateFlow<BindingEvent?>(null)
    val bindingEvents: StateFlow<BindingEvent?> = _bindingEvents.asStateFlow()
    
    /**
     * 初始化设备绑定流程
     * 这是应用启动时的主要入口点
     */
    suspend fun initializeDeviceBinding(): BindingInitResult {
        Log.i(TAG, "🚀 开始设备绑定初始化流程")
        _bindingState.value = BindingState.Initializing
        
        try {
            // 1. 检查本地绑定状态
            val locallyBound = deviceConfigManager.getBindingStatus()
            val deviceId = deviceConfigManager.getDeviceId()
            
            Log.d(TAG, "📱 设备ID: $deviceId")
            Log.d(TAG, "💾 本地绑定状态: $locallyBound")
            
            // 2. 执行OTA检查（无论本地状态如何都要检查）
            when (val result = bindingStatusChecker.checkBindingStatus()) {
                is BindingCheckResult.Bound -> {
                    Log.i(TAG, "✅ 设备已绑定成功！WebSocket URL: ${result.websocketUrl}")
                    _bindingState.value = BindingState.Bound(result.websocketUrl)
                    _bindingEvents.value = BindingEvent.DeviceReady(result.websocketUrl)
                    return BindingInitResult.AlreadyBound(result.websocketUrl)
                }
                
                is BindingCheckResult.Unbound -> {
                    Log.i(TAG, "📋 设备需要绑定，激活码: ${result.activationCode}")
                    _bindingState.value = BindingState.NeedsBinding(result.activationCode)
                    _bindingEvents.value = BindingEvent.ActivationCodeReceived(result.activationCode)
                    return BindingInitResult.NeedsBinding(result.activationCode)
                }
                
                is BindingCheckResult.Error -> {
                    Log.e(TAG, "❌ 绑定状态检查失败: ${result.message}")
                    _bindingState.value = BindingState.Error(result.message)
                    _bindingEvents.value = BindingEvent.ErrorOccurred(result.message)
                    return BindingInitResult.Error(result.message)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "💥 设备绑定初始化异常", e)
            val errorMessage = "初始化失败: ${e.message}"
            _bindingState.value = BindingState.Error(errorMessage)
            _bindingEvents.value = BindingEvent.ErrorOccurred(errorMessage)
            return BindingInitResult.Error(errorMessage)
        }
    }
    
    /**
     * 开始智能绑定流程
     * 当设备需要绑定时调用
     */
    suspend fun startSmartBinding(activationCode: String): SmartBindingResult {
        Log.i(TAG, "🎯 开始智能绑定流程，激活码: $activationCode")
        _bindingState.value = BindingState.BindingInProgress(activationCode)
        _bindingEvents.value = BindingEvent.BindingStarted(activationCode)
        
        return try {
            // 1. 提供用户指导
            _bindingEvents.value = BindingEvent.ShowUserGuide(
                activationCode = activationCode,
                managementUrl = buildManagementUrl(),
                instructions = buildBindingInstructions(activationCode)
            )
            
            // 2. 开始后台轮询检查
            startBindingPolling(activationCode)
            
        } catch (e: Exception) {
            Log.e(TAG, "智能绑定流程异常", e)
            val errorMessage = "绑定流程失败: ${e.message}"
            _bindingState.value = BindingState.Error(errorMessage)
            _bindingEvents.value = BindingEvent.ErrorOccurred(errorMessage)
            SmartBindingResult.Failed(errorMessage)
        }
    }
    
    /**
     * 开始后台轮询检查绑定状态
     */
    private suspend fun startBindingPolling(activationCode: String): SmartBindingResult {
        Log.i(TAG, "🔄 开始绑定状态轮询检查")
        var attempts = 0
        
        while (attempts < MAX_POLLING_ATTEMPTS) {
            attempts++
            
            Log.d(TAG, "🔍 绑定状态检查 ($attempts/$MAX_POLLING_ATTEMPTS)")
            _bindingEvents.value = BindingEvent.PollingUpdate(attempts, MAX_POLLING_ATTEMPTS)
            
            try {
                when (val result = bindingStatusChecker.refreshBindingStatus()) {
                    is BindingCheckResult.Bound -> {
                        Log.i(TAG, "🎉 绑定成功！WebSocket URL: ${result.websocketUrl}")
                        _bindingState.value = BindingState.Bound(result.websocketUrl)
                        _bindingEvents.value = BindingEvent.BindingCompleted(result.websocketUrl)
                        return SmartBindingResult.Success(result.websocketUrl)
                    }
                    
                    is BindingCheckResult.Unbound -> {
                        // 仍需绑定，继续轮询
                        Log.d(TAG, "⏳ 仍需绑定，继续等待用户操作")
                        if (result.activationCode != activationCode) {
                            // 激活码变化了，更新状态
                            _bindingState.value = BindingState.BindingInProgress(result.activationCode)
                            _bindingEvents.value = BindingEvent.ActivationCodeChanged(result.activationCode)
                        }
                    }
                    
                    is BindingCheckResult.Error -> {
                        Log.w(TAG, "⚠️ 轮询检查出错，将重试: ${result.message}")
                        // 网络错误不算失败，继续重试
                    }
                }
                
                // 等待下次检查
                if (attempts < MAX_POLLING_ATTEMPTS) {
                    delay(POLLING_INTERVAL_MS)
                }
                
            } catch (e: Exception) {
                Log.w(TAG, "轮询检查异常，将重试", e)
            }
        }
        
        // 轮询超时
        Log.w(TAG, "⏰ 绑定轮询超时")
        _bindingState.value = BindingState.PollingTimeout(activationCode)
        _bindingEvents.value = BindingEvent.BindingTimeout
        return SmartBindingResult.Timeout
    }
    
    /**
     * 手动刷新绑定状态
     */
    suspend fun refreshBindingStatus(): BindingCheckResult {
        Log.d(TAG, "🔄 手动刷新绑定状态")
        return bindingStatusChecker.refreshBindingStatus()
    }
    
    /**
     * 停止当前绑定流程
     */
    fun stopBinding() {
        Log.d(TAG, "⏹️ 停止绑定流程")
        _bindingState.value = BindingState.Stopped
        _bindingEvents.value = BindingEvent.BindingStopped
    }
    
    /**
     * 重置绑定状态
     */
    suspend fun resetBinding() {
        Log.d(TAG, "🔄 重置绑定状态")
        deviceConfigManager.updateBindingStatus(false)
        deviceConfigManager.setActivationCode(null)
        deviceConfigManager.setWebsocketUrl(null)
        _bindingState.value = BindingState.Unknown
        _bindingEvents.value = BindingEvent.BindingReset
    }
    
    private fun buildManagementUrl(): String {
        // 使用服务器基础URL构建管理面板URL
        return "http://47.122.144.73:8002/#/home"
    }
    
    private fun buildBindingInstructions(activationCode: String): List<String> {
        return listOf(
            "📱 激活码已自动复制到剪贴板",
            "🌐 点击下方按钮打开管理面板",
            "➕ 在管理面板点击\"新增设备\"",
            "📝 粘贴激活码: $activationCode",
            "✅ 完成绑定，应用将自动检测",
            "🔄 无需手动刷新，请耐心等待"
        )
    }
}

/**
 * 绑定状态枚举
 */
sealed class BindingState {
    object Unknown : BindingState()
    object Initializing : BindingState()
    data class NeedsBinding(val activationCode: String) : BindingState()
    data class BindingInProgress(val activationCode: String) : BindingState()
    data class Bound(val websocketUrl: String) : BindingState()
    data class PollingTimeout(val activationCode: String) : BindingState()
    data class Error(val message: String) : BindingState()
    object Stopped : BindingState()
}

/**
 * 绑定事件
 */
sealed class BindingEvent {
    data class DeviceReady(val websocketUrl: String) : BindingEvent()
    data class ActivationCodeReceived(val activationCode: String) : BindingEvent()
    data class BindingStarted(val activationCode: String) : BindingEvent()
    data class ShowUserGuide(
        val activationCode: String,
        val managementUrl: String,
        val instructions: List<String>
    ) : BindingEvent()
    data class PollingUpdate(val currentAttempt: Int, val maxAttempts: Int) : BindingEvent()
    data class ActivationCodeChanged(val newActivationCode: String) : BindingEvent()
    data class BindingCompleted(val websocketUrl: String) : BindingEvent()
    object BindingTimeout : BindingEvent()
    object BindingStopped : BindingEvent()
    object BindingReset : BindingEvent()
    data class ErrorOccurred(val message: String) : BindingEvent()
}

/**
 * 绑定初始化结果
 */
sealed class BindingInitResult {
    data class AlreadyBound(val websocketUrl: String) : BindingInitResult()
    data class NeedsBinding(val activationCode: String) : BindingInitResult()
    data class Error(val message: String) : BindingInitResult()
}

/**
 * 智能绑定结果
 */
sealed class SmartBindingResult {
    data class Success(val websocketUrl: String) : SmartBindingResult()
    object Timeout : SmartBindingResult()
    data class Failed(val message: String) : SmartBindingResult()
} 