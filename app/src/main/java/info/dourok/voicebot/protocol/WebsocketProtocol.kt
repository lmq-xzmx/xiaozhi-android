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

    init {
        sessionId = "your_session_id" // 模拟 session_id，实际从系统获取
    }

    override suspend fun start() {
        Log.i(TAG, "WebSocket protocol start() called")
        // 自动建立WebSocket连接
        Log.i(TAG, "正在建立WebSocket连接...")
        val success = openAudioChannel()
        if (success) {
            Log.i(TAG, "WebSocket连接建立成功")
        } else {
            Log.e(TAG, "WebSocket连接建立失败")
        }
    }

    override suspend fun sendAudio(data: ByteArray) {
        // Log.i(TAG, "Sending audio: ${data.size}")
        websocket?.run {
            send(ByteString.of(*data))
        } ?: Log.e(TAG, "WebSocket is null when trying to send audio")
    }

    override suspend fun sendText(text: String) {
        Log.i(TAG, "Sending text: $text")
        websocket?.run {
            send(text)
        } ?: Log.e(TAG, "WebSocket is null when trying to send text")
    }

    override fun isAudioChannelOpened(): Boolean {
        val result = websocket != null && isOpen
        Log.d(TAG, "isAudioChannelOpened: $result (websocket=$websocket, isOpen=$isOpen)")
        return result
    }

    override fun closeAudioChannel() {
        Log.i(TAG, "Closing audio channel")
        websocket?.close(1000, "Normal closure")
        websocket = null
        isOpen = false
    }

    override suspend fun openAudioChannel(): Boolean = withContext(Dispatchers.IO) {
        Log.i(TAG, "Opening audio channel to $url")
        
        // 关闭旧连接
        closeAudioChannel()

        // 重置CompletableDeferred
        if (helloReceived.isCompleted) {
            Log.w(TAG, "helloReceived was already completed, this might indicate a previous connection issue")
        }

        // 创建 WebSocket 请求
        val request = Request.Builder()
            .url(url)
            .addHeader("Authorization", "Bearer $accessToken")
            .addHeader("Protocol-Version", "1")
            .addHeader("Device-Id", deviceInfo.mac_address)
            .addHeader("Client-Id", deviceInfo.uuid)
            .build()
        
        Log.d("DeviceInfo", "Current Device-Id: ${deviceInfo.mac_address}")
        Log.i(TAG, "WebSocket connecting to $url")
        
        // 打印所有headers用于调试
        for (i in 0 until request.headers.size) {
            val name = request.headers.name(i)
            val value = request.headers.value(i)
            Log.d(TAG, "Header: $name: $value")
        }

        // 初始化 WebSocket
        websocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                isOpen = true
                Log.i(TAG, "WebSocket connected successfully")
                Log.i(TAG, "Response code: ${response.code}")
                Log.i(TAG, "Response headers: ${response.headers}")
                
                scope.launch {
                    audioChannelStateFlow.emit(AudioState.OPENED)
                }

                // 发送 Hello 消息
                val helloMessage = JSONObject().apply {
                    put("type", "hello")
                    put("version", 1)
                    put("transport", "websocket")
                    put("audio_params", JSONObject().apply {
                        put("format", "opus")
                        put("sample_rate", 16000)
                        put("channels", 1)
                        put("frame_duration", OPUS_FRAME_DURATION_MS)
                    })
                }
                Log.i(TAG, "Sending hello message: $helloMessage")
                webSocket.send(helloMessage.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.i(TAG, "=== 服务器完整响应 START ===")
                Log.i(TAG, "原始消息: $text")
                Log.i(TAG, "消息长度: ${text.length}")
                Log.i(TAG, "时间戳: ${System.currentTimeMillis()}")
                
                scope.launch {
                    try {
                        val json = JSONObject(text)
                        val type = json.optString("type", "未知")
                        Log.i(TAG, "JSON类型: $type")
                        Log.d(TAG, "JSON内容: ${json.toString(2)}")
                        
                        // 检查所有可能的STT相关字段
                        val possibleSTTFields = listOf("stt", "text", "transcript", "recognition", "speech", "result", "data")
                        possibleSTTFields.forEach { field ->
                            if (json.has(field)) {
                                Log.i(TAG, "🎯 发现可能的STT字段: $field = ${json.get(field)}")
                            }
                        }
                        
                        // 检查消息中的所有字段
                        val keys = json.keys()
                        Log.d(TAG, "消息包含字段: ${keys.asSequence().toList()}")
                        
                        when (type) {
                            "hello" -> {
                                Log.i(TAG, "收到服务器hello，解析中...")
                                parseServerHello(json)
                            }
                            "stt" -> {
                                Log.i(TAG, "🎉 *** 收到STT响应! ***")
                                Log.i(TAG, "STT内容: ${json.toString()}")
                                incomingJsonFlow.emit(json)
                            }
                            "error" -> {
                                Log.e(TAG, "❌ 服务器返回错误: ${json.toString()}")
                                incomingJsonFlow.emit(json)
                            }
                            "" -> {
                                Log.w(TAG, "⚠️ 空类型消息: $text")
                                // 尝试直接转发，可能是无类型的STT响应
                                incomingJsonFlow.emit(json)
                            }
                            else -> {
                                Log.d(TAG, "转发消息到处理流程: $type")
                                incomingJsonFlow.emit(json)
                            }
                        }
                        
                        Log.i(TAG, "=== 服务器完整响应 END ===")
                        
                    } catch (e: Exception) {
                        Log.e(TAG, "JSON解析失败: ${e.message}")
                        Log.w(TAG, "可能是纯文本响应或格式错误的JSON")
                        Log.w(TAG, "原始内容: $text")
                        // 尝试作为纯文本处理
                        if (text.contains("stt", ignoreCase = true) || 
                            text.contains("speech", ignoreCase = true) ||
                            text.contains("transcript", ignoreCase = true)) {
                            Log.i(TAG, "🎯 疑似STT纯文本响应: $text")
                        }
                    }
                }
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                Log.d(TAG, "Received binary message: ${bytes.size} bytes")
                scope.launch {
                    incomingAudioFlow.emit(bytes.toByteArray())
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket closing: $code: $reason")
                super.onClosing(webSocket, code, reason)
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                isOpen = false
                Log.i(TAG, "WebSocket closed: $code: $reason")
                scope.launch {
                    audioChannelStateFlow.emit(AudioState.CLOSED)
                }
                websocket = null
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                isOpen = false
                Log.e(TAG, "WebSocket connection failed")
                Log.e(TAG, "Error: ${t.message}", t)
                response?.let {
                    Log.e(TAG, "Response code: ${it.code}")
                    Log.e(TAG, "Response message: ${it.message}")
                    try {
                        Log.e(TAG, "Response body: ${it.body?.string()}")
                    } catch (e: Exception) {
                        Log.e(TAG, "Could not read response body: ${e.message}")
                    }
                }
                scope.launch {
                    networkErrorFlow.emit("Server connection failed: ${t.message}")
                }
                websocket = null
                
                // 确保helloReceived得到通知
                if (!helloReceived.isCompleted) {
                    helloReceived.complete(false)
                }
            }
        })

        // 等待服务器 Hello（模拟 C++ 的 xEventGroupWaitBits）
        try {
            Log.i(TAG, "Waiting for server hello (timeout: 10s)...")
            val success = withTimeout(10000) {
                helloReceived.await()
            }
            Log.i(TAG, "Server hello result: $success")
            return@withContext success
        } catch (e: TimeoutCancellationException) {
            Log.e(TAG, "Timeout waiting for server hello")
            scope.launch {
                networkErrorFlow.emit("Server hello timeout")
            }
            closeAudioChannel()
            return@withContext false
        } catch (e: Exception) {
            Log.e(TAG, "Error waiting for server hello: ${e.message}", e)
            closeAudioChannel()
            return@withContext false
        }
    }

    private fun parseServerHello(root: JSONObject) {
        Log.i(TAG, "Parsing server hello: $root")
        
        val transport = root.optString("transport")
        Log.d(TAG, "Server transport: $transport")
        
        if (transport != "websocket") {
            Log.e(TAG, "Unsupported transport: $transport (expected: websocket)")
            helloReceived.complete(false)
            return
        }

        val audioParams = root.optJSONObject("audio_params")
        if (audioParams != null) {
            Log.d(TAG, "Server audio params: $audioParams")
            val sampleRate = audioParams.optInt("sample_rate", -1)
            if (sampleRate != -1) {
                serverSampleRate = sampleRate
                Log.d(TAG, "Server sample rate: $sampleRate")
            }
        } else {
            Log.w(TAG, "No audio_params in server hello")
        }
        
        sessionId = root.optString("session_id")
        Log.i(TAG, "Session ID from server: $sessionId")

        Log.i(TAG, "Server hello parsed successfully, completing handshake")
        helloReceived.complete(true)
    }

    // 清理资源
    override fun dispose() {
        Log.i(TAG, "Disposing WebSocket protocol")
        scope.cancel()
        closeAudioChannel()
        client.dispatcher.executorService.shutdown()
    }

    private var serverSampleRate: Int = -1 // 模拟 C++ 的成员变量
}