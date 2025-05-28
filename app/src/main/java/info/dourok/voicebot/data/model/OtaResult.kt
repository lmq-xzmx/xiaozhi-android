package info.dourok.voicebot.data.model

import org.json.JSONObject

/**
 * OTA配置结果数据模型
 * 支持从 http://47.122.144.73:8002/xiaozhi/ota/ 获取配置
 */
data class OtaResult(
    val websocketConfig: WebSocketConfig?,
    val activation: Activation?,
    val serverTime: ServerTime?,
    val firmware: Firmware?
) {
    val needsActivation: Boolean get() = activation != null
    
    val isActivated: Boolean get() = websocketConfig != null && activation == null
    
    val activationCode: String? get() = activation?.code
    
    val websocketUrl: String? get() = websocketConfig?.url
}

/**
 * WebSocket配置
 */
data class WebSocketConfig(
    val url: String,
    val token: String? = null
)

/**
 * 设备激活信息
 */
data class Activation(
    val code: String,
    val message: String
) {
    val frontendUrl: String? get() {
        val lines = message.split("\n")
        return lines.firstOrNull { it.startsWith("http") }
            ?: "http://47.122.144.73:8002/#/home"
    }
}

/**
 * 服务器时间信息
 */
data class ServerTime(
    val timestamp: Long,
    val timezone: String?,
    val timezoneOffset: Int
)

/**
 * 固件信息
 */
data class Firmware(
    val version: String,
    val url: String
)

/**
 * JSON解析扩展函数
 */
fun fromJsonToWebSocketConfig(json: JSONObject): WebSocketConfig {
    return WebSocketConfig(
        url = json.getString("url"),
        token = json.optString("token", null)
    )
}

fun fromJsonToActivation(json: JSONObject): Activation {
    return Activation(
        code = json.getString("code"),
        message = json.getString("message")
    )
}

fun fromJsonToServerTime(json: JSONObject): ServerTime {
    return ServerTime(
        timestamp = json.getLong("timestamp"),
        timezone = json.optString("timezone", null),
        timezoneOffset = json.getInt("timezone_offset")
    )
}

fun fromJsonToFirmware(json: JSONObject): Firmware {
    return Firmware(
        version = json.getString("version"),
        url = json.getString("url")
    )
}

fun fromJsonToOtaResult(json: JSONObject): OtaResult {
    return OtaResult(
        websocketConfig = json.optJSONObject("websocket")?.let { fromJsonToWebSocketConfig(it) },
        activation = json.optJSONObject("activation")?.let { fromJsonToActivation(it) },
        serverTime = json.optJSONObject("server_time")?.let { fromJsonToServerTime(it) },
        firmware = json.optJSONObject("firmware")?.let { fromJsonToFirmware(it) }
    )
}
