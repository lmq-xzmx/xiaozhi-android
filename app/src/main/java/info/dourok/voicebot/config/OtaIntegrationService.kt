package info.dourok.voicebot.config

import android.util.Log
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.OtaResult
import kotlinx.coroutines.*
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
    }
    
    private var otaConfigJob: Job? = null
    private var currentOtaResult: OtaResult? = null
    
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
                
            } catch (e: Exception) {
                Log.e(TAG, "❌ OTA配置初始化异常", e)
                useDefaultConfig()
            }
        }
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
                
                // 使用默认配置让STT先工作
                useDefaultConfig()
            }
            
            else -> {
                Log.w(TAG, "⚠️ OTA响应格式异常")
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
        otaConfigJob = null
        Log.i(TAG, "🧹 OTA集成服务已清理")
    }
} 