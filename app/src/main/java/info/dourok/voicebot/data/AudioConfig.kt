package info.dourok.voicebot.data

/**
 * 统一音频参数配置
 * 修改为与服务器兼容的参数：version=1, frame_duration=60ms
 */
object AudioConfig {
    // 基础音频参数 - 与服务器端点兼容
    const val SAMPLE_RATE = 16000
    const val CHANNELS = 1
    const val FRAME_DURATION_MS = 60  // 修改为60ms，与服务器端点一致
    const val BITRATE = 24000
    
    // 协议参数 - 与服务器端点兼容
    const val PROTOCOL_VERSION = 1  // 修改为版本1，与服务器一致
    const val TRANSPORT_TYPE = "websocket"
    
    // 音频格式
    const val AUDIO_FORMAT = "opus"
    
    // WebSocket配置
    const val CONNECTION_TIMEOUT_SEC = 30L
    const val READ_TIMEOUT_SEC = 60L
    const val WRITE_TIMEOUT_SEC = 30L
    const val PING_INTERVAL_SEC = 30L
    const val MAX_QUEUE_SIZE = 16 * 1024 * 1024  // 16MB
    
    // 重连配置
    const val MAX_RECONNECT_ATTEMPTS = 5
    const val RECONNECT_DELAY_MS = 2000L
    
    // Hello消息设备信息
    const val DEVICE_NAME = "小智Android客户端"
    const val CLIENT_TYPE = "android"
    
    /**
     * 获取音频参数JSON对象
     */
    fun getAudioParamsJson() = mapOf(
        "format" to AUDIO_FORMAT,
        "sample_rate" to SAMPLE_RATE,
        "channels" to CHANNELS,
        "frame_duration" to FRAME_DURATION_MS,
        "bitrate" to BITRATE
    )
    
    /**
     * 获取Hello消息的完整参数
     */
    fun getHelloParams(deviceInfo: info.dourok.voicebot.data.model.DeviceInfo) = mapOf(
        "type" to "hello",
        "version" to PROTOCOL_VERSION,
        "transport" to TRANSPORT_TYPE,
        "device_id" to deviceInfo.mac_address,
        "device_name" to DEVICE_NAME,
        "device_mac" to deviceInfo.mac_address,
        "client_type" to CLIENT_TYPE,
        "audio_params" to getAudioParamsJson()
    )
} 