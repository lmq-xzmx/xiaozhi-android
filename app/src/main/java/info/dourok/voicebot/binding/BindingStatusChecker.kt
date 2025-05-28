package info.dourok.voicebot.binding

import android.content.Context
import android.util.Log
import info.dourok.voicebot.config.DeviceConfigManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BindingStatusChecker @Inject constructor(
    private val deviceConfigManager: DeviceConfigManager,
    private val context: Context
) {
    companion object {
        private const val TAG = "BindingStatusChecker"
        private const val OTA_ENDPOINT = "/xiaozhi/ota/"
        private const val TIMEOUT_MS = 10000
    }
    
    suspend fun checkBindingStatus(): BindingCheckResult = withContext(Dispatchers.IO) {
        try {
            val deviceId = deviceConfigManager.getDeviceId()
            val serverUrl = deviceConfigManager.getServerUrl()
            
            Log.d(TAG, "检查绑定状态 - 设备ID: $deviceId, 服务器: $serverUrl")
            
            val response = performOTACheck(deviceId, serverUrl)
            
            when {
                response.has("activation") -> {
                    val activationObj = response.getJSONObject("activation")
                    val activationCode = activationObj.getString("code")
                    val message = activationObj.optString("message", "")
                    
                    Log.i(TAG, "设备需要绑定，激活码: $activationCode")
                    
                    // 保存激活码到配置
                    deviceConfigManager.setActivationCode(activationCode)
                    deviceConfigManager.updateBindingStatus(false)
                    
                    BindingCheckResult.Unbound(deviceId, activationCode)
                }
                response.has("websocket") -> {
                    val websocketObj = response.getJSONObject("websocket")
                    val websocketUrl = websocketObj.getString("url")
                    
                    Log.i(TAG, "设备已绑定，WebSocket URL: $websocketUrl")
                    
                    // 更新绑定状态和WebSocket URL
                    deviceConfigManager.updateBindingStatus(true)
                    deviceConfigManager.setWebsocketUrl(websocketUrl)
                    
                    BindingCheckResult.Bound(deviceId, websocketUrl)
                }
                else -> {
                    Log.e(TAG, "服务器响应格式无效: $response")
                    BindingCheckResult.Error("服务器响应格式无效")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "检查绑定状态失败", e)
            BindingCheckResult.Error("网络错误: ${e.message}")
        }
    }
    
    private suspend fun performOTACheck(deviceId: String, serverUrl: String): JSONObject {
        val url = URL("$serverUrl$OTA_ENDPOINT")
        val connection = url.openConnection() as HttpURLConnection
        
        try {
            // 设置请求参数
            connection.requestMethod = "POST"
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Device-Id", deviceId)
            connection.setRequestProperty("Client-Id", "android-app-${System.currentTimeMillis()}")
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            connection.doOutput = true
            
            // 构建标准化的请求体 - 使用下划线命名格式
            val requestBody = JSONObject().apply {
                // 应用信息对象
                put("application", JSONObject().apply {
                    put("version", "1.0.0")
                })
                
                // 使用下划线命名的字段名（与成功测试格式一致）
                put("mac_address", deviceId)
                put("chip_model_name", "android")
                
                // 板子信息
                put("board", JSONObject().apply {
                    put("type", "android")
                })
            }
            
            Log.d(TAG, "发送OTA请求到: $url")
            Log.d(TAG, "请求体: ${requestBody.toString(2)}")
            
            // 发送请求
            OutputStreamWriter(connection.outputStream).use { writer ->
                writer.write(requestBody.toString())
                writer.flush()
            }
            
            // 读取响应
            val responseCode = connection.responseCode
            Log.d(TAG, "OTA响应码: $responseCode")
            
            if (responseCode == HttpURLConnection.HTTP_OK) {
                val response = BufferedReader(InputStreamReader(connection.inputStream)).use { reader ->
                    reader.readText()
                }
                
                Log.d(TAG, "OTA响应: $response")
                return JSONObject(response)
            } else {
                val errorResponse = BufferedReader(InputStreamReader(connection.errorStream ?: connection.inputStream)).use { reader ->
                    reader.readText()
                }
                Log.e(TAG, "OTA请求失败: $responseCode, $errorResponse")
                throw Exception("HTTP $responseCode: $errorResponse")
            }
        } finally {
            connection.disconnect()
        }
    }
    
    /**
     * 刷新绑定状态检查
     * 用于智能绑定管理器的轮询检查
     */
    suspend fun refreshBindingStatus(): BindingCheckResult {
        return checkBindingStatus()
    }
    
    suspend fun getLastCheckTime(): Long {
        return deviceConfigManager.getLastCheckTime()
    }
}

sealed class BindingCheckResult {
    data class Bound(val deviceId: String, val websocketUrl: String) : BindingCheckResult()
    data class Unbound(val deviceId: String, val activationCode: String) : BindingCheckResult()
    data class Error(val message: String) : BindingCheckResult()
    
    val isSuccess: Boolean
        get() = this is Bound || this is Unbound
        
    val isBound: Boolean
        get() = this is Bound
        
    val errorMessage: String?
        get() = if (this is Error) message else null
} 