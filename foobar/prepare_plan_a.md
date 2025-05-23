# 🚀 方案A准备：完整设备绑定实现

如果OTA格式调试失败，我们立即转向方案A的实施。

## 第一步：创建OTA数据模型

### 1.1 创建 `OTAResponse.kt`
```kotlin
// app/src/main/java/info/dourok/voicebot/data/model/OTAResponse.kt
package info.dourok.voicebot.data.model

sealed class OTAResponse {
    data class RequiresActivation(
        val activationCode: String,
        val message: String,
        val challenge: String
    ) : OTAResponse()
    
    data class Activated(
        val websocketUrl: String
    ) : OTAResponse()
    
    data class Error(
        val message: String
    ) : OTAResponse()
}
```

### 1.2 创建 `BindingResult.kt`
```kotlin
// app/src/main/java/info/dourok/voicebot/data/model/BindingResult.kt
package info.dourok.voicebot.data.model

sealed class BindingResult {
    object Success : BindingResult()
    data class Failed(val message: String) : BindingResult()
}
```

## 第二步：创建OTA客户端

### 2.1 创建 `OTAClient.kt`
```kotlin
// app/src/main/java/info/dourok/voicebot/data/network/OTAClient.kt
package info.dourok.voicebot.data.network

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import info.dourok.voicebot.data.model.OTAResponse

class OTAClient(private val baseUrl: String) {
    companion object {
        private const val TAG = "OTAClient"
    }
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    suspend fun checkDeviceActivation(
        deviceId: String, 
        clientId: String,
        appVersion: String = "1.0.0"
    ): OTAResponse = withContext(Dispatchers.IO) {
        val requestBody = JSONObject().apply {
            put("macAddress", deviceId)
            put("application", JSONObject().apply {
                put("version", appVersion)
                put("name", "xiaozhi-android")
            })
            put("board", JSONObject().apply {
                put("type", "android")
            })
            put("chipModelName", "android")
        }

        val request = Request.Builder()
            .url("$baseUrl/ota/")
            .post(requestBody.toString().toRequestBody("application/json".toMediaType()))
            .addHeader("Device-Id", deviceId)
            .addHeader("Client-Id", clientId)
            .addHeader("Content-Type", "application/json")
            .build()

        Log.i(TAG, "发送OTA请求到: ${request.url}")
        Log.d(TAG, "设备ID: $deviceId, 客户端ID: $clientId")
        Log.d(TAG, "请求体: ${requestBody.toString(2)}")

        try {
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.i(TAG, "OTA响应状态: ${response.code}")
            Log.d(TAG, "OTA响应内容: $responseBody")

            if (response.isSuccessful) {
                parseOTAResponse(responseBody)
            } else {
                Log.e(TAG, "OTA请求失败: ${response.code} - ${response.message}")
                OTAResponse.Error("OTA请求失败: ${response.code}")
            }
        } catch (e: Exception) {
            Log.e(TAG, "OTA请求异常: ${e.message}", e)
            OTAResponse.Error("网络请求失败: ${e.message}")
        }
    }

    private fun parseOTAResponse(responseBody: String): OTAResponse {
        return try {
            val json = JSONObject(responseBody)
            
            // 检查错误
            if (json.has("error")) {
                return OTAResponse.Error(json.getString("error"))
            }
            
            // 检查是否需要激活
            val activation = json.optJSONObject("activation")
            if (activation != null) {
                val code = activation.getString("code")
                val message = activation.optString("message", "")
                val challenge = activation.optString("challenge", "")
                
                Log.i(TAG, "设备需要激活，激活码: $code")
                return OTAResponse.RequiresActivation(code, message, challenge)
            }
            
            // 检查WebSocket配置
            val websocket = json.optJSONObject("websocket")
            if (websocket != null) {
                val wsUrl = websocket.getString("url")
                Log.i(TAG, "获取到WebSocket URL: $wsUrl")
                return OTAResponse.Activated(wsUrl)
            }
            
            // 未知响应格式
            Log.w(TAG, "未知的OTA响应格式: $responseBody")
            OTAResponse.Error("未知的服务器响应格式")
            
        } catch (e: Exception) {
            Log.e(TAG, "解析OTA响应失败: ${e.message}", e)
            OTAResponse.Error("解析服务器响应失败: ${e.message}")
        }
    }
}
```

## 第三步：修改FormRepository

### 3.1 修改 `FormResult.kt`
```kotlin
// 在FormResult.kt中添加
data class RequiresActivation(
    val activationCode: String,
    val message: String,
    val agentId: String,
    val baseUrl: String
) : FormResult()
```

### 3.2 修改 `FormRepository.kt`
```kotlin
// 在FormRepository.kt中添加WebSocket处理方法
private suspend fun handleWebSocketConfiguration(config: XiaoZhiConfig) {
    Log.i(TAG, "开始WebSocket设备绑定流程...")
    
    val otaClient = OTAClient(config.qtaUrl.removeSuffix("/"))
    val otaResponse = otaClient.checkDeviceActivation(
        deviceId = deviceInfo.mac_address,
        clientId = deviceInfo.uuid
    )

    when (otaResponse) {
        is OTAResponse.RequiresActivation -> {
            Log.i(TAG, "设备需要激活，激活码: ${otaResponse.activationCode}")
            _resultFlow.value = FormResult.RequiresActivation(
                activationCode = otaResponse.activationCode,
                message = otaResponse.message,
                agentId = "6bf580ad09cf4b1e8bd332dafb9e6d30",
                baseUrl = config.qtaUrl.removeSuffix("/ota/")
            )
        }
        
        is OTAResponse.Activated -> {
            Log.i(TAG, "设备已激活，配置WebSocket连接")
            settingsRepository.transportType = TransportType.WebSockets
            settingsRepository.webSocketUrl = otaResponse.websocketUrl
            settingsRepository.mqttConfig = null
            _resultFlow.value = FormResult.XiaoZhiResult(null)
        }
        
        is OTAResponse.Error -> {
            Log.e(TAG, "OTA检查失败: ${otaResponse.message}")
            _resultFlow.value = FormResult.Error(otaResponse.message)
        }
    }
}
```

## 立即实施指令

如果OTA调试失败，请告知我，我将立即指导您：
1. 创建上述文件
2. 修改现有代码
3. 添加设备激活UI
4. 测试完整绑定流程

---
**请先尝试debug_ota_formats.md中的格式，如果都失败就开始方案A实施。** 