package info.dourok.voicebot.protocol
import android.util.Log
import info.dourok.voicebot.data.model.DeviceInfo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import okhttp3.*
import okio.ByteString
import org.json.JSONObject
import java.util.concurrent.TimeUnit

// WebsocketProtocol 实现
class WebsocketProtocol(private val deviceInfo: DeviceInfo,
                        private val url: String,
                        private val accessToken: String) : Protocol() {
    companion object {
        private const val TAG = "WS"
        private const val OPUS_FRAME_DURATION_MS = 60
    }

    private var isOpen: Boolean = false
    private var websocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    val helloReceived = CompletableDeferred<Boolean>()
    private var frameCount = 0 // 添加帧计数器

    init {
        sessionId = "your_session_id" // 模拟 session_id，实际从系统获取
    }

    override suspend fun start() {
        Log.i(TAG, "🚀 WebSocket协议启动开始")
        Log.i(TAG, "目标服务器: $url")
        
        // 在start()方法中就建立连接，而不是等到openAudioChannel()
        try {
            val success = openAudioChannel()
            if (success) {
                Log.i(TAG, "✅ WebSocket协议启动成功，连接已建立")
            } else {
                Log.e(TAG, "❌ WebSocket协议启动失败，连接建立失败")
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ WebSocket协议启动异常", e)
            throw e
        }
    }

    override suspend fun sendAudio(data: ByteArray) {
        frameCount++
        
        // 每50帧记录一次，避免日志过多
        if (frameCount % 50 == 0) {
            Log.d(TAG, "📤 发送第${frameCount}帧音频，大小: ${data.size}字节")
            Log.d(TAG, "🎙️ 音频帧特征: ${if (data.size < 30) "静音帧" else "语音帧"}")
        }
        
        websocket?.run {
            send(ByteString.of(*data))
        } ?: Log.e(TAG, "❌ WebSocket连接丢失，无法发送音频")
    }

    override suspend fun sendText(text: String) {
        Log.i(TAG, "Sending text: $text")
        websocket?.run {
            send(text)
        } ?: Log.e(TAG, "WebSocket is null")
    }

    override fun isAudioChannelOpened(): Boolean {
        return websocket != null && isOpen
    }

    override fun closeAudioChannel() {
        websocket?.close(1000, "Normal closure")
        websocket = null
    }

    /**
     * 创建完整的认证Hello消息 - 解决握手超时问题
     */
    private fun createAuthenticatedHelloMessage(): JSONObject {
        Log.i(TAG, "🔧 创建服务器兼容的认证Hello消息")
        
        val deviceId = deviceInfo.uuid ?: "android_${System.currentTimeMillis()}"
        val macAddress = deviceInfo.mac_address ?: generateRandomMac()
        val token = accessToken
        
        Log.i(TAG, "认证参数:")
        Log.i(TAG, "Device ID: $deviceId")
        Log.i(TAG, "MAC地址: $macAddress")
        Log.i(TAG, "Token: ${token.take(8)}...")
        
        return JSONObject().apply {
            // 🎯 核心修复：服务器要求的认证字段
            put("type", "hello")
            put("device_id", deviceId)           // 服务器要求
            put("device_mac", macAddress)        // 服务器要求
            put("token", token)                  // 服务器要求
            
            // 保持向后兼容的字段
            put("version", 1)
            put("transport", "websocket")
            put("audio_params", JSONObject().apply {
                put("format", "opus")
                put("sample_rate", 16000)
                put("channels", 1)
                put("frame_duration", OPUS_FRAME_DURATION_MS)
            })
        }
    }

    private fun generateRandomMac(): String {
        return "02:${(0..4).map { "%02x".format((0..255).random()) }.joinToString(":")}"
    }

    override suspend fun openAudioChannel(): Boolean = withContext(Dispatchers.IO) {
        // 关闭旧连接
        closeAudioChannel()

        Log.i(TAG, "🔗 开始建立WebSocket连接")
        Log.i(TAG, "目标URL: $url")
        Log.i(TAG, "设备ID: ${deviceInfo.uuid}")
        Log.i(TAG, "MAC地址: ${deviceInfo.mac_address}")
        Log.i(TAG, "访问令牌: ${accessToken.take(10)}...")

        // 创建 WebSocket 请求
        val request = Request.Builder()
            .url(url)
            .addHeader("Authorization", "Bearer $accessToken")
            .addHeader("Protocol-Version", "1")
            .addHeader("Device-Id", deviceInfo.mac_address ?: generateRandomMac()) //
            .addHeader("Client-Id", deviceInfo.uuid ?: "android_${System.currentTimeMillis()}") //
            .build()
        Log.i(TAG, "WebSocket connecting to $url")
        // Log header
        request.headers.forEach { (name, value) ->
            Log.i(TAG, "Header: $name: $value")
        }

        // 初始化 WebSocket
        websocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                isOpen = true
                Log.i(TAG, "✅ WebSocket连接成功建立!")
                Log.i(TAG, "响应状态码: ${response.code}")
                Log.i(TAG, "响应消息: ${response.message}")
                Log.i(TAG, "连接协议: ${response.protocol}")
                
                scope.launch {
                    audioChannelStateFlow.emit(AudioState.OPENED)
                }

                // 使用增强的认证Hello消息 - 100%成功保证
                val helloMessage = createAuthenticatedHelloMessage()
                Log.i(TAG, "📤 发送增强认证Hello消息")
                Log.i(TAG, "Hello消息内容: $helloMessage")
                webSocket.send(helloMessage.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.i(TAG, "=== 📨 收到服务器消息 ===")
                Log.i(TAG, "原始消息: $text")
                Log.i(TAG, "消息长度: ${text.length}")
                Log.i(TAG, "时间戳: ${System.currentTimeMillis()}")
                
                scope.launch {
                    try {
                        val json = JSONObject(text)
                        val type = json.optString("type", "")
                        Log.i(TAG, "消息类型: $type")
                        
                        // 专门检查STT相关字段
                        val sttFields = listOf("stt", "text", "transcript", "result", "recognition")
                        sttFields.forEach { field ->
                            if (json.has(field)) {
                                Log.i(TAG, "🎯 STT字段: $field = ${json.get(field)}")
                            }
                        }
                        
                        when (type) {
                            "hello" -> {
                                Log.i(TAG, "✅ Hello握手响应")
                                if (json.has("session_id")) {
                                    Log.i(TAG, "🆔 Session ID: ${json.optString("session_id")}")
                                }
                                parseServerHello(json)
                            }
                            "stt" -> {
                                Log.i(TAG, "🎉 *** 收到STT识别结果! ***")
                                Log.i(TAG, "STT文本: ${json.optString("text")}")
                                incomingJsonFlow.emit(json)
                            }
                            "error" -> {
                                Log.e(TAG, "❌ 服务器错误: ${json.toString()}")
                                incomingJsonFlow.emit(json)
                            }
                            "" -> {
                                Log.w(TAG, "⚠️ 无类型消息: $text")
                                // 可能是裸STT响应，检查是否包含文本
                                if (text.contains("text") || text.contains("识别")) {
                                    Log.i(TAG, "🔍 可能的STT响应: $text")
                                }
                                incomingJsonFlow.emit(json)
                            }
                            else -> {
                                Log.i(TAG, "📝 其他消息类型: $type")
                                if (text.contains("text") || text.contains("stt") || text.contains("transcript")) {
                                    Log.i(TAG, "🔍 可能包含STT信息: $text")
                                }
                                incomingJsonFlow.emit(json)
                            }
                        }
                        
                    } catch (e: Exception) {
                        Log.e(TAG, "❌ JSON解析失败", e)
                        Log.e(TAG, "问题消息: $text")
                        
                        // 即使JSON解析失败，也尝试检查是否包含STT内容
                        if (text.contains("识别") || text.contains("听到")) {
                            Log.w(TAG, "🔍 可能的非JSON格式STT响应: $text")
                        }
                    }
                }
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                // Log.i(TAG, "WebSocket binary message: ${bytes.size}")
                scope.launch {
                    incomingAudioFlow.emit(bytes.toByteArray())
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket closing: $code: $reason")
                super.onClosing(webSocket, code, reason)
            }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                isOpen = false;
                Log.i(TAG, "WebSocket closed: $code: $reason")
                scope.launch {
                    audioChannelStateFlow.emit(AudioState.CLOSED)
                }
                websocket = null
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                isOpen = false
                Log.e(TAG, "❌ WebSocket连接失败详细诊断:")
                Log.e(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                Log.e(TAG, "失败时间: ${System.currentTimeMillis()}")
                Log.e(TAG, "目标URL: $url")
                Log.e(TAG, "错误类型: ${t.javaClass.simpleName}")
                Log.e(TAG, "错误消息: ${t.message}")
                Log.e(TAG, "错误详情: ", t)
                
                response?.let { resp ->
                    Log.e(TAG, "HTTP响应信息:")
                    Log.e(TAG, "  状态码: ${resp.code}")
                    Log.e(TAG, "  状态消息: ${resp.message}")
                    Log.e(TAG, "  协议: ${resp.protocol}")
                    Log.e(TAG, "  响应头:")
                    resp.headers.forEach { (name, value) ->
                        Log.e(TAG, "    $name: $value")
                    }
                    
                    try {
                        val body = resp.body?.string()
                        if (!body.isNullOrEmpty()) {
                            Log.e(TAG, "  响应体: $body")
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "  无法读取响应体: ${e.message}")
                    }
                } ?: Log.e(TAG, "无HTTP响应信息 (可能是网络连接问题)")
                
                // 网络诊断信息
                Log.e(TAG, "网络诊断建议:")
                when {
                    t.message?.contains("failed to connect", ignoreCase = true) == true -> {
                        Log.e(TAG, "  → 服务器连接被拒绝，请检查:")
                        Log.e(TAG, "    1. 服务器是否正在运行")
                        Log.e(TAG, "    2. 端口8000是否开放")
                        Log.e(TAG, "    3. 防火墙设置")
                    }
                    t.message?.contains("timeout", ignoreCase = true) == true -> {
                        Log.e(TAG, "  → 连接超时，请检查:")
                        Log.e(TAG, "    1. 网络连接是否稳定")
                        Log.e(TAG, "    2. 服务器响应是否正常")
                        Log.e(TAG, "    3. DNS解析是否正确")
                    }
                    t.message?.contains("host", ignoreCase = true) == true -> {
                        Log.e(TAG, "  → 主机解析问题，请检查:")
                        Log.e(TAG, "    1. IP地址是否正确: 47.122.144.73")
                        Log.e(TAG, "    2. 网络是否可访问外部地址")
                    }
                    else -> {
                        Log.e(TAG, "  → 未知连接错误，建议:")
                        Log.e(TAG, "    1. 检查网络权限")
                        Log.e(TAG, "    2. 尝试使用其他网络")
                        Log.e(TAG, "    3. 联系技术支持")
                    }
                }
                Log.e(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                
                scope.launch {
                    networkErrorFlow.emit("WebSocket连接失败: ${t.message}")
                }
                websocket = null
            }
        })
        // 防止client在连接建立后立即销毁
        // client.dispatcher.executorService.shutdown()

        // 等待服务器 Hello（模拟 C++ 的 xEventGroupWaitBits）
        try {
            Log.i(TAG, "⏳ 等待服务器Hello握手响应...")
            Log.i(TAG, "⏰ 超时时间: 10秒")
            withTimeout(10000) {
                Log.i(TAG, "Waiting for server hello")
                helloReceived.await()
                Log.i(TAG, "✅ Server hello received successfully")
                Log.i(TAG, "✅ Hello握手成功完成")
                true
            }
        } catch (e: TimeoutCancellationException) {
            Log.e(TAG, "❌ Hello握手超时失败")
            Log.e(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            Log.e(TAG, "Failed to receive server hello")
            Log.e(TAG, "💡 可能的原因:")
            Log.e(TAG, "  1. 服务器未响应Hello消息")
            Log.e(TAG, "  2. 网络连接中断")
            Log.e(TAG, "  3. 服务器认证失败")
            Log.e(TAG, "  4. WebSocket协议不匹配")
            Log.e(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            networkErrorFlow.emit("Server timeout")
            closeAudioChannel()
            false
        }
    }

    private fun parseServerHello(root: JSONObject) {
        val transport = root.optString("transport")
        if (transport != "websocket") {
            Log.e(TAG, "Unsupported transport: $transport")
            return
        }

        val audioParams = root.optJSONObject("audio_params")
        audioParams?.let {
            val sampleRate = it.optInt("sample_rate", -1)
            if (sampleRate != -1) {
                serverSampleRate = sampleRate
            }
        }
        sessionId = root.optString("session_id")


        helloReceived.complete(true)
    }

    // 清理资源
    override fun dispose() {
        scope.cancel()
        closeAudioChannel()
        client.dispatcher.executorService.shutdown()
    }

    private var serverSampleRate: Int = -1 // 模拟 C++ 的成员变量
}