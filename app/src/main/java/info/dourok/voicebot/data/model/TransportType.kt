package info.dourok.voicebot.data.model

/**
 * 传输协议类型枚举
 * 定义支持的通信协议类型
 */
enum class TransportType {
    /**
     * WebSocket协议 - 推荐使用
     */
    WebSockets,
    
    /**
     * MQTT协议 - 传统支持
     */
    MQTT
} 