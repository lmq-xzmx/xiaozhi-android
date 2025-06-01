package info.dourok.voicebot.ui

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import info.dourok.voicebot.AudioRecorder
import info.dourok.voicebot.NavigationEvents
import info.dourok.voicebot.OpusDecoder
import info.dourok.voicebot.OpusEncoder
import info.dourok.voicebot.OpusStreamPlayer
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.data.AudioConfig
import info.dourok.voicebot.protocol.AbortReason
import info.dourok.voicebot.protocol.AudioState
import info.dourok.voicebot.protocol.ListeningMode
import info.dourok.voicebot.protocol.MqttProtocol
import info.dourok.voicebot.protocol.Protocol
import info.dourok.voicebot.protocol.WebsocketProtocol
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    @NavigationEvents private val navigationEvents: MutableSharedFlow<String>,
    private val deviceInfo: DeviceInfo,
    private val settings: SettingsRepository
) : ViewModel() {

    companion object {
        private const val TAG = "ChatViewModel"
    }

    // 安全初始化标志
    private var isInitialized = false
    private var initializationError: String? = null

    // 延迟初始化protocol
    private var protocol: Protocol? = null

    val display = Display()
    var encoder: OpusEncoder? = null
    var decoder: OpusDecoder? = null
    var recorder: AudioRecorder? = null
    var player: OpusStreamPlayer? = null
    var aborted: Boolean = false
    var keepListening: Boolean = true
    val deviceStateFlow = MutableStateFlow(DeviceState.IDLE)
    
    // 初始化阶段状态
    private val _initializationStage = MutableStateFlow(InitializationStage.CHECKING_PREREQUISITES)
    val initializationStage: StateFlow<InitializationStage> = _initializationStage
    
    var deviceState: DeviceState
        get() = deviceStateFlow.value
        set(value) {
            deviceStateFlow.value = value
        }

    init {
        Log.i(TAG, "🚀 ChatViewModel开始初始化")
        try {
            // 延迟初始化，避免在构造函数中执行复杂操作
            viewModelScope.launch {
                delay(100) // 给UI时间完成渲染
                performSafeInitialization()
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ ChatViewModel构造函数异常: ${e.message}", e)
            initializationError = e.message
            deviceState = DeviceState.FATAL_ERROR
        }
    }

    /**
     * 安全的分阶段初始化流程
     * 按照理想工作流程逐步初始化，每个阶段都有完整的错误处理
     */
    private suspend fun performSafeInitialization() {
        try {
            deviceState = DeviceState.STARTING
            
            // 阶段1：检查前置条件
            _initializationStage.value = InitializationStage.CHECKING_PREREQUISITES
            if (!checkPrerequisites()) {
                Log.e(TAG, "前置条件检查失败")
                deviceState = DeviceState.FATAL_ERROR
                return
            }
            
            // 阶段2：初始化协议
            _initializationStage.value = InitializationStage.INITIALIZING_PROTOCOL
            if (!initializeProtocolSafely()) {
                Log.e(TAG, "协议初始化失败")
                deviceState = DeviceState.FATAL_ERROR
                return
            }
            
            // ⭐ 关键修复：立即启动消息处理流程
            Log.i(TAG, "🔥 立即启动消息处理流程...")
            if (!startMessageProcessingSafely()) {
                Log.e(TAG, "消息处理启动失败")
                deviceState = DeviceState.FATAL_ERROR
                return
            }
            
            // 阶段3：建立网络连接
            _initializationStage.value = InitializationStage.CONNECTING_NETWORK
            if (!connectNetworkSafely()) {
                Log.e(TAG, "网络连接失败")
                deviceState = DeviceState.FATAL_ERROR
                return
            }
            
            // 阶段4：设置音频系统
            _initializationStage.value = InitializationStage.SETTING_UP_AUDIO
            if (!setupAudioSafely()) {
                Log.e(TAG, "音频系统设置失败")
                deviceState = DeviceState.FATAL_ERROR
                return
            }
            
            // 阶段5：完成初始化（消息处理已在阶段2后启动）
            _initializationStage.value = InitializationStage.READY
            deviceState = DeviceState.IDLE
            isInitialized = true
            Log.i(TAG, "✅ ChatViewModel初始化完成")
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ 安全初始化过程异常: ${e.message}", e)
            initializationError = e.message
            deviceState = DeviceState.FATAL_ERROR
        }
    }
    
    /**
     * 检查前置条件
     */
    private fun checkPrerequisites(): Boolean {
        return try {
            Log.d(TAG, "检查前置条件...")
            
            // 检查音频权限
            if (!checkAudioPermissions()) {
                Log.e(TAG, "音频权限检查失败")
                return false
            }
            
            // 检查Native库
            if (!checkNativeLibraries()) {
                Log.e(TAG, "Native库检查失败")
                return false
            }
            
            // 检查网络权限
            if (!checkNetworkPermissions()) {
                Log.e(TAG, "网络权限检查失败")
                return false
            }
            
            // 检查配置完整性
            if (!checkConfiguration()) {
                Log.e(TAG, "配置完整性检查失败")
                return false
            }
            
            true
        } catch (e: Exception) {
            Log.e(TAG, "前置条件检查异常: ${e.message}", e)
            false
        }
    }
    
    private fun checkAudioPermissions(): Boolean {
        return try {
            val permission = context.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)
            val hasPermission = permission == android.content.pm.PackageManager.PERMISSION_GRANTED
            Log.d(TAG, "音频权限检查结果: $hasPermission")
            hasPermission
        } catch (e: Exception) {
            Log.e(TAG, "音频权限检查异常: ${e.message}", e)
            false
        }
    }
    
    private fun checkNetworkPermissions(): Boolean {
        return try {
            val internetPermission = context.checkSelfPermission(android.Manifest.permission.INTERNET)
            val networkStatePermission = context.checkSelfPermission(android.Manifest.permission.ACCESS_NETWORK_STATE)
            
            val hasPermissions = internetPermission == android.content.pm.PackageManager.PERMISSION_GRANTED &&
                    networkStatePermission == android.content.pm.PackageManager.PERMISSION_GRANTED
            
            Log.d(TAG, "网络权限检查结果: $hasPermissions")
            hasPermissions
        } catch (e: Exception) {
            Log.e(TAG, "网络权限检查异常: ${e.message}", e)
            false
        }
    }
    
    private fun checkNativeLibraries(): Boolean {
        return try {
            // 尝试加载Native库
            System.loadLibrary("app")
            Log.d(TAG, "✅ Native库加载成功")
            
            // 验证关键功能可用性（通过调用一个简单的JNI函数）
            try {
                // 测试Opus编码器初始化
                val testResult = testOpusEncoder()
                if (testResult) {
                    Log.d(TAG, "✅ Opus编码器功能验证成功")
                    true
                } else {
                    Log.e(TAG, "❌ Opus编码器功能验证失败")
                    false
                }
            } catch (e: UnsatisfiedLinkError) {
                Log.e(TAG, "❌ Native函数调用失败: ${e.message}", e)
                false
            }
            
        } catch (e: UnsatisfiedLinkError) {
            Log.e(TAG, "❌ Native库加载失败: ${e.message}", e)
            false
        } catch (e: Exception) {
            Log.e(TAG, "❌ Native库检查异常: ${e.message}", e)
            false
        }
    }
    
    /**
     * 测试Opus编码器是否正常工作
     */
    private external fun testOpusEncoder(): Boolean
    
    private fun checkConfiguration(): Boolean {
        return try {
            // 检查设备信息
            if (deviceInfo.mac_address.isBlank()) {
                Log.e(TAG, "设备MAC地址为空")
                return false
            }
            
            // 检查传输类型配置
            when (settings.transportType) {
                TransportType.MQTT -> {
                    // MQTT模式下检查配置
                    Log.d(TAG, "检查MQTT配置...")
                }
                TransportType.WebSockets -> {
                    // WebSocket模式下检查配置
                    Log.d(TAG, "检查WebSocket配置...")
                }
                null -> {
                    Log.e(TAG, "传输类型未配置")
                    return false
                }
            }
            
            Log.d(TAG, "配置检查通过")
            true
        } catch (e: Exception) {
            Log.e(TAG, "配置检查异常: ${e.message}", e)
            false
        }
    }
    
    /**
     * 安全的协议初始化
     */
    private suspend fun initializeProtocolSafely(): Boolean {
        return try {
            Log.i(TAG, "开始安全协议初始化，传输类型: ${settings.transportType}")
            
            protocol = when (settings.transportType) {
                TransportType.MQTT -> {
                    val mqttConfig = settings.mqttConfig
                    if (mqttConfig == null) {
                        Log.w(TAG, "MQTT配置未设置，回退到WebSocket模式")
                        createWebSocketProtocolSafely()
                    } else {
                        Log.i(TAG, "创建MQTT协议，endpoint: ${mqttConfig.endpoint}")
                        try {
                            MqttProtocol(context, mqttConfig)
                        } catch (e: Exception) {
                            Log.e(TAG, "MQTT协议创建失败，回退到WebSocket: ${e.message}", e)
                            createWebSocketProtocolSafely()
                        }
                    }
                }
                
                TransportType.WebSockets -> {
                    createWebSocketProtocolSafely()
                }
                
                null -> {
                    Log.e(TAG, "传输类型未配置")
                    null
                }
            }
            
            val success = protocol != null
            Log.i(TAG, "协议初始化结果: $success")
            success
            
        } catch (e: Exception) {
            Log.e(TAG, "协议初始化异常: ${e.message}", e)
            false
        }
    }
    
    private fun createWebSocketProtocolSafely(): Protocol? {
        return try {
            val webSocketUrl = settings.webSocketUrl
            val finalUrl = if (webSocketUrl.isNullOrEmpty()) {
                val defaultUrl = "ws://47.122.144.73:8000/xiaozhi/v1/"
                Log.i(TAG, "使用默认WebSocket URL: $defaultUrl")
                defaultUrl
            } else {
                Log.i(TAG, "使用配置的WebSocket URL: $webSocketUrl")
                webSocketUrl
            }
            
            WebsocketProtocol(deviceInfo, finalUrl, "test-token")
        } catch (e: Exception) {
            Log.e(TAG, "WebSocket协议创建失败: ${e.message}", e)
            null
        }
    }
    
    /**
     * 建立网络连接
     */
    private suspend fun connectNetworkSafely(): Boolean {
        return try {
            val proto = protocol
            if (proto == null) {
                Log.e(TAG, "协议未初始化，无法建立连接")
                return false
            }
            
            Log.i(TAG, "🌐 启动协议连接...")
            proto.start()
            deviceState = DeviceState.CONNECTING
            
            Log.i(TAG, "🔗 尝试打开音频通道...")
            if (proto.openAudioChannel()) {
                Log.i(TAG, "✅ 音频通道打开成功")
                true
            } else {
                Log.e(TAG, "❌ 音频通道打开失败")
                false
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ 网络连接建立异常: ${e.message}", e)
            false
        }
    }
    
    /**
     * 安全的音频处理设置
     */
    private suspend fun setupAudioSafely(): Boolean {
        return try {
            val proto = protocol
            if (proto == null) {
                Log.e(TAG, "协议未初始化，无法设置音频处理")
                return false
            }
            
            Log.i(TAG, "🎵 开始设置音频处理...")
            
            // 设置音频播放
            if (!setupAudioPlayback(proto)) {
                Log.e(TAG, "音频播放设置失败")
                return false
            }
            
            // 设置音频录制
            if (!setupAudioRecording(proto)) {
                Log.e(TAG, "音频录制设置失败")
                return false
            }
            
            Log.i(TAG, "✅ 音频处理设置完成")
            true
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ 音频处理设置异常: ${e.message}", e)
            false
        }
    }
    
    private suspend fun setupAudioPlayback(proto: Protocol): Boolean {
        return try {
            withContext(Dispatchers.IO) {
                launch {
                    val sampleRate = 24000
                    val channels = 1
                    val frameSizeMs = 60 // 匹配服务器配置
                    
                    player = OpusStreamPlayer(sampleRate, channels, frameSizeMs)
                    decoder = OpusDecoder(sampleRate, channels, frameSizeMs)
                    
                    player?.start(proto.incomingAudioFlow.map { audioData ->
                        try {
                            deviceState = DeviceState.SPEAKING
                            decoder?.decode(audioData) ?: byteArrayOf()
                        } catch (e: Exception) {
                            Log.e(TAG, "音频解码异常: ${e.message}")
                            byteArrayOf()
                        }
                    })
                    
                    Log.i(TAG, "🔊 音频播放设置成功")
                }
            }
            true
        } catch (e: Exception) {
            Log.e(TAG, "❌ 音频播放设置异常: ${e.message}", e)
            false
        }
    }
    
    private suspend fun setupAudioRecording(proto: Protocol): Boolean {
        return try {
            delay(1000) // 等待播放设置完成
            
            viewModelScope.launch {
                try {
                    Log.i(TAG, "🎤 开始设置音频录制和编码...")
                    Log.i(TAG, "使用统一音频配置 - 采样率: ${AudioConfig.SAMPLE_RATE}Hz, 通道: ${AudioConfig.CHANNELS}, 帧长: ${AudioConfig.FRAME_DURATION_MS}ms")
                    
                    // 使用统一的音频配置，解决硬编码问题
                    encoder = OpusEncoder(AudioConfig.SAMPLE_RATE, AudioConfig.CHANNELS, AudioConfig.FRAME_DURATION_MS)
                    recorder = AudioRecorder(AudioConfig.SAMPLE_RATE, AudioConfig.CHANNELS, AudioConfig.FRAME_DURATION_MS)
                    
                    val audioFlow = recorder?.startRecording()
                    if (audioFlow == null) {
                        Log.e(TAG, "❌ 音频录制启动失败")
                        showErrorMessage("音频录制启动失败，请检查麦克风权限")
                        return@launch
                    }
                    
                    Log.i(TAG, "✅ 音频录制器创建成功")
                    
                    val opusFlow = audioFlow.map { encoder?.encode(it) }
                    
                    // 自动开始STT监听
                    Log.i(TAG, "📢 设备进入LISTENING状态，开始STT监听")
                    deviceState = DeviceState.LISTENING
                    
                    // 发送开始监听指令到服务器
                    proto.sendStartListening(ListeningMode.AUTO_STOP)
                    
                    var audioFrameCount = 0
                    opusFlow.collect { encodedData ->
                        encodedData?.let { 
                            proto.sendAudio(it)
                            audioFrameCount++
                            
                            // 每100帧记录一次统计，减少日志噪音
                            if (audioFrameCount % 100 == 0) {
                                Log.d(TAG, "🎤 已发送音频帧: $audioFrameCount, 最新帧大小: ${it.size}字节")
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "❌ 音频录制设置失败: ${e.message}", e)
                    showErrorMessage("音频录制设置失败: ${e.message}")
                    deviceState = DeviceState.FATAL_ERROR
                }
            }
            true
        } catch (e: Exception) {
            Log.e(TAG, "❌ 音频录制设置异常: ${e.message}", e)
            false
        }
    }
    
    /**
     * 安全启动消息处理流程
     * 增强STT响应处理和错误诊断
     */
    private suspend fun startMessageProcessingSafely(): Boolean {
        return try {
            val proto = protocol
            if (proto == null) {
                Log.e(TAG, "协议未初始化，无法启动消息处理")
                return false
            }
            
            Log.i(TAG, "🚀 启动增强版消息处理流程...")
            
            // 启动网络错误监听
            viewModelScope.launch(Dispatchers.IO) {
                try {
                    proto.networkErrorFlow.collect { error ->
                        Log.e(TAG, "🚨 网络错误: $error")
                        schedule {
                            showErrorMessage(error)
                            if (deviceState != DeviceState.FATAL_ERROR) {
                                deviceState = DeviceState.IDLE
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "网络错误监听异常: ${e.message}", e)
                }
            }
            
            // 启动音频通道状态监听
            viewModelScope.launch(Dispatchers.IO) {
                try {
                    proto.audioChannelStateFlow.collect { state ->
                        Log.i(TAG, "🔊 音频通道状态变化: $state")
                        when (state) {
                            AudioState.OPENED -> {
                                Log.i(TAG, "✅ 音频通道已打开")
                            }
                            AudioState.CLOSED -> {
                                Log.w(TAG, "⚠️ 音频通道已关闭")
                                if (deviceState == DeviceState.LISTENING || deviceState == DeviceState.SPEAKING) {
                                    schedule {
                                        deviceState = DeviceState.IDLE
                                    }
                                }
                            }
                            AudioState.ERROR -> {
                                Log.e(TAG, "❌ 音频通道错误")
                                schedule {
                                    deviceState = DeviceState.FATAL_ERROR
                                    showErrorMessage("音频通道错误，请重新尝试")
                                }
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "音频状态监听异常: ${e.message}", e)
                }
            }
            
            // 启动消息处理协程 - 增强STT处理
            viewModelScope.launch(Dispatchers.IO) {
                try {
                    Log.i(TAG, "📡 开始监听服务器响应消息...")
                    
                    var messageCount = 0
                    var sttResponseCount = 0
                    var lastSttTime = 0L
                    
                    proto.incomingJsonFlow.collect { json ->
                        messageCount++
                        Log.i(TAG, "🎯 收到服务器JSON消息 #$messageCount: ${json.toString()}")
                        
                        val type = json.optString("type", "")
                        Log.i(TAG, "📋 消息类型: '$type'")
                        
                        when (type) {
                            "tts" -> {
                                val state = json.optString("state")
                                Log.i(TAG, "🔊 TTS消息，状态: $state")
                                when (state) {
                                    "start" -> {
                                        schedule {
                                            aborted = false
                                            if (deviceState == DeviceState.IDLE || deviceState == DeviceState.LISTENING) {
                                                deviceState = DeviceState.SPEAKING
                                                Log.i(TAG, "📢 开始TTS播放")
                                            }
                                        }
                                    }
                                    "end" -> {
                                        schedule {
                                            Log.i(TAG, "📢 TTS播放结束")
                                            if (keepListening && !aborted) {
                                                proto.sendStartListening(ListeningMode.AUTO_STOP)
                                                deviceState = DeviceState.LISTENING
                                                Log.i(TAG, "🎤 重新开始STT监听")
                                            } else {
                                                deviceState = DeviceState.IDLE
                                            }
                                        }
                                    }
                                }
                            }
                            
                            "stt" -> {
                                sttResponseCount++
                                val currentTime = System.currentTimeMillis()
                                val text = json.optString("text")
                                val isFinal = json.optBoolean("is_final", false)
                                
                                Log.i(TAG, "🎤 *** STT响应 #$sttResponseCount ***: text='$text', is_final=$isFinal")
                                Log.i(TAG, "   STT响应间隔: ${if (lastSttTime > 0) currentTime - lastSttTime else 0}ms")
                                lastSttTime = currentTime
                                
                                if (isFinal && text.isNotEmpty()) {
                                    schedule {
                                        Log.i(TAG, "📝 STT最终结果: $text")
                                        display.setChatMessage("user", text)
                                        deviceState = DeviceState.IDLE
                                    }
                                } else if (text.isNotEmpty()) {
                                    Log.i(TAG, "📝 STT中间结果: $text")
                                    // 可以选择显示中间结果
                                }
                            }
                            
                            "llm" -> {
                                val text = json.optString("text")
                                Log.i(TAG, "🤖 *** LLM响应 ***: $text")
                                if (text.isNotEmpty()) {
                                    schedule {
                                        display.setChatMessage("assistant", text)
                                    }
                                }
                            }
                            
                            "emotion" -> {
                                val emotion = json.optString("emotion")
                                Log.i(TAG, "😊 *** 情感响应 ***: $emotion")
                                if (emotion.isNotEmpty()) {
                                    schedule {
                                        display.setEmotion(emotion)
                                    }
                                }
                            }
                            
                            "hello" -> {
                                Log.i(TAG, "🤝 收到服务器Hello握手响应")
                                // 解析服务器Hello响应，验证协议兼容性
                                val serverVersion = json.optInt("version", -1)
                                val serverFrameDuration = json.optInt("frame_duration", -1)
                                Log.i(TAG, "   服务器版本: $serverVersion, 帧长度: ${serverFrameDuration}ms")
                                
                                if (serverVersion != AudioConfig.PROTOCOL_VERSION) {
                                    Log.w(TAG, "⚠️ 协议版本不匹配: 客户端=${AudioConfig.PROTOCOL_VERSION}, 服务器=$serverVersion")
                                }
                                if (serverFrameDuration != AudioConfig.FRAME_DURATION_MS) {
                                    Log.w(TAG, "⚠️ 帧长度不匹配: 客户端=${AudioConfig.FRAME_DURATION_MS}ms, 服务器=${serverFrameDuration}ms")
                                }
                            }
                            
                            "error" -> {
                                val errorMsg = json.optString("message", json.optString("error", "未知错误"))
                                Log.e(TAG, "❌ 服务器返回错误: $errorMsg")
                                schedule {
                                    showErrorMessage("服务器错误: $errorMsg")
                                }
                            }
                            
                            "stt_fallback" -> {
                                // 处理JSON解析失败但可能包含STT信息的回退消息
                                val rawText = json.optString("raw_text", "")
                                Log.w(TAG, "🎯 处理STT回退消息: $rawText")
                                // 这里可以添加更复杂的文本解析逻辑
                            }
                            
                            "" -> {
                                Log.w(TAG, "⚠️ 收到无类型消息: ${json.toString()}")
                                // 智能处理无类型消息，减少冗余
                                val possibleSTTContent = json.optString("text", 
                                                         json.optString("transcript", 
                                                         json.optString("recognition", "")))
                                if (possibleSTTContent.isNotEmpty()) {
                                    Log.i(TAG, "🎯 疑似STT无类型响应，文本: '$possibleSTTContent'")
                                        schedule {
                                        display.setChatMessage("user", possibleSTTContent)
                                        }
                                } else {
                                    Log.d(TAG, "   无类型消息无有效内容，跳过")
                                }
                            }
                            
                            else -> {
                                Log.d(TAG, "🔄 其他类型消息: $type，内容: ${json.toString()}")
                                // 检查是否包含文本内容
                                val textContent = json.optString("text", "")
                                if (textContent.isNotEmpty()) {
                                    Log.i(TAG, "   发现文本内容: '$textContent'")
                                }
                            }
                        }
                        
                        // 定期输出统计信息
                        if (messageCount % 50 == 0) {
                            Log.i(TAG, "📊 消息统计 - 总消息: $messageCount, STT响应: $sttResponseCount")
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "❌ 消息处理流程异常: ${e.message}", e)
                    schedule {
                        showErrorMessage("消息处理异常: ${e.message}")
                    deviceState = DeviceState.FATAL_ERROR
                    }
                }
            }
            
            Log.i(TAG, "✅ 增强版消息处理流程启动成功")
            true
        } catch (e: Exception) {
            Log.e(TAG, "❌ 消息处理启动异常: ${e.message}", e)
            false
        }
    }
    
    /**
     * 增强的错误消息显示
     */
    private fun showErrorMessage(message: String) {
        Log.e(TAG, "显示错误消息: $message")
        viewModelScope.launch {
            try {
                navigationEvents.emit("error:$message")
            } catch (e: Exception) {
                Log.e(TAG, "显示错误消息失败: ${e.message}", e)
            }
        }
    }

    fun toggleChatState() {
        viewModelScope.launch {
            when (deviceState) {
                DeviceState.ACTIVATING -> {
                    reboot()
                }

                DeviceState.IDLE -> {
                    if (protocol?.openAudioChannel() == true) {
                        keepListening = true
                        protocol?.sendStartListening(ListeningMode.AUTO_STOP)
                        deviceState = DeviceState.LISTENING
                    } else {
                        deviceState = DeviceState.IDLE
                    }
                }

                DeviceState.SPEAKING -> {
                    abortSpeaking(AbortReason.NONE)
                }

                DeviceState.LISTENING -> {
                    protocol?.closeAudioChannel()
                }

                else -> {
                    Log.e(TAG, "Protocol not initialized or invalid state")
                }
            }
        }
    }

    fun startListening() {
        viewModelScope.launch {
            if (deviceState == DeviceState.ACTIVATING) {
                reboot()
                return@launch
            }

            keepListening = false
            if (deviceState == DeviceState.IDLE) {
                val proto = protocol
                if (proto != null && !proto.isAudioChannelOpened()) {
                    deviceState = DeviceState.CONNECTING
                    if (!proto.openAudioChannel()) {
                        deviceState = DeviceState.IDLE
                        return@launch
                    }
                }
                proto?.sendStartListening(ListeningMode.MANUAL)
                deviceState = DeviceState.LISTENING
            } else if (deviceState == DeviceState.SPEAKING) {
                abortSpeaking(AbortReason.NONE)
                protocol?.sendStartListening(ListeningMode.MANUAL)
                delay(120) // Wait for the speaker to empty the buffer
                deviceState = DeviceState.LISTENING
            }
        }
    }

    private fun reboot() {
        // 实现重启逻辑
        Log.i(TAG, "Rebooting device...")
        viewModelScope.launch {
            try {
                // 关闭当前连接
                protocol?.closeAudioChannel()
                protocol?.dispose()
                
                // 重置设备状态
                deviceState = DeviceState.STARTING
                
                // 重新执行安全初始化
                performSafeInitialization()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to reboot", e)
                deviceState = DeviceState.FATAL_ERROR
                showErrorMessage("重启失败：${e.message}")
            }
        }
    }

    fun abortSpeaking(reason: AbortReason) {
        Log.i(TAG, "Abort speaking")
        aborted = true
        viewModelScope.launch {
            protocol?.sendAbortSpeaking(reason)
        }
    }
    
    private fun schedule(task: suspend () -> Unit) {
        viewModelScope.launch {
            task()
        }
    }

    fun stopListening() {
        viewModelScope.launch {
            if (deviceState == DeviceState.LISTENING) {
                protocol?.sendStopListening()
                deviceState = DeviceState.IDLE
            }
        }
    }

    override fun onCleared() {
        try {
            protocol?.dispose()
            encoder?.release()
            decoder?.release()
            player?.stop()
            recorder?.stopRecording()
        } catch (e: Exception) {
            Log.e(TAG, "清理资源时发生异常: ${e.message}", e)
        }
        super.onCleared()
    }
}

/**
 * 初始化阶段枚举
 */
enum class InitializationStage {
    CHECKING_PREREQUISITES,    // 检查前置条件
    INITIALIZING_PROTOCOL,     // 初始化协议
    CONNECTING_NETWORK,        // 连接网络
    SETTING_UP_AUDIO,         // 设置音频
    STARTING_MESSAGE_PROCESSING, // 启动消息处理
    READY                     // 准备就绪
}

enum class DeviceState {
    UNKNOWN,
    STARTING,
    WIFI_CONFIGURING,
    IDLE,
    CONNECTING,
    LISTENING,
    SPEAKING,
    UPGRADING,
    ACTIVATING,
    FATAL_ERROR
}

class Display {
    val chatFlow = MutableStateFlow<List<Message>>(listOf())
    val emotionFlow = MutableStateFlow<String>("neutral")
    fun setChatMessage(sender: String, message: String) {
        chatFlow.value = chatFlow.value + Message(sender, message)
    }

    fun setEmotion(emotion: String) {
        emotionFlow.value = emotion
    }
}

val df = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

data class Message(
    val sender: String = "",
    val message: String = "",
    val nowInString: String = df.format(System.currentTimeMillis())
)
