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
import info.dourok.voicebot.config.DeviceConfigManager
import info.dourok.voicebot.config.DeviceConfig
import info.dourok.voicebot.config.ActivationManager
import info.dourok.voicebot.config.ActivationResult
import info.dourok.voicebot.config.ActivationState
import info.dourok.voicebot.data.SettingsRepository
import info.dourok.voicebot.data.model.DeviceInfo
import info.dourok.voicebot.data.model.DeviceIdManager
import info.dourok.voicebot.data.model.DummyDataGenerator
import info.dourok.voicebot.data.model.TransportType
import info.dourok.voicebot.protocol.AbortReason
import info.dourok.voicebot.protocol.ListeningMode
import info.dourok.voicebot.protocol.MqttProtocol
import info.dourok.voicebot.protocol.Protocol
import info.dourok.voicebot.protocol.WebsocketProtocol
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Locale
import javax.inject.Inject
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.catch

@HiltViewModel
class ChatViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val settingsRepository: SettingsRepository,
    private val deviceConfigManager: DeviceConfigManager,
    private val deviceIdManager: DeviceIdManager,
    val activationManager: ActivationManager
) : ViewModel() {
    companion object {
        private const val TAG = "ChatViewModel"
        private const val INITIALIZATION_TIMEOUT_MS = 30000L // 30秒超时
    }

    private var deviceInfo: DeviceInfo? = null
    private var protocol: Protocol? = null
    private var encoder: OpusEncoder? = null
    private var decoder: OpusDecoder? = null
    private var player: OpusStreamPlayer? = null
    private var recorder: AudioRecorder? = null
    private var aborted = false
    private var keepListening = false
    
    // 状态防抖动机制，避免UI频繁闪烁
    private var lastStateChangeTime = 0L
    private var pendingStateChange: DeviceState? = null
    private var stateDebounceJob: Job? = null
    
    val deviceStateFlow = MutableStateFlow(DeviceState.UNKNOWN)
    var deviceState: DeviceState
        get() = deviceStateFlow.value
        set(value) {
            setDeviceStateWithDebounce(value)
        }

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    private val _isConnecting = MutableStateFlow(false)
    val isConnecting: StateFlow<Boolean> = _isConnecting.asStateFlow()

    private val _initializationStatus = MutableStateFlow<InitializationStatus>(InitializationStatus.NotStarted)
    val initializationStatus: StateFlow<InitializationStatus> = _initializationStatus.asStateFlow()

    // 激活状态
    val activationState: StateFlow<ActivationState> = activationManager.activationState

    val display = Display()

    // TTS音频数据缓冲区
    private val ttsAudioBuffer = MutableSharedFlow<ByteArray>()
    private var isTtsPlaying = false
    
    // 音频流程控制
    private var currentAudioJob: Job? = null
    private var isAudioFlowRunning = false

    init {
        Log.i(TAG, "ChatViewModel 构造函数完成，等待手动初始化")
        // 不在构造函数中进行任何复杂操作
    }

    /**
     * 手动启动初始化过程
     * 由UI层在适当时机调用
     */
    fun startInitialization() {
        if (_initializationStatus.value != InitializationStatus.NotStarted) {
            Log.w(TAG, "初始化已经开始或完成，当前状态: ${_initializationStatus.value}")
            return
        }
        
        Log.i(TAG, "开始手动初始化ChatViewModel")
        _initializationStatus.value = InitializationStatus.InProgress

        viewModelScope.launch {
            try {
                withTimeout(INITIALIZATION_TIMEOUT_MS) {
                    performInitialization()
                }
            } catch (e: TimeoutCancellationException) {
                Log.e(TAG, "初始化超时")
                _initializationStatus.value = InitializationStatus.Failed("初始化超时")
                deviceState = DeviceState.FATAL_ERROR
                _errorMessage.value = "初始化超时，请检查网络连接"
            } catch (e: Exception) {
                Log.e(TAG, "初始化失败", e)
                _initializationStatus.value = InitializationStatus.Failed(e.message ?: "未知错误")
                deviceState = DeviceState.FATAL_ERROR
                _errorMessage.value = "初始化失败: ${e.message}"
            }
        }
    }

    private suspend fun performInitialization() {
        Log.i(TAG, "执行初始化流程")
        
        try {
            _isConnecting.value = true
            _errorMessage.value = null
            deviceState = DeviceState.STARTING
            
            // 步骤1: 检查激活状态
            Log.i(TAG, "步骤1: 检查设备激活状态")
            val activationResult = activationManager.checkActivationStatus()
            
            when (activationResult) {
                is ActivationResult.NeedsActivation -> {
                    // 需要激活，等待用户操作
                    Log.i(TAG, "设备需要激活，激活码: ${activationResult.activationCode}")
                    _initializationStatus.value = InitializationStatus.NeedsActivation(
                        activationResult.activationCode,
                        activationResult.frontendUrl
                    )
                    deviceState = DeviceState.ACTIVATING
                    return
                }
                
                is ActivationResult.Activated -> {
                    // 已激活，继续初始化
                    Log.i(TAG, "设备已激活，WebSocket URL: ${activationResult.websocketUrl}")
                    proceedWithActivatedDevice(activationResult.websocketUrl)
                }
                
                is ActivationResult.NetworkError -> {
                    throw Exception("网络连接失败: ${activationResult.message}")
                }
                
                is ActivationResult.InvalidResponse -> {
                    throw Exception("服务器响应异常: ${activationResult.message}")
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "初始化过程中发生错误", e)
            throw e
        } finally {
            _isConnecting.value = false
        }
    }
    
    /**
     * 处理已激活设备的初始化
     */
    private suspend fun proceedWithActivatedDevice(websocketUrl: String) {
        Log.i(TAG, "继续已激活设备的初始化流程")
        
        // 🔧 修复：确保配置同步，防止SettingsRepository配置丢失
        if (settingsRepository.webSocketUrl.isNullOrEmpty()) {
            Log.w(TAG, "SettingsRepository中WebSocket URL为空，从DeviceConfigManager恢复")
            val savedUrl = deviceConfigManager.getWebsocketUrl()
            if (!savedUrl.isNullOrEmpty()) {
                settingsRepository.webSocketUrl = savedUrl
                settingsRepository.transportType = TransportType.WebSockets
                Log.i(TAG, "✅ 配置已从DeviceConfigManager恢复: $savedUrl")
            }
        } else {
            Log.i(TAG, "✅ SettingsRepository配置正常: ${settingsRepository.webSocketUrl}")
        }
        
        // 步骤2: 初始化设备信息
        Log.i(TAG, "步骤2: 初始化设备信息")
        val actualDeviceId = deviceConfigManager.getDeviceId()
        deviceInfo = DummyDataGenerator.generate(deviceIdManager).copy(
            uuid = "android-app-${System.currentTimeMillis()}"
        )
        
        // 步骤3: 初始化音频组件
        Log.i(TAG, "步骤3: 初始化音频组件")
        initializeAudioComponents()
        
        // 步骤4: 初始化协议
        Log.i(TAG, "步骤4: 初始化WebSocket协议")
        val accessToken = getAccessToken() ?: "default-token"
        protocol = WebsocketProtocol(deviceInfo!!, websocketUrl, accessToken)
        
        // 步骤5: 启动协议
        Log.i(TAG, "步骤5: 启动协议")
        protocol?.start()
        
        // 步骤6: 设置消息监听
        Log.i(TAG, "步骤6: 设置消息监听")
        observeProtocolMessages()
        
        // 步骤7: ESP32兼容模式 - 初始化完成后自动启动语音交互
        Log.i(TAG, "步骤7: 自动启动ESP32兼容的语音交互模式")
        
        // 初始化完成
        deviceState = DeviceState.IDLE
        _initializationStatus.value = InitializationStatus.Completed
        Log.i(TAG, "ChatViewModel 初始化完成")
        
        // ESP32兼容：自动启动持续监听模式
        Log.i(TAG, "🚀 ESP32兼容模式：自动启动语音交互，无需手动按钮")
        startEsp32CompatibleMode()
    }
    
    /**
     * 激活完成后的处理
     */
    fun onActivationComplete(websocketUrl: String) {
        Log.i(TAG, "激活完成，WebSocket URL: $websocketUrl")
        
        viewModelScope.launch {
            try {
                _initializationStatus.value = InitializationStatus.InProgress
                proceedWithActivatedDevice(websocketUrl)
            } catch (e: Exception) {
                Log.e(TAG, "激活后初始化失败", e)
                _initializationStatus.value = InitializationStatus.Failed("激活后初始化失败: ${e.message}")
                deviceState = DeviceState.FATAL_ERROR
                _errorMessage.value = "激活后初始化失败: ${e.message}"
            }
        }
    }

    private suspend fun getAccessToken(): String? {
        // 从设备配置或绑定信息中获取访问令牌
        // 这里需要根据实际的令牌存储方式来实现
        // 暂时返回一个默认值，实际应该从绑定响应中保存的令牌获取
        return "default-access-token"
    }
    
    private fun initializeAudioComponents() {
        try {
            val sampleRate = 16000
            val channels = 1
            val frameSizeMs = 60
            
            encoder = OpusEncoder(sampleRate, channels, frameSizeMs)
            decoder = OpusDecoder(sampleRate, channels, frameSizeMs)
            player = OpusStreamPlayer(sampleRate, channels, frameSizeMs)
            recorder = AudioRecorder(sampleRate, channels, frameSizeMs)
            Log.i(TAG, "Audio components initialized successfully")
                } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize audio components", e)
            throw e
                }
            }

    private fun observeProtocolMessages() {
        viewModelScope.launch {
            protocol?.incomingJsonFlow?.collect { json ->
                    val type = json.optString("type")
                    when (type) {
                        "tts" -> {
                            val state = json.optString("state")
                            when (state) {
                                "start" -> {
                                    schedule {
                                        aborted = false
                                        if (deviceState == DeviceState.IDLE || deviceState == DeviceState.LISTENING) {
                                            deviceState = DeviceState.SPEAKING
                                        Log.i(TAG, "🔊 TTS开始播放，设备状态 -> SPEAKING")
                                        
                                        // ESP32兼容：启动TTS音频播放流程
                                        startTtsAudioPlayback()
                                        
                                        // ESP32兼容：TTS播放时继续音频发送以支持语音打断
                                        if (keepListening) {
                                            Log.i(TAG, "🎤 TTS播放中继续音频监测，支持语音打断")
                                            // 不改变isAudioFlowRunning状态，让音频流程继续运行
                                            // 这样服务器端VAD能检测到用户说话并自动打断TTS
                                        }
                                        }
                                    }
                                }

                                "stop" -> {
                                    schedule {
                                        if (deviceState == DeviceState.SPEAKING) {
                                        Log.i(TAG, "⏹️ TTS播放结束，等待播放完成...")
                                        
                                        // ESP32兼容：停止TTS音频播放
                                        stopTtsAudioPlayback()
                                        
                                            player?.waitForPlaybackCompletion()
                                        Log.i(TAG, "✅ TTS播放完成")
                                        
                                        // ESP32兼容：TTS结束后自动恢复监听
                                            if (keepListening) {
                                            Log.i(TAG, "🔄 ESP32兼容模式：自动恢复监听状态")
                                            
                                            // 安全地恢复监听状态
                                            restoreListeningStateSafely()
                                            } else {
                                                deviceState = DeviceState.IDLE
                                            Log.i(TAG, "💤 进入IDLE状态（非持续监听模式）")
                                            }
                                        }
                                    }
                                }

                                "sentence_start" -> {
                                    val text = json.optString("text")
                                    if (text.isNotEmpty()) {
                                    Log.i(TAG, "💬 TTS文本: $text")
                                        schedule {
                                            display.setChatMessage("assistant", text)
                                        }
                                    }
                                }
                            }
                        }

                        "stt" -> {
                            val text = json.optString("text")
                            if (text.isNotEmpty()) {
                            Log.i(TAG, "🎯 STT识别结果: '$text'")
                                schedule {
                                    display.setChatMessage("user", text)
                                }
                            
                            // ESP32兼容：STT识别后，在AUTO_STOP模式下等待服务器响应
                            if (keepListening && deviceState == DeviceState.LISTENING) {
                                Log.i(TAG, "📝 ESP32兼容模式：STT识别完成，等待服务器TTS响应...")
                                // 注意：不立即切换状态，等待TTS开始信号
                            }
                        }
                    }
                    
                    "listen" -> {
                        // 处理服务器端的监听状态变化（ESP32兼容）
                        val state = json.optString("state")
                        when (state) {
                            "stop" -> {
                                Log.i(TAG, "🛑 服务器指示停止监听")
                                if (deviceState == DeviceState.LISTENING) {
                                    // 暂时停止音频发送，等待STT结果
                                    Log.i(TAG, "⏸️ 暂停音频发送，等待STT处理...")
                                }
                            }
                            "start" -> {
                                Log.i(TAG, "▶️ 服务器指示开始监听")
                                if (keepListening && deviceState != DeviceState.LISTENING) {
                                    deviceState = DeviceState.LISTENING
                                    protocol?.let { startContinuousAudioFlow(it) }
                                }
                                }
                            }
                        }

                        "llm" -> {
                            val emotion = json.optString("emotion")
                            if (emotion.isNotEmpty()) {
                                schedule {
                                    display.setEmotion(emotion)
                                }
                            }
                        }

                        "iot" -> {
                            val commands = json.optJSONArray("commands")
                        Log.i(TAG, "🏠 IOT commands: $commands")
//                            if (commands != null) {
//                                val thingManager = iot.ThingManager.getInstance()
//                                for (i in 0 until commands.length()) {
//                                    val command = commands.getJSONObject(i)
//                                    thingManager.invoke(command)
//                                }
//                            }
                        }
                    }
            } ?: Log.w(TAG, "Protocol or incomingJsonFlow is null, cannot observe messages")
        }
        
        // ESP32兼容：添加TTS音频数据接收处理
        observeTtsAudioData()
    }
    
    /**
     * ESP32兼容：监听TTS音频数据流
     * 处理服务器发送的TTS音频数据并播放
     */
    private fun observeTtsAudioData() {
        viewModelScope.launch(SupervisorJob()) {
            try {
                // 缓冲区管理变量
                var audioDataCount = 0
                var totalAudioBytes = 0
                var lastBufferCleanTime = System.currentTimeMillis()
                
                protocol?.incomingAudioFlow?.collect { audioData ->
                    if (deviceState == DeviceState.SPEAKING && audioData.isNotEmpty()) {
                        try {
                            audioDataCount++
                            totalAudioBytes += audioData.size
                            val currentTime = System.currentTimeMillis()
                            
                            Log.d(TAG, "🎵 收到TTS音频数据: ${audioData.size} 字节 (总计: $audioDataCount 包)")
                            
                            // 解码Opus音频数据为PCM
                            val currentDecoder = decoder
                            if (currentDecoder != null) {
                                val pcmData = currentDecoder.decode(audioData)
                                if (pcmData != null && pcmData.isNotEmpty()) {
                                    // 检查缓冲区大小，防止积累过多
                                    val bufferSize = totalAudioBytes / 1024  // KB
                                    if (bufferSize > 1024) {  // 超过1MB缓冲时警告
                                        Log.w(TAG, "⚠️ TTS音频缓冲区较大: ${bufferSize}KB，可能影响性能")
                                    }
                                    
                                    // 发送到TTS音频缓冲区
                                    ttsAudioBuffer.emit(pcmData)
                                    Log.d(TAG, "🎵 TTS音频数据已缓冲: ${pcmData.size} 字节PCM数据")
                                    
                                    // 定期清理统计信息，防止溢出
                                    if (currentTime - lastBufferCleanTime > 10000) {  // 每10秒重置统计
                                        Log.d(TAG, "🧹 重置TTS缓冲区统计: 处理了${audioDataCount}包，共${totalAudioBytes/1024}KB")
                                        audioDataCount = 0
                                        totalAudioBytes = 0
                                        lastBufferCleanTime = currentTime
                                        
                                        // 建议垃圾回收
                                        System.gc()
                                    }
                                    
                                } else {
                                    Log.w(TAG, "Opus解码失败，音频包#$audioDataCount")
                                }
                            } else {
                                Log.e(TAG, "解码器未初始化，无法处理TTS音频")
                                return@collect
                            }
                        } catch (e: CancellationException) {
                            Log.i(TAG, "TTS音频处理被取消")
                            throw e
                        } catch (e: Exception) {
                            Log.e(TAG, "TTS音频解码失败", e)
                            // 解码失败时，不中断整个流程，继续处理下一包
                        }
                    } else if (audioData.isNotEmpty()) {
                        Log.d(TAG, "收到${audioData.size}字节音频数据，但设备状态不是SPEAKING: $deviceState")
                    }
                }
            } catch (e: CancellationException) {
                Log.i(TAG, "TTS音频数据监听被取消")
            } catch (e: Exception) {
                Log.e(TAG, "TTS音频数据监听失败", e)
                _errorMessage.value = "TTS音频处理失败: ${e.message}"
            } finally {
                Log.i(TAG, "TTS音频数据监听结束")
            }
        } ?: Log.w(TAG, "Protocol or incomingAudioFlow is null, cannot observe TTS audio")
    }
    
    /**
     * ESP32兼容：启动TTS音频播放
     */
    private fun startTtsAudioPlayback() {
        Log.i(TAG, "🎵 启动TTS音频播放流程")
        
        val currentPlayer = player
        if (currentPlayer == null) {
            Log.e(TAG, "播放器未初始化，无法播放TTS音频")
            return
        }
        
        // 防止重复启动
        if (isTtsPlaying) {
            Log.w(TAG, "TTS播放已在进行中，跳过重复启动")
            return
        }
        
        try {
            isTtsPlaying = true
            
            // 确保播放器处于正确状态
            currentPlayer.stop()  // 先停止之前可能的播放
            
            // 启动流式播放
            currentPlayer.start(ttsAudioBuffer)
            Log.i(TAG, "🔊 TTS流式播放已启动")
            
        } catch (e: Exception) {
            Log.e(TAG, "启动TTS播放失败", e)
            isTtsPlaying = false
            _errorMessage.value = "TTS播放启动失败: ${e.message}"
        }
    }
    
    /**
     * ESP32兼容：停止TTS音频播放
     */
    private fun stopTtsAudioPlayback() {
        Log.i(TAG, "🛑 停止TTS音频播放流程")
        
        if (!isTtsPlaying) {
            Log.d(TAG, "TTS播放器未在运行，无需停止")
            return
        }
        
        try {
            isTtsPlaying = false
            
            val currentPlayer = player
            if (currentPlayer != null) {
                // 安全停止播放器
                currentPlayer.stop()
                Log.d(TAG, "TTS播放器已停止")
                
                // 短暂延迟确保播放器完全停止
                viewModelScope.launch {
                    delay(100)  // 等待100ms确保资源释放
                    Log.d(TAG, "TTS播放器资源清理完成")
                }
            } else {
                Log.w(TAG, "播放器实例为null，无法停止")
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "停止TTS播放时发生异常", e)
            // 即使出现异常，也要确保状态正确
            isTtsPlaying = false
        }
    }

    /**
     * 启动ESP32兼容的自动化语音交互
     * 使用AUTO_STOP模式，与ESP32端保持一致
     */
    fun startEsp32CompatibleMode() {
        viewModelScope.launch {
            val currentProtocol = protocol
            if (currentProtocol == null) {
                Log.e(TAG, "Protocol not initialized")
                _errorMessage.value = "协议未初始化，请等待连接建立"
                return@launch
            }
            
            Log.i(TAG, "🚀 启动ESP32兼容的自动化语音交互模式")
            
            if (deviceState == DeviceState.IDLE) {
                // 打开音频通道
                if (!currentProtocol.isAudioChannelOpened()) {
                    deviceState = DeviceState.CONNECTING
                    if (!currentProtocol.openAudioChannel()) {
                        deviceState = DeviceState.IDLE
                        Log.e(TAG, "音频通道打开失败")
                        return@launch
                    }
                }
                
                // 启动ESP32标准的AUTO_STOP模式
                keepListening = true
                currentProtocol.sendStartListening(ListeningMode.AUTO_STOP)
                deviceState = DeviceState.LISTENING
                
                Log.i(TAG, "✅ 已启动ESP32兼容模式 - AUTO_STOP监听")
                
                // 启动持续的音频录制流程
                startContinuousAudioFlow(currentProtocol)
            }
        }
    }
    
    /**
     * ESP32兼容的持续音频流程
     * 自动处理语音检测、STT、TTS循环
     */
    private fun startContinuousAudioFlow(protocol: Protocol) {
        // 防止重复启动
        if (isAudioFlowRunning) {
            Log.w(TAG, "音频流程已在运行，跳过重复启动")
            return
        }
        
        // 取消之前的音频任务
        currentAudioJob?.cancel()
        
        currentAudioJob = viewModelScope.launch(SupervisorJob()) {
            try {
                isAudioFlowRunning = true
                Log.i(TAG, "启动ESP32兼容的持续音频流程...")
                
                val currentRecorder = recorder
                val currentEncoder = encoder
                
                if (currentRecorder == null || currentEncoder == null) {
                    Log.e(TAG, "音频组件未初始化")
                    _errorMessage.value = "音频组件未初始化"
                    return@launch
                }
                
                // 确保录音已停止并等待释放完成
                try {
                    withContext(Dispatchers.IO) {
                        currentRecorder.stopRecording()
                        delay(200) // 等待200ms确保录音完全停止
                    }
                } catch (e: CancellationException) {
                    Log.w(TAG, "录音停止操作被取消")
                    throw e
                } catch (e: Exception) {
                    Log.e(TAG, "停止录音时发生异常", e)
                }
                
                // 启动持续录音（与ESP32端一致）
                Log.i(TAG, "开始ESP32模式的持续音频录制...")
                
                try {
                    withContext(Dispatchers.IO) {
                        val audioFlow = currentRecorder.startRecording()
                        
                        // 音频处理计数器，防止内存积累
                        var audioFrameCount = 0
                        var lastLogTime = System.currentTimeMillis()
                        
                        // 处理音频数据流
                        audioFlow.catch { exception ->
                            Log.e(TAG, "音频流异常", exception)
                            if (exception !is CancellationException) {
                                _errorMessage.value = "音频流异常: ${exception.message}"
                            }
                        }.collect { pcmData ->
                            // 检查协程是否已被取消
                            ensureActive()
                            
                            // 检查是否应该继续处理
                            if (!keepListening || !isAudioFlowRunning) {
                                Log.i(TAG, "音频流程停止标志检测到，退出音频处理")
                                return@collect
                            }
                            
                            audioFrameCount++
                            val currentTime = System.currentTimeMillis()
                            
                            // ESP32兼容：在LISTENING和SPEAKING状态下都发送音频数据
                            // SPEAKING状态下发送音频是为了让服务器VAD检测语音打断
                            if (deviceState == DeviceState.LISTENING || deviceState == DeviceState.SPEAKING) {
                                try {
                                    // 编码为Opus格式
                                    val opusData = currentEncoder.encode(pcmData)
                                    if (opusData != null && opusData.isNotEmpty()) {
                                        // 发送到服务器（与ESP32端相同）
                                        protocol.sendAudio(opusData)
                                        
                                        // 在SPEAKING状态下发送音频时的日志（降低频率）
                                        if (deviceState == DeviceState.SPEAKING) {
                                            if (currentTime - lastLogTime > 3000) {  // 每3秒记录一次
                                                Log.d(TAG, "🎤 SPEAKING状态下发送音频供VAD检测打断: ${opusData.size}字节 (帧#$audioFrameCount)")
                                                lastLogTime = currentTime
                                            }
                                        }
                                    } else {
                                        Log.w(TAG, "Opus编码失败，跳过此帧")
                                    }
                                } catch (e: CancellationException) {
                                    Log.w(TAG, "音频处理被取消")
                                    throw e
                                } catch (e: Exception) {
                                    Log.e(TAG, "音频处理失败", e)
                                    // 出现异常时，不立即退出，而是继续处理下一帧
                                }
                            }
                            
                            // 定期进行内存清理，防止积累
                            if (audioFrameCount % 1000 == 0) {
                                Log.d(TAG, "🧹 音频处理达到1000帧，建议进行内存清理")
                                // 触发垃圾回收建议
                                System.gc()
                            }
                        }
                    }
                } catch (e: CancellationException) {
                    Log.i(TAG, "音频流程被正常取消")
                    throw e
                } catch (e: Exception) {
                    Log.e(TAG, "音频流程发生异常", e)
                    _errorMessage.value = "音频流程异常: ${e.message}"
                }
                
            } catch (e: CancellationException) {
                Log.i(TAG, "ESP32兼容音频流程被取消")
                // 协程取消是正常的，不需要报告为错误
            } catch (e: Exception) {
                Log.e(TAG, "ESP32兼容音频流程失败", e)
                _errorMessage.value = "音频流程失败: ${e.message}"
                deviceState = DeviceState.IDLE
            } finally {
                isAudioFlowRunning = false
                Log.i(TAG, "音频流程已结束")
                
                // 安全清理资源
                try {
                    withContext(NonCancellable) {
                        recorder?.stopRecording()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "清理录音资源时发生异常", e)
                }
            }
        }
    }
    
    /**
     * 安全地恢复监听状态
     */
    private fun restoreListeningStateSafely() {
        viewModelScope.launch(SupervisorJob()) {
            try {
                Log.i(TAG, "开始安全恢复监听状态...")
                
                val currentProtocol = protocol
                if (currentProtocol == null) {
                    Log.e(TAG, "协议未初始化，无法恢复监听")
                    return@launch
                }
                
                // 短暂延迟，确保TTS完全结束
                try {
                    delay(200)
                } catch (e: CancellationException) {
                    Log.w(TAG, "恢复监听延迟被取消")
                    return@launch
                }
                
                // 检查状态是否仍然需要恢复监听
                if (!keepListening) {
                    Log.i(TAG, "监听标志已关闭，取消恢复")
                    return@launch
                }
                
                // 发送监听命令
                try {
                    currentProtocol.sendStartListening(ListeningMode.AUTO_STOP)
                    deviceState = DeviceState.LISTENING
                    
                    // 修复：移除音频流重启，避免第二轮对话断续问题
                    // 原代码：startContinuousAudioFlow(currentProtocol)
                    // ESP32兼容模式下音频流应持续运行，TTS结束后无需重启
                    
                    Log.i(TAG, "✅ 监听状态恢复成功（音频流保持连续运行）")
                } catch (e: Exception) {
                    Log.e(TAG, "发送监听命令失败", e)
                    _errorMessage.value = "发送监听命令失败: ${e.message}"
                    deviceState = DeviceState.IDLE
                    keepListening = false
                }
                
            } catch (e: CancellationException) {
                Log.i(TAG, "恢复监听状态被取消")
            } catch (e: Exception) {
                Log.e(TAG, "恢复监听状态失败", e)
                _errorMessage.value = "恢复监听失败: ${e.message}"
                deviceState = DeviceState.IDLE
                keepListening = false
            }
        }
    }

    fun toggleChatState() {
        viewModelScope.launch {
            val currentProtocol = protocol
            if (currentProtocol == null) {
                Log.e(TAG, "Protocol not initialized")
                _errorMessage.value = "协议未初始化，请等待连接建立"
                return@launch
            }
            
            when (deviceState) {
                DeviceState.ACTIVATING -> {
                    reboot()
                }

                DeviceState.UNKNOWN, DeviceState.IDLE -> {
                    // 使用ESP32兼容模式
                    startEsp32CompatibleMode()
                }

                DeviceState.SPEAKING -> {
                    abortSpeaking(AbortReason.NONE)
                }

                DeviceState.LISTENING -> {
                    // 停止ESP32兼容模式
                    stopEsp32CompatibleMode()
                }

                else -> {
                    Log.e(TAG, "Invalid state for toggle: $deviceState")
                }
            }
        }
    }
    
    /**
     * 停止ESP32兼容模式
     */
    fun stopEsp32CompatibleMode() {
        viewModelScope.launch {
            val currentProtocol = protocol
            if (currentProtocol == null) {
                Log.e(TAG, "Protocol not initialized")
                return@launch
            }
            
            Log.i(TAG, "🛑 停止ESP32兼容模式")
            
            // 停止持续监听
            keepListening = false
            isAudioFlowRunning = false
            
            // 取消当前音频任务
            currentAudioJob?.cancel()
            currentAudioJob = null
            
            // 停止录音
            recorder?.stopRecording()
            
            // 短暂延迟确保录音完全停止
            delay(100)
            
            // 发送停止监听命令
            currentProtocol.sendStopListening()
            
            // 关闭音频通道
            currentProtocol.closeAudioChannel()
            
            deviceState = DeviceState.IDLE
            
            Log.i(TAG, "✅ ESP32兼容模式已停止")
        }
    }

    fun startListening() {
        // 保留原有方法作为后备，但推荐使用ESP32兼容模式
        Log.i(TAG, "⚠️ 使用传统监听模式，推荐使用ESP32兼容模式")
        viewModelScope.launch {
            val currentProtocol = protocol
            if (currentProtocol == null) {
                Log.e(TAG, "Protocol not initialized")
                _errorMessage.value = "协议未初始化，请等待连接建立"
                return@launch
            }
            
            if (deviceState == DeviceState.ACTIVATING) {
                reboot()
                return@launch
            }

            keepListening = false
            if (deviceState == DeviceState.IDLE) {
                if (!currentProtocol.isAudioChannelOpened()) {
                    deviceState = DeviceState.CONNECTING
                    if (!currentProtocol.openAudioChannel()) {
                        deviceState = DeviceState.IDLE
                        return@launch
                    }
                }
                
                // 使用AUTO_STOP模式而不是MANUAL模式
                currentProtocol.sendStartListening(ListeningMode.AUTO_STOP)
                deviceState = DeviceState.LISTENING
                
                // 启动音频录制和传输流程
                startAudioRecordingFlow(currentProtocol)
                
            } else if (deviceState == DeviceState.SPEAKING) {
                abortSpeaking(AbortReason.NONE)
                currentProtocol.sendStartListening(ListeningMode.AUTO_STOP)
                delay(120) // Wait for the speaker to empty the buffer
                deviceState = DeviceState.LISTENING
                
                // 启动音频录制和传输流程
                startAudioRecordingFlow(currentProtocol)
            }
        }
    }
    
    /**
     * 启动音频录制和传输流程
     */
    private fun startAudioRecordingFlow(protocol: Protocol) {
        viewModelScope.launch {
            try {
                Log.i(TAG, "启动音频录制流程...")
                
                val currentRecorder = recorder
                val currentEncoder = encoder
                
                if (currentRecorder == null || currentEncoder == null) {
                    Log.e(TAG, "音频组件未初始化")
                    _errorMessage.value = "音频组件未初始化"
                    return@launch
                }
                
                // 启动录音
                Log.i(TAG, "开始音频录制...")
                val audioFlow = currentRecorder.startRecording()
                
                // 处理音频数据流
                audioFlow.collect { pcmData ->
                    try {
                        // 编码为Opus格式
                        val opusData = currentEncoder.encode(pcmData)
                        if (opusData != null && opusData.isNotEmpty()) {
                            // 发送到服务器
                            protocol.sendAudio(opusData)
                            
                            // 每100帧记录一次日志
                            if (System.currentTimeMillis() % 2000 < 100) {
                                Log.d(TAG, "音频数据发送: PCM=${pcmData.size}字节 -> Opus=${opusData.size}字节")
                            }
                        } else {
                            Log.w(TAG, "Opus编码失败，跳过此帧")
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "音频处理失败", e)
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "启动音频录制流程失败", e)
                _errorMessage.value = "音频录制启动失败: ${e.message}"
                deviceState = DeviceState.IDLE
            }
        }
    }

    private fun reboot() {
        // Implement the reboot logic here
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
            val currentProtocol = protocol
            if (currentProtocol == null) {
                Log.e(TAG, "Protocol not initialized")
                return@launch
            }
            
            if (deviceState == DeviceState.LISTENING) {
                // 停止录音
                Log.i(TAG, "停止音频录制...")
                recorder?.stopRecording()
                
                // 发送停止监听命令
                currentProtocol.sendStopListening()
                deviceState = DeviceState.IDLE
                
                Log.i(TAG, "语音监听已停止")
            }
        }
    }

    override fun onCleared() {
        Log.i(TAG, "ChatViewModel 正在清理资源...")
        
        // 立即停止所有音频流程
        keepListening = false
        isAudioFlowRunning = false
        isTtsPlaying = false
        
        // 取消所有协程任务
        try {
            currentAudioJob?.cancel()
            currentAudioJob = null
            Log.d(TAG, "音频协程任务已取消")
        } catch (e: Exception) {
            Log.e(TAG, "取消音频协程时出现异常", e)
        }
        
        // 释放音频组件（使用安全的方式）
        try {
            // 停止协议
            protocol?.let { p ->
                try {
                    // 使用协程调用suspend函数
                    viewModelScope.launch {
                        try {
                            p.sendStopListening()
                        } catch (e: Exception) {
                            Log.e(TAG, "发送停止监听指令时出现异常", e)
                        }
                    }
                    p.closeAudioChannel()
                    p.dispose()
                    Log.d(TAG, "协议已清理")
                } catch (e: Exception) {
                    Log.e(TAG, "清理协议时出现异常", e)
                }
            }
            protocol = null
            
            // 释放音频组件
            encoder?.let { e ->
                try {
                    e.release()
                    Log.d(TAG, "编码器已释放")
                } catch (ex: Exception) {
                    Log.e(TAG, "释放编码器时出现异常", ex)
                }
            }
            encoder = null
            
            decoder?.let { d ->
                try {
                    d.release()
                    Log.d(TAG, "解码器已释放")
                } catch (ex: Exception) {
                    Log.e(TAG, "释放解码器时出现异常", ex)
                }
            }
            decoder = null
            
            player?.let { p ->
                try {
                    p.stop()
                    Log.d(TAG, "播放器已停止")
                } catch (ex: Exception) {
                    Log.e(TAG, "停止播放器时出现异常", ex)
                }
            }
            player = null
            
            recorder?.let { r ->
                try {
                    r.stopRecording()
                    Log.d(TAG, "录音器已停止")
                } catch (ex: Exception) {
                    Log.e(TAG, "停止录音器时出现异常", ex)
                }
            }
            recorder = null
            
        } catch (e: Exception) {
            Log.e(TAG, "释放音频组件时出现异常", e)
        }
        
        // 清理设备信息
        deviceInfo = null
        
        // 清理状态
        deviceState = DeviceState.UNKNOWN
        _errorMessage.value = null
        
        // 触发垃圾回收，清理内存
        System.gc()
        
        Log.i(TAG, "ChatViewModel 资源清理完成")
        super.onCleared()
    }

    /**
     * 设备状态防抖动设置，减少UI频繁更新
     */
    private fun setDeviceStateWithDebounce(newState: DeviceState, minIntervalMs: Long = 300) {
        val currentTime = System.currentTimeMillis()
        
        // 对于重要状态变化（IDLE, FATAL_ERROR）立即更新
        if (newState == DeviceState.IDLE || newState == DeviceState.FATAL_ERROR || 
            newState == DeviceState.CONNECTING || deviceStateFlow.value == DeviceState.UNKNOWN) {
            updateDeviceStateImmediately(newState)
            return
        }
        
        // 如果距离上次状态变化时间很短，进行防抖处理
        if (currentTime - lastStateChangeTime < minIntervalMs) {
            pendingStateChange = newState
            
            // 取消之前的防抖任务
            stateDebounceJob?.cancel()
            
            // 启动新的防抖任务
            stateDebounceJob = viewModelScope.launch {
                delay(minIntervalMs)
                pendingStateChange?.let { pendingState ->
                    updateDeviceStateImmediately(pendingState)
                    pendingStateChange = null
                }
            }
            
            Log.d(TAG, "设备状态变化被防抖延迟: $newState")
        } else {
            updateDeviceStateImmediately(newState)
        }
    }
    
    /**
     * 立即更新设备状态
     */
    private fun updateDeviceStateImmediately(newState: DeviceState) {
        val oldState = deviceStateFlow.value
        if (oldState != newState) {
            Log.d(TAG, "设备状态变更: $oldState -> $newState")
            deviceStateFlow.value = newState
            lastStateChangeTime = System.currentTimeMillis()
            
            // 取消待处理的状态变化
            pendingStateChange = null
            stateDebounceJob?.cancel()
        }
    }
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

/**
 * 初始化状态
 */
sealed class InitializationStatus {
    object NotStarted : InitializationStatus()
    object InProgress : InitializationStatus()
    object Completed : InitializationStatus()
    data class Failed(val error: String) : InitializationStatus()
    data class NeedsActivation(val activationCode: String, val frontendUrl: String) : InitializationStatus()
}
