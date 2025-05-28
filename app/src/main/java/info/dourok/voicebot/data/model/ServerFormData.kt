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
    val otaUrl: String = "http://47.122.144.73:8002/xiaozhi/ota/",
    val transportType: TransportType = TransportType.WebSockets
)

data class SelfHostConfig(
    val webSocketUrl: String = "ws://192.168.1.246:8000",
    val otaUrl: String = "http://192.168.1.246:8002/xiaozhi/ota/",
    val transportType: TransportType = TransportType.WebSockets // 固定为 WebSockets
)

// TransportType已在单独文件中定义，此处移除重复定义

// :feature:form/data/model/ValidationResult.kt
data class ValidationResult(
    val isValid: Boolean,
    val errors: Map<String, String> = emptyMap()
)