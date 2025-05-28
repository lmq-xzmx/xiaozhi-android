package info.dourok.voicebot.data.model

import org.json.JSONObject

/**
 * MQTT配置数据结构
 * 用于MQTT协议连接配置
 */
data class MqttConfig(
    val endpoint: String,
    val clientId: String,
    val username: String,
    val password: String,
    val publishTopic: String,
    val subscribeTopic: String
)

/**
 * 从JSON对象转换为MqttConfig
 */
fun fromJsonToMqttConfig(json: JSONObject): MqttConfig {
    return MqttConfig(
        endpoint = json.getString("endpoint"),
        clientId = json.getString("client_id"),
        username = json.getString("username"),
        password = json.getString("password"),
        publishTopic = json.getString("publish_topic"),
        subscribeTopic = json.getString("subscribe_topic")
    )
}

/**
 * 将MqttConfig转换为JSON字符串
 */
fun MqttConfig.toJson(): String {
    val json = JSONObject().apply {
        put("endpoint", endpoint)
        put("client_id", clientId)
        put("username", username)
        put("password", password)
        put("publish_topic", publishTopic)
        put("subscribe_topic", subscribeTopic)
    }
    return json.toString()
} 