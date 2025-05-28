package info.dourok.voicebot.config

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import info.dourok.voicebot.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * OTA配置管理器
 * 负责从 http://47.122.144.73:8002/xiaozhi/ota/ 获取WebSocket配置
 */
@Singleton
class OtaConfigManager @Inject constructor(
    private val context: Context
) {
    companion object {
        private const val TAG = "OtaConfigManager"
        private const val OTA_URL = "http://47.122.144.73:8002/xiaozhi/ota/"
        private const val PREFS_NAME = "ota_config"
        private const val KEY_WEBSOCKET_URL = "websocket_url"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_LAST_UPDATE = "last_update"
        private const val KEY_ACTIVATION_CODE = "activation_code"
    }
    
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * 获取或生成设备ID（MAC地址格式）
     */
    fun getDeviceId(): String {
        return prefs.getString(KEY_DEVICE_ID, null) ?: generateDeviceId().also { deviceId ->
            prefs.edit().putString(KEY_DEVICE_ID, deviceId).apply()
            Log.i(TAG, "✅ 生成新设备ID: $deviceId")
        }
    }
    
    /**
     * 获取缓存的WebSocket URL
     */
    fun getCachedWebSocketUrl(): String? {
        return prefs.getString(KEY_WEBSOCKET_URL, null)
    }
    
    /**
     * 获取缓存的激活码
     */
    fun getCachedActivationCode(): String? {
        return prefs.getString(KEY_ACTIVATION_CODE, null)
    }
    
    /**
     * 从OTA服务器获取配置
     */
    suspend fun fetchOtaConfig(): OtaResult? = withContext(Dispatchers.IO) {
        try {
            Log.i(TAG, "🔧 开始获取OTA配置...")
            Log.i(TAG, "📡 OTA URL: $OTA_URL")
            
            val deviceId = getDeviceId()
            val clientId = UUID.randomUUID().toString()
            
            // 构建请求数据
            val requestData = JSONObject().apply {
                put("application", JSONObject().apply {
                    put("version", "1.0.0")
                    put("name", "xiaozhi-android")
                })
                put("macAddress", deviceId)
                put("board", JSONObject().apply {
                    put("type", "android")
                })
                put("chipModelName", "android")
            }
            
            Log.i(TAG, "📤 发送OTA请求...")
            Log.d(TAG, "设备ID: $deviceId")
            Log.d(TAG, "客户端ID: $clientId")
            
            val url = URL(OTA_URL)
            val connection = url.openConnection() as HttpURLConnection
            
            connection.apply {
                requestMethod = "POST"
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Device-Id", deviceId)
                setRequestProperty("Client-Id", clientId)
                doOutput = true
                connectTimeout = 10000
                readTimeout = 10000
            }
            
            // 发送请求数据
            OutputStreamWriter(connection.outputStream).use { writer ->
                writer.write(requestData.toString())
            }
            
            val responseCode = connection.responseCode
            Log.i(TAG, "📥 OTA响应码: $responseCode")
            
            if (responseCode == HttpURLConnection.HTTP_OK) {
                val response = connection.inputStream.bufferedReader().use { it.readText() }
                Log.i(TAG, "✅ OTA配置获取成功")
                Log.d(TAG, "响应内容: $response")
                
                val responseJson = JSONObject(response)
                val otaResult = fromJsonToOtaResult(responseJson)
                
                // 缓存配置
                cacheOtaResult(otaResult)
                
                return@withContext otaResult
                
            } else {
                val errorResponse = connection.errorStream?.bufferedReader()?.use { it.readText() }
                Log.e(TAG, "❌ OTA请求失败: $responseCode")
                Log.e(TAG, "错误响应: $errorResponse")
                return@withContext null
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ OTA配置获取异常", e)
            return@withContext null
        }
    }
    
    /**
     * 缓存OTA结果
     */
    private fun cacheOtaResult(otaResult: OtaResult) {
        prefs.edit().apply {
            // 缓存WebSocket URL
            otaResult.websocketUrl?.let { 
                putString(KEY_WEBSOCKET_URL, it)
                Log.i(TAG, "💾 WebSocket URL已缓存: $it")
            }
            
            // 缓存激活码
            otaResult.activationCode?.let { 
                putString(KEY_ACTIVATION_CODE, it)
                Log.i(TAG, "💾 激活码已缓存: $it")
            }
            
            // 更新时间戳
            putLong(KEY_LAST_UPDATE, System.currentTimeMillis())
            
            apply()
        }
    }
    
    /**
     * 清除缓存的配置
     */
    fun clearCache() {
        prefs.edit().apply {
            remove(KEY_WEBSOCKET_URL)
            remove(KEY_ACTIVATION_CODE)
            remove(KEY_LAST_UPDATE)
            apply()
        }
        Log.i(TAG, "🗑️ OTA缓存已清除")
    }
    
    /**
     * 生成MAC地址格式的设备ID
     */
    private fun generateDeviceId(): String {
        val uuid = UUID.randomUUID().toString().replace("-", "")
        val macFormat = uuid.substring(0, 12).uppercase()
        return "${macFormat.substring(0, 2)}:${macFormat.substring(2, 4)}:${macFormat.substring(4, 6)}:" +
               "${macFormat.substring(6, 8)}:${macFormat.substring(8, 10)}:${macFormat.substring(10, 12)}"
    }
    
    /**
     * 检查配置是否需要更新（可选功能）
     */
    fun shouldUpdateConfig(): Boolean {
        val lastUpdate = prefs.getLong(KEY_LAST_UPDATE, 0)
        val now = System.currentTimeMillis()
        val hoursSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60)
        
        // 24小时更新一次配置
        return hoursSinceUpdate >= 24 || getCachedWebSocketUrl() == null
    }
} 