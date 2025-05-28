package info.dourok.voicebot.config

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import info.dourok.voicebot.Ota
import info.dourok.voicebot.data.model.OtaResult
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ActivationManager @Inject constructor(
    private val context: Context,
    private val ota: Ota,
    private val deviceConfigManager: DeviceConfigManager
) {
    companion object {
        private const val TAG = "ActivationManager"
        private const val OTA_URL = "http://47.122.144.73:8002/xiaozhi/ota/"
        private const val MAX_RETRY_ATTEMPTS = 3
        private const val RETRY_DELAY_MS = 2000L
    }
    
    private val _activationState = MutableStateFlow<ActivationState>(ActivationState.Unknown)
    val activationState: StateFlow<ActivationState> = _activationState.asStateFlow()
    
    /**
     * 检查设备激活状态
     */
    suspend fun checkActivationStatus(): ActivationResult {
        Log.i(TAG, "开始检查设备激活状态")
        _activationState.value = ActivationState.Checking
        
        // 🔧 首先检查本地缓存的配置，避免不必要的OTA检查
        val cachedWebsocketUrl = deviceConfigManager.getWebsocketUrl()
        val bindingStatus = deviceConfigManager.getBindingStatus()
        
        if (bindingStatus && !cachedWebsocketUrl.isNullOrEmpty()) {
            Log.i(TAG, "✅ 使用缓存的WebSocket配置: $cachedWebsocketUrl")
            _activationState.value = ActivationState.Activated(cachedWebsocketUrl)
            return ActivationResult.Activated(cachedWebsocketUrl)
        }
        
        Log.i(TAG, "🔍 没有缓存配置，执行OTA检查...")
        
        var lastException: Exception? = null
        
        // 重试机制
        repeat(MAX_RETRY_ATTEMPTS) { attempt ->
            try {
                Log.d(TAG, "OTA检查尝试 ${attempt + 1}/$MAX_RETRY_ATTEMPTS")
                
                val success = ota.checkVersion(OTA_URL)
                if (!success) {
                    throw Exception("OTA检查失败")
                }
                
                val otaResult = ota.otaResult
                if (otaResult == null) {
                    throw Exception("OTA结果为空")
                }
                
                return handleOtaResult(otaResult)
                
            } catch (e: Exception) {
                lastException = e
                Log.w(TAG, "OTA检查失败 (尝试 ${attempt + 1}): ${e.message}")
                
                if (attempt < MAX_RETRY_ATTEMPTS - 1) {
                    delay(RETRY_DELAY_MS)
                }
            }
        }
        
        // 所有重试都失败
        _activationState.value = ActivationState.Error("网络连接失败")
        return ActivationResult.NetworkError(lastException?.message ?: "未知网络错误")
    }
    
    /**
     * 处理OTA结果
     */
    private suspend fun handleOtaResult(otaResult: OtaResult): ActivationResult {
        Log.i(TAG, "处理OTA结果: needsActivation=${otaResult.needsActivation}, isActivated=${otaResult.isActivated}")
        
        return when {
            // 情况1: 需要激活（返回了激活码）
            otaResult.needsActivation -> {
                val activationCode = otaResult.activationCode!!
                val frontendUrl = otaResult.activation!!.frontendUrl
                
                Log.i(TAG, "设备需要激活，激活码: $activationCode")
                
                // 保存激活码
                deviceConfigManager.setActivationCode(activationCode)
                deviceConfigManager.updateBindingStatus(false)
                
                _activationState.value = ActivationState.NeedsActivation(activationCode, frontendUrl)
                
                ActivationResult.NeedsActivation(
                    activationCode = activationCode,
                    frontendUrl = frontendUrl ?: "http://47.122.144.73:8002/#/home"
                )
            }
            
            // 情况2: 已激活（返回了WebSocket配置）
            otaResult.isActivated -> {
                val websocketUrl = otaResult.websocketUrl!!
                
                Log.i(TAG, "设备已激活，WebSocket URL: $websocketUrl")
                
                // 保存WebSocket URL和绑定状态
                deviceConfigManager.setWebsocketUrl(websocketUrl)
                deviceConfigManager.updateBindingStatus(true)
                deviceConfigManager.setActivationCode(null) // 清除激活码
                
                _activationState.value = ActivationState.Activated(websocketUrl)
                
                ActivationResult.Activated(websocketUrl)
            }
            
            // 情况3: 响应格式异常
            else -> {
                Log.e(TAG, "OTA响应格式异常，既没有激活码也没有WebSocket配置")
                _activationState.value = ActivationState.Error("服务器响应格式异常")
                ActivationResult.InvalidResponse("服务器响应格式异常")
            }
        }
    }
    
    /**
     * 打开前端管理面板
     */
    fun openManagementPanel(frontendUrl: String, activationCode: String) {
        try {
            // 构建带参数的URL
            val urlWithParams = if (frontendUrl.contains("?")) {
                "$frontendUrl&code=$activationCode"
            } else {
                "$frontendUrl?code=$activationCode"
            }
            
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(urlWithParams)).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            
            context.startActivity(intent)
            Log.i(TAG, "已打开管理面板: $urlWithParams")
            
        } catch (e: Exception) {
            Log.e(TAG, "打开管理面板失败: ${e.message}")
        }
    }
    
    /**
     * 轮询检查激活状态（用于激活码输入后的自动检查）
     */
    suspend fun pollActivationStatus(
        maxAttempts: Int = 30, // 5分钟，每10秒检查一次
        intervalMs: Long = 10000L
    ): ActivationResult {
        Log.i(TAG, "开始轮询激活状态，最多尝试 $maxAttempts 次")
        
        repeat(maxAttempts) { attempt ->
            Log.d(TAG, "轮询检查 ${attempt + 1}/$maxAttempts")
            
            val result = checkActivationStatus()
            
            when (result) {
                is ActivationResult.Activated -> {
                    Log.i(TAG, "轮询检查成功，设备已激活")
                    return result
                }
                is ActivationResult.NeedsActivation -> {
                    // 仍需激活，继续轮询
                    if (attempt < maxAttempts - 1) {
                        delay(intervalMs)
                    }
                }
                is ActivationResult.NetworkError,
                is ActivationResult.InvalidResponse -> {
                    // 网络错误或响应异常，继续重试
                    if (attempt < maxAttempts - 1) {
                        delay(intervalMs)
                    }
                }
            }
        }
        
        Log.w(TAG, "轮询超时，设备仍未激活")
        _activationState.value = ActivationState.Error("激活超时")
        return ActivationResult.NetworkError("激活超时，请检查是否已在管理面板完成绑定")
    }
    
    /**
     * 重置激活状态
     */
    suspend fun resetActivationState() {
        Log.i(TAG, "重置激活状态")
        deviceConfigManager.clearAllConfig()
        _activationState.value = ActivationState.Unknown
    }
}

/**
 * 激活状态
 */
sealed class ActivationState {
    object Unknown : ActivationState()
    object Checking : ActivationState()
    data class NeedsActivation(val activationCode: String, val frontendUrl: String?) : ActivationState()
    data class Activated(val websocketUrl: String) : ActivationState()
    data class Error(val message: String) : ActivationState()
}

/**
 * 激活结果
 */
sealed class ActivationResult {
    data class NeedsActivation(val activationCode: String, val frontendUrl: String) : ActivationResult()
    data class Activated(val websocketUrl: String) : ActivationResult()
    data class NetworkError(val message: String) : ActivationResult()
    data class InvalidResponse(val message: String) : ActivationResult()
} 