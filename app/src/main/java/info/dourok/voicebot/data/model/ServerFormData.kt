package info.dourok.voicebot.data.model

// :feature:form/data/model/ServerFormData.kt
data class ServerFormData(
    val serverType: ServerType = ServerType.XiaoZhi,
    val xiaoZhiConfig: XiaoZhiConfig = XiaoZhiConfig(),
    val selfHostConfig: SelfHostConfig = SelfHostConfig()
)

enum class ServerType {
    XiaoZhi, SelfHost
}

data class XiaoZhiConfig(
    val webSocketUrl: String = "ws://47.122.144.73:8000/xiaozhi/v1/",
    val qtaUrl: String = "http://47.122.144.73:8002/xiaozhi/ota/",
    val transportType: TransportType = TransportType.WebSockets
)

data class SelfHostConfig(
    val webSocketUrl: String = "ws://47.122.144.73:8000/xiaozhi/v1/",
    val transportType: TransportType = TransportType.WebSockets // 固定为 WebSockets
)

enum class TransportType {
    MQTT, WebSockets
}

// :feature:form/data/model/ValidationResult.kt
data class ValidationResult(
    val isValid: Boolean,
    val errors: Map<String, String> = emptyMap()
)