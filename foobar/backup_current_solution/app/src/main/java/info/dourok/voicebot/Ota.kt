package info.dourok.voicebot

import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.content.FileProvider
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okio.buffer
import okio.sink
import org.json.JSONObject
import org.json.JSONArray
import java.io.File
import java.util.concurrent.TimeUnit
import androidx.core.content.edit
import info.dourok.voicebot.data.model.Activation
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.model.DeviceIdManager
import info.dourok.voicebot.data.model.MqttConfig
import info.dourok.voicebot.data.model.OtaResult
import info.dourok.voicebot.data.model.fromJsonToOtaResult
import info.dourok.voicebot.data.model.toJson
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.config.DeviceConfigManager
import info.dourok.voicebot.data.SettingsRepository
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class Ota @Inject constructor(
    private val context: Context,
    val deviceInfo: DeviceInfo,
    private val deviceIdManager: DeviceIdManager,
    private val deviceConfigManager: DeviceConfigManager,
    private val settingsRepository: SettingsRepository
) {
    companion object {
        private const val TAG = "Ota"
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    var otaResult: OtaResult? = null

    val headers = mutableMapOf<String, String>()
    val currentVersion = deviceInfo.application.version
    val firmwareUrl: String
        get() = otaResult?.firmware?.url ?: ""
    val hasActivationCode: Boolean
        get() = otaResult?.activation != null

    // 升级进度和速度的 Flow
    private val _upgradeState = MutableStateFlow(Pair(0, 0L)) // (progress, speed)
    val upgradeState: StateFlow<Pair<Int, Long>> = _upgradeState

    // 设置 HTTP Header
    fun setHeader(key: String, value: String) {
        headers[key] = value
    }

    init {
        setHeader("Device-Id", deviceInfo.mac_address)
        setHeader("Client-Id", deviceInfo.uuid)
        setHeader("X-Language", "Chinese")
    }

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
     * 构建ESP32兼容的OTA请求体
     */
    private suspend fun buildESP32CompatibleOtaRequest(): JSONObject {
        val deviceId = deviceIdManager.getStableDeviceId()
        
        return JSONObject().apply {
            // 使用ESP32标准字段名
            put("mac", deviceId)  // 不是macAddress
            put("chip_model", "android")  // 不是chipModelName
            
            // 简化application结构
            put("application", JSONObject().apply {
                put("version", deviceInfo.application.version)
                put("name", "xiaozhi")  // 不是xiaozhi-android
            })
            
            // 简化board结构
            put("board", JSONObject().apply {
                put("type", "android")
            })
            
            // 保留必要字段
            put("uuid", deviceInfo.uuid)
        }
    }
    
    /**
     * 构建最简化的OTA请求体
     */
    private suspend fun buildMinimalOtaRequest(): JSONObject {
        val deviceId = deviceIdManager.getStableDeviceId()
        
        return JSONObject().apply {
            put("mac", deviceId)
            put("chip_model", "android")
            put("version", deviceInfo.application.version)
            put("uuid", deviceInfo.uuid)
        }
    }
    
    /**
     * 构建ESP32精确格式的OTA请求体（已验证可用）
     */
    private suspend fun buildESP32ExactOtaRequest(): JSONObject {
        val deviceId = deviceIdManager.getStableDeviceId()
        
        return JSONObject().apply {
            put("version", 2)
            put("flash_size", 8589934592L)  // 8GB Android存储
            put("psram_size", 8589934592L)  // 8GB RAM
            put("mac_address", deviceId)
            put("uuid", deviceInfo.uuid)
            put("chip_model_name", "ESP32")  // 关键：使用ESP32而不是android
            
            // chip_info对象
            put("chip_info", JSONObject().apply {
                put("model", 1030)  // Android API level
                put("cores", Runtime.getRuntime().availableProcessors())
                put("revision", 1)
                put("features", 63)  // 所有功能位
            })
            
            // application对象
            put("application", JSONObject().apply {
                put("version", deviceInfo.application.version)
                put("name", "xiaozhi")  // 关键：使用xiaozhi而不是xiaozhi-android
                put("compile_time", SimpleDateFormat("MMM dd yyyy HH:mm:ss", Locale.ENGLISH)
                    .format(Date()))
                put("compile_date", SimpleDateFormat("MMM dd yyyy", Locale.ENGLISH)
                    .format(Date()))
                put("compile_time_str", SimpleDateFormat("HH:mm:ss", Locale.ENGLISH)
                    .format(Date()))
                put("idf_version", "android-${Build.VERSION.RELEASE}")
            })
            
            // partition_table数组
            put("partition_table", JSONArray().apply {
                put(JSONObject().apply {
                    put("label", "system")
                    put("offset", 0)
                    put("size", 4294967296L)  // 4GB
                    put("type", 0)
                    put("subtype", 0)
                })
            })
            
            // ota对象
            put("ota", JSONObject().apply {
                put("state", "app_update")
            })
            
            // board对象
            put("board", JSONObject().apply {
                put("type", "esp32")  // 关键：使用esp32而不是android
                put("manufacturer", Build.MANUFACTURER)
                put("model", Build.MODEL)
                put("version", Build.VERSION.RELEASE)
            })
        }
    }
    
    /**
     * 尝试发送OTA请求
     */
    private suspend fun tryOtaRequest(requestBody: JSONObject, checkVersionUrl: String): Boolean {
        return try {
            Log.d(TAG, "尝试OTA请求格式:")
            Log.d(TAG, requestBody.toString(2))
            
            val requestBuilder = Request.Builder()
                .url(checkVersionUrl)
                .addHeader("Content-Type", "application/json")
            
            // 添加所有headers
            headers.forEach { (key, value) -> 
                requestBuilder.addHeader(key, value) 
            }
            
            val request = requestBuilder.post(
                requestBody.toString().toRequestBody("application/json".toMediaTypeOrNull())
            ).build()

            val response = client.newCall(request).execute()
            
            Log.d(TAG, "服务器响应: ${response.code}")
            val responseBody = response.body?.string() ?: ""
            Log.d(TAG, "响应内容: $responseBody")
            
            if (response.isSuccessful && responseBody.isNotEmpty()) {
                val json = JSONObject(responseBody)
                
                // 检查是否是标准API响应格式
                if (json.has("code") && json.has("msg")) {
                    val code = json.getInt("code")
                    val msg = json.getString("msg")
                    
                    if (code == 0) {
                        // API成功，检查data字段
                        val data = json.optJSONObject("data")
                        if (data != null) {
                            Log.i(TAG, "收到标准API成功响应，解析data字段")
                            parseJsonResponse(data)
                            return true
                        } else {
                            Log.w(TAG, "API成功但data为空")
                            return false
                        }
                    } else {
                        // API错误
                        Log.w(TAG, "API返回错误: code=$code, msg=$msg")
                        if (code == 500) {
                            Log.w(TAG, "服务器内部错误，可能是请求格式不兼容")
                        }
                        return false
                    }
                } else {
                    // 直接的OTA响应格式
                    Log.i(TAG, "收到直接OTA响应格式")
                    parseJsonResponse(json)
                    return true
                }
            } else {
                Log.w(TAG, "HTTP响应失败或响应体为空: ${response.code}")
                return false
            }
            
        } catch (e: Exception) {
            Log.w(TAG, "OTA请求失败: ${e.message}")
            false
        }
    }

    // 检查版本
    suspend fun checkVersion(checkVersionUrl: String): Boolean = withContext(Dispatchers.IO) {
        Log.i(TAG, "开始OTA版本检查: $checkVersionUrl")
        Log.i(TAG, "Current version: $currentVersion")

        if (checkVersionUrl.length < 10) {
            Log.e(TAG, "OTA URL配置错误，长度过短: $checkVersionUrl")
            return@withContext false
        }

        try {
            // 获取稳定的设备ID并更新header
            val deviceId = deviceIdManager.getStableDeviceId()
            setHeader("Device-Id", deviceId)
            
            Log.d(TAG, "使用设备ID: $deviceId")
            
            // 调整格式优先级：简化格式优先，避免服务器500错误
            val requestFormats = listOf(
                "简化Android格式",
                "Android标准格式",
                "ESP32兼容格式",
                "ESP32精确格式"
            )
            
            for (formatName in requestFormats) {
                Log.i(TAG, "尝试 $formatName")
                
                val requestBody = when (formatName) {
                    "简化Android格式" -> buildSimplifiedAndroidOtaRequest()
                    "Android标准格式" -> buildStandardOtaRequest()
                    "ESP32兼容格式" -> buildESP32CompatibleOtaRequest()
                    "ESP32精确格式" -> buildESP32ExactOtaRequest()
                    else -> buildSimplifiedAndroidOtaRequest()
                }
                
                val success = tryOtaRequest(requestBody, checkVersionUrl)
                
                if (success) {
                    Log.i(TAG, "$formatName 成功！")
                    return@withContext true
                } else {
                    Log.w(TAG, "$formatName 失败，尝试下一个格式")
                }
            }
            
            Log.e(TAG, "所有OTA请求格式都失败")
            return@withContext false
            
        } catch (e: Exception) {
            Log.e(TAG, "OTA检查异常", e)
            val errorMessage = when (e) {
                is java.net.SocketTimeoutException -> "网络连接超时，请检查网络设置"
                is java.net.ConnectException -> "无法连接到服务器，请检查服务器地址"
                is java.net.UnknownHostException -> "无法解析服务器地址，请检查网络"
                else -> "网络错误：${e.message}"
            }
            Log.e(TAG, "错误详情: $errorMessage")
            return@withContext false
        }
    }

    /**
     * 构建简化的Android OTA请求体（优先使用）
     */
    private suspend fun buildSimplifiedAndroidOtaRequest(): JSONObject {
        val deviceId = deviceIdManager.getStableDeviceId()
        
        return JSONObject().apply {
            // 使用标准字段名，但简化结构
            put("mac_address", deviceId)
            put("chip_model_name", "android")
            
            // 简化application结构
            put("application", JSONObject().apply {
                put("version", deviceInfo.application.version)
                put("name", "xiaozhi-android")
            })
            
            // 简化board结构
            put("board", JSONObject().apply {
                put("type", "android")
            })
            
            // 必要字段
            put("uuid", deviceInfo.uuid)
        }
    }

    // 解析 JSON 响应
    private suspend fun parseJsonResponse(json: JSONObject) {
        try {
            val otaResult = fromJsonToOtaResult(json)
            this.otaResult = otaResult
            
            Log.i(TAG, "OTA响应解析完成: needsActivation=${otaResult.needsActivation}, isActivated=${otaResult.isActivated}")
            
            // 根据响应类型保存相应配置
            when {
                // 情况1：需要激活（有activation字段）
                otaResult.needsActivation -> {
                    val activationCode = otaResult.activationCode!!
                    Log.i(TAG, "设备需要激活，激活码: $activationCode")
                    
                    // 保存激活信息到DeviceConfigManager
                    deviceConfigManager.setActivationCode(activationCode)
                    deviceConfigManager.updateBindingStatus(false)
                    
                    // 清除之前的WebSocket配置
                    settingsRepository.webSocketUrl = null
                    settingsRepository.transportType = TransportType.None
                }
                
                // 情况2：已激活（有websocket字段）
                otaResult.isActivated -> {
                    val websocketUrl = otaResult.websocketUrl!!
                    Log.i(TAG, "设备已激活，WebSocket URL: $websocketUrl")
                    
                    // 保存WebSocket配置到两个地方
                    deviceConfigManager.setWebsocketUrl(websocketUrl)
                    deviceConfigManager.updateBindingStatus(true)
                    deviceConfigManager.setActivationCode(null) // 清除激活码
                    
                    // 同步到SettingsRepository
                    settingsRepository.webSocketUrl = websocketUrl
                    settingsRepository.transportType = TransportType.WebSockets
                    
                    Log.i(TAG, "WebSocket配置已保存到SettingsRepository")
                }
                
                // 情况3：有MQTT配置（备用传输方式）
                otaResult.mqttConfig != null -> {
                    val mqttConfig = otaResult.mqttConfig!!
                    Log.i(TAG, "收到MQTT配置: ${mqttConfig.endpoint}")
                    
                    // 保存MQTT配置
                    deviceConfigManager.updateBindingStatus(true)
                    settingsRepository.transportType = TransportType.MQTT
                    // 这里可以添加MQTT配置保存逻辑
                }
                
                else -> {
                    Log.w(TAG, "OTA响应不包含有效的配置信息")
                }
            }
            
            // 保存服务器时间（如果有）
            otaResult.serverTime?.let { serverTime ->
                Log.d(TAG, "服务器时间: ${serverTime.timestamp}")
                // 可以用于时间同步
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "解析OTA响应失败", e)
        }
    }

    // 标记当前版本有效（Android 不直接支持分区，这里模拟）
    suspend fun markCurrentVersionValid() {
        Log.i(TAG, "Marking current version as valid (Android simulation)")
        // Android 不需要分区管理，通常由系统验证 APK
    }

    // 升级固件
    suspend fun upgrade(firmwareUrl: String = this.firmwareUrl) = withContext(Dispatchers.IO) {
        Log.i(TAG, "Upgrading firmware from $firmwareUrl")

        val request = Request.Builder()
            .url(firmwareUrl)
            .build()

        try {
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                Log.e(TAG, "Failed to download firmware: ${response.code}")
                return@withContext
            }

            val contentLength = response.body?.contentLength() ?: 0L
            if (contentLength == 0L) {
                Log.e(TAG, "Failed to get content length")
                return@withContext
            }

            val file = File(context.cacheDir, "firmware.apk")
            val sink = file.sink().buffer()
            val source = response.body?.source() ?: return@withContext

            var totalRead = 0L
            var recentRead = 0L
            var lastCalcTime = System.currentTimeMillis()

            while (true) {
                val read = source.read(sink.buffer, 512)
                if (read == -1L) break

                recentRead += read
                totalRead += read
                val currentTime = System.currentTimeMillis()
                if (currentTime - lastCalcTime >= 1000 || read == 0L) {
                    val progress = (totalRead * 100 / contentLength).toInt()
                    val speed = recentRead * 1000 / (currentTime - lastCalcTime) // 字节/秒
                    Log.i(TAG, "Progress: $progress% ($totalRead/$contentLength), Speed: $speed B/s")
                    _upgradeState.emit(Pair(progress, speed))
                    lastCalcTime = currentTime
                    recentRead = 0L
                }
            }

            sink.close()
            source.close()

            // 验证和安装（Android APK 示例）
            val downloadedVersion = "1.0.0" // 假设从文件元数据获取，实际需解析
            if (downloadedVersion == currentVersion) {
                Log.e(TAG, "Firmware version is the same, skipping upgrade")
                return@withContext
            }

            installFirmware(file)
            Log.i(TAG, "Firmware upgrade successful, restarting app...")
            delay(3000) // 模拟重启
            restartApp()

        } catch (e: Exception) {
            Log.e(TAG, "Upgrade failed: ${e.message}")
        }
    }

    // 开始升级，带回调
    suspend fun startUpgrade() {
        upgrade(firmwareUrl)
    }

    // 解析版本号
    private fun parseVersion(version: String): List<Int> {
        return version.split(".").map { it.toInt() }
    }

    // 检查是否有新版本
    private fun isNewVersionAvailable(currentVersion: String, newVersion: String): Boolean {
        val current = parseVersion(currentVersion)
        val newer = parseVersion(newVersion)

        for (i in 0 until minOf(current.size, newer.size)) {
            if (newer[i] > current[i]) return true
            if (newer[i] < current[i]) return false
        }
        return newer.size > current.size
    }

    // 安装固件（Android APK 示例）
    private fun installFirmware(file: File) {
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        val intent = Intent(Intent.ACTION_INSTALL_PACKAGE).apply {
            data = uri
            flags = Intent.FLAG_GRANT_READ_URI_PERMISSION
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                putExtra(Intent.EXTRA_NOT_UNKNOWN_SOURCE, true)
            }
        }
        context.startActivity(intent)
    }

    // 重启应用
    private fun restartApp() {
        val intent = context.packageManager.getLaunchIntentForPackage(context.packageName)
        intent?.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
        context.startActivity(intent)
        android.os.Process.killProcess(android.os.Process.myPid())
    }
}
