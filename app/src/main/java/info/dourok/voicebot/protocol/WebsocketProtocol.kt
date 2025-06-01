package info.dourok.voicebot.protocol
import android.util.Log
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.AudioConfig
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
    }

    private var isOpen: Boolean = false
    private var websocket: WebSocket? = null
    private var isReconnecting: Boolean = false
    private var reconnectAttempts: Int = 0
    private val client = OkHttpClient.Builder()
        .connectTimeout(AudioConfig.CONNECTION_TIMEOUT_SEC, TimeUnit.SECONDS)
        .readTimeout(AudioConfig.READ_TIMEOUT_SEC, TimeUnit.SECONDS)
        .writeTimeout(AudioConfig.WRITE_TIMEOUT_SEC, TimeUnit.SECONDS)
        .pingInterval(AudioConfig.PING_INTERVAL_SEC, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    val helloReceived = CompletableDeferred<Boolean>()

    init {
        sessionId = "android_client_${System.currentTimeMillis()}"
        
        // 启动连接状态监控
        scope.launch {
            monitorConnectionHealth()
        }
    }

    override suspend fun start() {
        Log.i(TAG, "🚀 WebSocket protocol start() - 开始初始化")
        
        try {
            // 重置连接状态
            isOpen = false
            isReconnecting = false
            reconnectAttempts = 0
            
            // 取消之前的WebSocket连接
            websocket?.let {
                Log.i(TAG, "清理旧的WebSocket连接")
                it.close(1000, "重新启动")
                websocket = null
            }
            
            Log.i(TAG, "✅ WebSocket协议初始化完成")
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ WebSocket协议启动异常: ${e.message}", e)
            throw e
        }
    }

    override suspend fun sendAudio(data: ByteArray) {
        try {
            val ws = websocket
            if (ws != null && isOpen && ws.queueSize() < AudioConfig.MAX_QUEUE_SIZE) {
                ws.send(ByteString.of(*data))
                Log.v(TAG, "音频数据发送成功: ${data.size} bytes")
            } else {
                val reason = when {
                    ws == null -> "WebSocket连接为空"
                    !isOpen -> "WebSocket连接已关闭"
                    else -> "WebSocket队列已满(${ws.queueSize()} bytes)"
                }
                Log.e(TAG, "无法发送音频数据: $reason")
                
                // 智能重连逻辑
                if (ws == null || !isOpen) {
                    attemptReconnection()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "发送音频数据失败: ${e.message}", e)
            scope.launch {
                networkErrorFlow.emit("音频发送失败: ${e.message}")
            }
        }
    }

    override suspend fun sendText(text: String) {
        try {
            Log.i(TAG, "发送文本消息: $text")
            websocket?.run {
                send(text)
                Log.d(TAG, "文本消息发送成功")
            } ?: run {
                Log.e(TAG, "WebSocket连接为空，无法发送文本")
                scope.launch {
                    networkErrorFlow.emit("WebSocket连接已断开")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "发送文本失败: ${e.message}", e)
            scope.launch {
                networkErrorFlow.emit("文本发送失败: ${e.message}")
            }
        }
    }

    override fun isAudioChannelOpened(): Boolean {
        val result = websocket != null && isOpen
        Log.v(TAG, "音频通道状态检查: $result")
        return result
    }

    override fun closeAudioChannel() {
        Log.i(TAG, "关闭音频通道")
        try {
            websocket?.close(1000, "正常关闭")
            websocket = null
            isOpen = false
            reconnectAttempts = 0  // 重置重连计数
            Log.i(TAG, "音频通道已关闭")
        } catch (e: Exception) {
            Log.e(TAG, "关闭音频通道时发生异常: ${e.message}", e)
        }
    }

    override suspend fun openAudioChannel(): Boolean = withContext(Dispatchers.IO) {
        Log.i(TAG, "开始打开音频通道到: $url")
        Log.i(TAG, "=== 🔍 详细连接诊断 START ===")
        Log.i(TAG, "目标URL: $url")
        Log.i(TAG, "访问令牌: $accessToken")
        Log.i(TAG, "设备MAC: ${deviceInfo.mac_address}")
        Log.i(TAG, "设备UUID: ${deviceInfo.uuid}")
        Log.i(TAG, "当前连接状态: isOpen=$isOpen, websocket=$websocket")
        Log.i(TAG, "=== 🔍 详细连接诊断 END ===")
        
        try {
            // 关闭旧连接
            closeAudioChannel()

            // 创建 WebSocket 请求 - 使用更完整的认证信息
            val request = Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer $accessToken")
                .addHeader("Protocol-Version", AudioConfig.PROTOCOL_VERSION.toString())
                .addHeader("Device-Id", deviceInfo.mac_address)
                .addHeader("Client-Id", deviceInfo.uuid)
                .addHeader("Client-Type", AudioConfig.CLIENT_TYPE)
                .addHeader("Frame-Duration", AudioConfig.FRAME_DURATION_MS.toString())
                .build()
            
            Log.d(TAG, "设备信息 - MAC: ${deviceInfo.mac_address}, UUID: ${deviceInfo.uuid}")
            Log.i(TAG, "正在连接WebSocket: $url")
            
            // 打印所有headers用于调试
            for (i in 0 until request.headers.size) {
                Log.d(TAG, "请求头: ${request.headers.name(i)}: ${request.headers.value(i)}")
            }

            // 初始化 WebSocket
            websocket = client.newWebSocket(request, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    isOpen = true
                    reconnectAttempts = 0  // 重置重连计数
                    Log.i(TAG, "🎉 WebSocket连接成功建立!")
                    Log.i(TAG, "响应码: ${response.code}")
                    Log.i(TAG, "响应头: ${response.headers}")
                    
                    scope.launch {
                        audioChannelStateFlow.emit(AudioState.OPENED)
                    }

                    // 发送 Hello 消息 - 使用完整的ESP32兼容格式
                    val helloParams = AudioConfig.getHelloParams(deviceInfo)
                    val helloMessage = JSONObject(helloParams)
                    Log.i(TAG, "发送完整Hello消息: $helloMessage")
                    webSocket.send(helloMessage.toString())
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    Log.i(TAG, "=== 🎯 服务器响应详细分析 START ===")
                    Log.i(TAG, "原始消息: $text")
                    Log.i(TAG, "消息长度: ${text.length}")
                    Log.i(TAG, "接收时间: ${System.currentTimeMillis()}")
                    
                    scope.launch {
                        try {
                            val json = JSONObject(text)
                            val type = json.optString("type", "")
                            Log.i(TAG, "消息类型: '$type'")
                            
                            // 详细分析消息内容 - 增强STT诊断
                            analyzeMessageContent(json, type)
                            
                            // ⚠️ 关键修复：确保所有消息都能到达ChatViewModel
                            Log.i(TAG, "💫 转发消息到ChatViewModel处理流程...")
                            incomingJsonFlow.emit(json)
                            
                            // 特殊处理逻辑
                            handleSpecificMessageType(json, type)
                            
                        } catch (e: Exception) {
                            Log.e(TAG, "❌ JSON解析异常: ${e.message}", e)
                            Log.e(TAG, "原始消息内容: $text")
                            
                            // 回退处理 - 尝试从纯文本中提取STT信息
                            handleParseFailedMessage(text)
                        }
                    }
                    Log.i(TAG, "=== 🎯 服务器响应详细分析 END ===")
                }

                override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                    Log.d(TAG, "收到二进制消息: ${bytes.size} bytes")
                    scope.launch {
                        incomingAudioFlow.emit(bytes.toByteArray())
                    }
                }

                override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                    Log.i(TAG, "WebSocket正在关闭: $code: $reason")
                    super.onClosing(webSocket, code, reason)
                }
                
                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    isOpen = false
                    Log.i(TAG, "WebSocket已关闭: $code: $reason")
                    scope.launch {
                        audioChannelStateFlow.emit(AudioState.CLOSED)
                    }
                    websocket = null
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    isOpen = false
                    Log.e(TAG, "❌ WebSocket连接失败")
                    Log.e(TAG, "错误详情: ${t.message}", t)
                    response?.let {
                        Log.e(TAG, "响应码: ${it.code}")
                        Log.e(TAG, "响应消息: ${it.message}")
                        try {
                            val body = it.body?.string()
                            if (!body.isNullOrEmpty()) {
                                Log.e(TAG, "响应体: $body")
                            }
                        } catch (e: Exception) {
                            Log.e(TAG, "读取响应体失败: ${e.message}")
                        }
                    }
                    
                    scope.launch {
                        audioChannelStateFlow.emit(AudioState.ERROR)
                        networkErrorFlow.emit("WebSocket连接失败: ${t.message}")
                    }
                    
                    // 自动重连
                    scope.launch {
                        attemptReconnection()
                    }
                }
            })

            // 等待连接建立或超时
            delay(5000)
            
            val success = isOpen && websocket != null
            Log.i(TAG, if (success) "✅ 音频通道打开成功" else "❌ 音频通道打开失败")
                return@withContext success
            
        } catch (e: Exception) {
            Log.e(TAG, "打开音频通道异常: ${e.message}", e)
            scope.launch {
                networkErrorFlow.emit("音频通道打开失败: ${e.message}")
            }
            return@withContext false
        }
    }

    /**
     * 增强的消息内容分析 - 专门用于STT诊断
     */
    private fun analyzeMessageContent(json: JSONObject, type: String) {
        Log.i(TAG, "📊 消息内容详细分析:")
        Log.i(TAG, "   类型: $type")
        
        // 检查所有可能的STT相关字段
        val sttFields = listOf("stt", "text", "transcript", "recognition", "speech", "result", "data")
        sttFields.forEach { field ->
            if (json.has(field)) {
                Log.i(TAG, "   🎯 STT相关字段发现: $field = ${json.get(field)}")
            }
        }
        
        // 检查消息中的所有字段
        val keys = json.keys().asSequence().toList()
        Log.d(TAG, "   所有字段: $keys")
        
        // 检查是否有错误信息
        if (json.has("error")) {
            Log.e(TAG, "   ❌ 发现错误字段: ${json.optString("error")}")
        }
        
        if (json.has("message")) {
            Log.i(TAG, "   💬 消息字段: ${json.optString("message")}")
        }
    }

    /**
     * 处理特定消息类型
     */
    private fun handleSpecificMessageType(json: JSONObject, type: String) {
        when (type) {
            "hello" -> {
                Log.i(TAG, "🤝 收到服务器Hello握手响应")
                parseServerHello(json)
            }
            
            "stt" -> {
                Log.i(TAG, "🎤 *** 收到STT响应! ***")
                val sttText = json.optString("text", "")
                val isFinal = json.optBoolean("is_final", false)
                Log.i(TAG, "   STT文本: '$sttText'")
                Log.i(TAG, "   是否最终: $isFinal")
                Log.i(TAG, "   完整STT内容: ${json.toString()}")
            }
            
            "llm" -> {
                Log.i(TAG, "🤖 收到LLM响应")
                val llmText = json.optString("text", "")
                Log.i(TAG, "   LLM文本: '$llmText'")
            }
            
            "tts" -> {
                Log.i(TAG, "🔊 收到TTS响应")
                val state = json.optString("state", "")
                Log.i(TAG, "   TTS状态: $state")
            }
            
            "error" -> {
                Log.e(TAG, "❌ 服务器返回错误")
                val errorMsg = json.optString("message", json.optString("error", "未知错误"))
                Log.e(TAG, "   错误详情: $errorMsg")
            }
            
            "" -> {
                // 处理无类型消息 - 可能是STT的特殊格式，减少冗余处理
                Log.w(TAG, "⚠️ 收到无类型消息，尝试智能解析")
                if (json.has("text") || json.has("transcript")) {
                    Log.i(TAG, "🎯 疑似STT无类型响应，转发处理")
                } else {
                    Log.d(TAG, "   跳过无关的无类型消息")
                }
            }
            
            else -> {
                Log.d(TAG, "🔄 其他类型消息: $type")
                // 检查是否包含有价值的信息
                if (json.has("text") && json.optString("text").isNotEmpty()) {
                    Log.i(TAG, "   包含文本内容，可能有价值")
                }
    }
        }
    }

    /**
     * 处理JSON解析失败的消息
     */
    private fun handleParseFailedMessage(text: String) {
        Log.w(TAG, "尝试从解析失败的消息中提取信息...")
        
        // 检查是否可能包含STT相关内容
        val sttKeywords = listOf("stt", "speech", "transcript", "recognition", "识别")
        val containsSTT = sttKeywords.any { text.contains(it, ignoreCase = true) }
        
        if (containsSTT) {
            Log.i(TAG, "🎯 疑似STT相关的非JSON响应: $text")
            // 创建一个包含原始文本的JSON对象
            try {
                val fallbackJson = JSONObject().apply {
                    put("type", "stt_fallback")
                    put("raw_text", text)
                    put("parsed", false)
                }
                scope.launch {
                    incomingJsonFlow.emit(fallbackJson)
                }
            } catch (e: Exception) {
                Log.e(TAG, "创建回退JSON失败: ${e.message}")
            }
        } else {
            Log.d(TAG, "非STT相关的解析失败消息，忽略")
        }
    }

    /**
     * 智能重连机制
     */
    private suspend fun attemptReconnection() {
        if (isReconnecting || reconnectAttempts >= AudioConfig.MAX_RECONNECT_ATTEMPTS) {
            Log.w(TAG, "重连已达最大次数或正在重连中，跳过")
            return
        }
        
        isReconnecting = true
        reconnectAttempts++
        
        Log.i(TAG, "🔄 开始第 $reconnectAttempts 次重连尝试...")
        
        try {
            delay(AudioConfig.RECONNECT_DELAY_MS)
            
            if (openAudioChannel()) {
                Log.i(TAG, "✅ 重连成功!")
                isReconnecting = false
            } else {
                Log.e(TAG, "❌ 第 $reconnectAttempts 次重连失败")
                isReconnecting = false
                
                if (reconnectAttempts >= AudioConfig.MAX_RECONNECT_ATTEMPTS) {
                    scope.launch {
                        networkErrorFlow.emit("连接已断开，重连失败，请检查网络")
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "重连过程异常: ${e.message}", e)
            isReconnecting = false
        }
    }

    /**
     * 连接健康监控
     */
    private suspend fun monitorConnectionHealth() {
        while (true) {
            delay(30000) // 每30秒检查一次
            
            if (isOpen && websocket != null) {
                try {
                    // 发送心跳ping
                    websocket?.send("ping")
                    Log.v(TAG, "发送心跳ping")
                } catch (e: Exception) {
                    Log.w(TAG, "心跳发送失败: ${e.message}")
                }
            }
        }
    }

    private fun parseServerHello(root: JSONObject) {
        Log.i(TAG, "解析服务器Hello: $root")
        
            val transport = root.optString("transport")
            Log.d(TAG, "服务器传输方式: $transport")
            
        if (transport != "websocket" && transport != "udp") {
            Log.e(TAG, "不支持的传输方式: $transport")
                helloReceived.complete(false)
                return
            }

            val audioParams = root.optJSONObject("audio_params")
            if (audioParams != null) {
                Log.d(TAG, "服务器音频参数: $audioParams")
                val sampleRate = audioParams.optInt("sample_rate", -1)
                if (sampleRate != -1) {
                    serverSampleRate = sampleRate
                    Log.d(TAG, "服务器采样率: $sampleRate")
                }
            } else {
            Log.w(TAG, "服务器Hello中无音频参数")
            }
            
        sessionId = root.optString("session_id", sessionId)
            Log.i(TAG, "从服务器获取会话ID: $sessionId")

        Log.i(TAG, "服务器Hello解析成功，完成握手")
            helloReceived.complete(true)
    }

    // 清理资源
    override fun dispose() {
        Log.i(TAG, "清理WebSocket协议资源")
        try {
            scope.cancel()
            closeAudioChannel()
            client.dispatcher.executorService.shutdown()
            Log.i(TAG, "WebSocket协议资源清理完成")
        } catch (e: Exception) {
            Log.e(TAG, "清理资源时发生异常: ${e.message}", e)
        }
    }

    private var serverSampleRate: Int = -1
}