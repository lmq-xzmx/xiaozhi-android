package info.dourok.voicebot.data.model

import org.json.JSONObject

//{
//    "mqtt":{
//    "endpoint":"post-cn-apg3xckag01.mqtt.aliyuncs.com",
//    "client_id":"GID_test@@@A4_B1_C2_D3_E4_F5",
//    "username":"Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01",
//    "password":"xdDhCgk9xjQpLECVH+5UsSBs0/k=",
//    "publish_topic":"device-server",
//    "subscribe_topic":"devices/A4_B1_C2_D3_E4_F5"
//},
//    "server_time":{
//    "timestamp":1740736167303,
//    "timezone":"Asia/Shanghai",
//    "timezone_offset":480
//},
//    "firmware":{
//    "version":"2.3.1",
//    "url":""
//},
//    "activation":{
//    "code":"010215",
//    "message":"xiaozhi.me\n010215"
//}
//}



data class OtaResult(
    val mqttConfig: MqttConfig?,
    val activation: Activation?,
    val serverTime: ServerTime?,
    val firmware: Firmware?
)

fun fromJsonToOtaResult(json: JSONObject): OtaResult? {
    return try {
        OtaResult(
            mqttConfig = json.optJSONObject("mqtt")?.let { fromJsonToMqttConfig(it) },
            activation = json.optJSONObject("activation")?.let { fromJsonToActivation(it) },
            serverTime = json.optJSONObject("server_time")?.let { fromJsonToServerTime(it) },
            firmware = json.optJSONObject("firmware")?.let { fromJsonToFirmware(it) }
        )
    } catch (e: Exception) {
        android.util.Log.e("OtaResult", "Failed to parse OTA result: ${e.message}")
        null
    }
}


data class ServerTime(
    val timestamp: Long,
    val timezone: String,
    val timezoneOffset: Int
)

fun fromJsonToServerTime(json: JSONObject): ServerTime {
    return ServerTime(
        timestamp = json.getLong("timestamp"),
        timezone = json.getString("timezone"),
        timezoneOffset = json.getInt("timezone_offset")
    )
}


data class Firmware(
    val version: String,
    val url: String
)

fun fromJsonToFirmware(json: JSONObject): Firmware {
    return Firmware(
        version = json.getString("version"),
        url = json.getString("url")
    )
}


data class Activation(
    val code: String,
    val message: String
)

fun fromJsonToActivation(json: JSONObject): Activation {
    return Activation(
        code = json.getString("code"),
        message = json.getString("message")
    )
}



data class MqttConfig(
    val endpoint: String,
    val clientId: String,
    val username: String,
    val password: String,
    val publishTopic: String,
    val subscribeTopic: String
)
//{
//    "endpoint":"post-cn-apg3xckag01.mqtt.aliyuncs.com",
//    "client_id":"GID_test@@@A4_B1_C2_D3_E4_F5",
//    "username":"Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01",
//    "password":"xdDhCgk9xjQpLECVH+5UsSBs0/k=",
//    "publish_topic":"device-server",
//    "subscribe_topic":"devices/A4_B1_C2_D3_E4_F5"
//}
fun fromJsonToMqttConfig(json: JSONObject): MqttConfig {
    return MqttConfig(
        json.getString("endpoint"),
        json.getString("client_id"),
        json.getString("username"),
        json.getString("password"),
        json.getString("publish_topic"),
        json.getString("subscribe_topic")
    )
}
