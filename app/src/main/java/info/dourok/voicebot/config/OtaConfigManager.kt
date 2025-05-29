package info.dourok.voicebot.config

import android.content.Context
import android.content.SharedPreferences
import android.net.wifi.WifiManager
import android.provider.Settings
import android.util.Log
import info.dourok.voicebot.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.NetworkInterface
import java.net.URL
import java.security.MessageDigest
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
        private const val CACHE_EXPIRY_MS = 24 * 60 * 60 * 1000L // 24小时
    }
    
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * 🔧 修改3: 获取或生成基于硬件的持久设备ID
     */
    fun getDeviceId(): String {
        // 首先尝试从缓存获取
        val cachedDeviceId = prefs.getString(KEY_DEVICE_ID, null)
        if (cachedDeviceId != null) {
            Log.d(TAG, "✅ 使用缓存的设备ID: $cachedDeviceId")
            return cachedDeviceId
        }
        
        // 🔧 修改3: 生成基于硬件特征的持久设备ID
        val hardwareDeviceId = generateHardwareBasedDeviceId()
        
        // 保存到缓存
        prefs.edit().putString(KEY_DEVICE_ID, hardwareDeviceId).apply()
        Log.i(TAG, "✅ 生成并缓存硬件基础设备ID: $hardwareDeviceId")
        
        return hardwareDeviceId
    }
    
    /**
     * 🔧 修改3: 生成基于硬件特征的设备ID
     * 即使清除应用数据，只要是同一台设备，生成的ID都是一致的
     */
    private fun generateHardwareBasedDeviceId(): String {
        try {
            // 方法1: 尝试获取真实MAC地址（Android 6.0+会有限制）
            val realMacAddress = getRealMacAddress()
            if (realMacAddress != null) {
                Log.i(TAG, "🔧 使用真实MAC地址: $realMacAddress")
                return formatMacAddress(realMacAddress)
            }
            
            // 方法2: 使用WiFi MAC地址（可能返回固定值）
            val wifiMacAddress = getWifiMacAddress()
            if (wifiMacAddress != null && wifiMacAddress != "02:00:00:00:00:00") {
                Log.i(TAG, "🔧 使用WiFi MAC地址: $wifiMacAddress")
                return formatMacAddress(wifiMacAddress)
            }
            
            // 方法3: 使用Android ID + 设备特征生成稳定ID
            val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
            val deviceModel = android.os.Build.MODEL
            val deviceManufacturer = android.os.Build.MANUFACTURER
            val deviceSerial = try {
                android.os.Build.getSerial()
            } catch (e: Exception) {
                "unknown"
            }
            
            // 组合设备特征
            val deviceFingerprint = "$androidId-$deviceModel-$deviceManufacturer-$deviceSerial"
            
            // 生成基于设备特征的MAC格式ID
            val hash = MessageDigest.getInstance("SHA-256").digest(deviceFingerprint.toByteArray())
            val macBytes = hash.sliceArray(0..5) // 取前6字节
            
            val generatedMac = macBytes.joinToString(":") { 
                String.format("%02X", it.toInt() and 0xFF) 
            }
            
            Log.i(TAG, "🔧 基于设备特征生成MAC格式ID: $generatedMac")
            Log.d(TAG, "设备特征: AndroidID=${androidId}, Model=${deviceModel}, Manufacturer=${deviceManufacturer}")
            
            return generatedMac
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ 生成硬件基础设备ID失败，使用随机ID", e)
            // 最后的fallback：生成随机MAC格式ID
            return generateRandomMacAddress()
        }
    }
    
    /**
     * 获取真实MAC地址（适用于Android 6.0以下或有root权限）
     */
    private fun getRealMacAddress(): String? {
        try {
            val networkInterfaces = NetworkInterface.getNetworkInterfaces()
            while (networkInterfaces.hasMoreElements()) {
                val networkInterface = networkInterfaces.nextElement()
                
                // 寻找WiFi网络接口
                if (networkInterface.name.equals("wlan0", ignoreCase = true)) {
                    val macBytes = networkInterface.hardwareAddress
                    if (macBytes != null && macBytes.size == 6) {
                        val macAddress = macBytes.joinToString(":") { 
                            String.format("%02X", it.toInt() and 0xFF) 
                        }
                        if (macAddress != "02:00:00:00:00:00") { // 排除虚拟MAC
                            return macAddress
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.d(TAG, "无法获取真实MAC地址: ${e.message}")
        }
        return null
    }
    
    /**
     * 获取WiFi MAC地址（Android 6.0+可能返回固定值）
     */
    private fun getWifiMacAddress(): String? {
        try {
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val wifiInfo = wifiManager.connectionInfo
            val macAddress = wifiInfo.macAddress
            if (macAddress != null && macAddress != "02:00:00:00:00:00") {
                return macAddress.uppercase()
            }
        } catch (e: Exception) {
            Log.d(TAG, "无法获取WiFi MAC地址: ${e.message}")
        }
        return null
    }
    
    /**
     * 格式化MAC地址为标准格式
     */
    private fun formatMacAddress(macAddress: String): String {
        return macAddress.replace("-", ":").uppercase()
    }
    
    /**
     * 生成随机MAC格式地址（作为最后的fallback）
     */
    private fun generateRandomMacAddress(): String {
        val random = Random()
        val macBytes = ByteArray(6)
        random.nextBytes(macBytes)
        // 设置本地管理位，避免与真实MAC冲突
        macBytes[0] = (macBytes[0].toInt() or 0x02).toByte()
        
        return macBytes.joinToString(":") { 
            String.format("%02X", it.toInt() and 0xFF) 
        }
    }
    
    /**
     * 获取缓存的WebSocket URL
     */
    fun getCachedWebSocketUrl(): String? {
        val lastUpdate = prefs.getLong(KEY_LAST_UPDATE, 0L)
        val isExpired = System.currentTimeMillis() - lastUpdate > CACHE_EXPIRY_MS
        
        return if (isExpired) {
            Log.d(TAG, "💾 缓存的WebSocket URL已过期")
            null
        } else {
            val url = prefs.getString(KEY_WEBSOCKET_URL, null)
            if (url != null) {
                Log.d(TAG, "💾 使用缓存的WebSocket URL: $url")
            }
            url
        }
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
        val deviceId = getDeviceId()
        
        Log.i(TAG, "📡 向OTA服务器请求配置...")
        Log.d(TAG, "设备ID: $deviceId")
        Log.d(TAG, "OTA URL: $OTA_URL")
        
        try {
            val connection = URL(OTA_URL).openConnection() as HttpURLConnection
            
            // 设置请求方法和头部
            connection.requestMethod = "POST"
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Device-Id", deviceId)
            connection.setRequestProperty("Client-Id", "android-app-${System.currentTimeMillis()}")
            connection.doOutput = true
            connection.connectTimeout = 10000
            connection.readTimeout = 15000
            
            // 构建请求体
            val requestJson = JSONObject().apply {
                put("device_id", deviceId)
                put("client_type", "android")
                put("app_version", "1.0.0")
                put("android_version", android.os.Build.VERSION.RELEASE)
                put("device_model", android.os.Build.MODEL)
            }
            
            Log.d(TAG, "📤 请求体: $requestJson")
            
            // 发送请求
            OutputStreamWriter(connection.outputStream).use { writer ->
                writer.write(requestJson.toString())
                writer.flush()
            }
            
            val responseCode = connection.responseCode
            Log.d(TAG, "📥 响应状态码: $responseCode")
            
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
            // 🔧 修改3: 保留设备ID，确保设备身份持久化
            // remove(KEY_DEVICE_ID) // 不清除设备ID
            apply()
        }
        Log.i(TAG, "🧹 OTA缓存已清除（保留设备ID）")
    }
    
    /**
     * 强制清除所有配置（包括设备ID）
     */
    fun clearAllConfig() {
        prefs.edit().clear().apply()
        Log.i(TAG, "🧹 所有OTA配置已清除")
    }
} 